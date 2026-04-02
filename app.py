from flask import Flask, render_template, Response, request, jsonify, send_from_directory, send_file
import cv2
import face_engine
import attendance_service
import config
import threading
import time
import os
from datetime import datetime

app = Flask(__name__)

# Global state for web streaming and registration
current_name = "Unknown"
latest_frame = None
registration_request = {"pending": False, "name": None, "result": None}
lock = threading.Lock()

def camera_thread():
    """Background thread for continuous camera capture and processing."""
    global current_name, latest_frame, registration_request
    
    # Try with AVFoundation for macOS stability
    cap = cv2.VideoCapture(config.CAMERA_INDEX, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        # Fallback to default
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # Face engine instance (shared)
    engine = face_engine.engine
    
    while True:
        success, frame = cap.read()
        if not success:
            time.sleep(0.1)
            continue
            
        # Handle Synchronized Registration Request
        with lock:
            if registration_request["pending"]:
                # The camera thread captures the frame directly
                name = registration_request["name"]
                success, msg = engine.register_face(frame.copy(), name)
                registration_request["result"] = {"success": success, "message": msg}
                registration_request["pending"] = False

        # Identify faces
        display_frame = frame.copy()
        identified_faces = engine.identify_faces(display_frame)
        
        with lock:
            if not identified_faces:
                current_name = "Unknown"
            else:
                name, (top, right, bottom, left) = identified_faces[0]
                current_name = name
                
                # Draw on display frame
                color = (229, 70, 79) if name == "Unknown" else (129, 185, 16) # BGR
                cv2.rectangle(display_frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(display_frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(display_frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

            # Update latest encoded frame for web streaming
            ret, buffer = cv2.imencode('.jpg', display_frame)
            latest_frame = buffer.tobytes()
        
        time.sleep(0.01)

@app.route('/')
def index():
    return render_template('index.html')

def gen_frames():
    """Video streaming generator function."""
    while True:
        with lock:
            if latest_frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_frame + b'\r\n')
        time.sleep(0.04) # ~25 FPS

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    with lock:
        return jsonify({"name": current_name})

@app.route('/get_students')
def get_students():
    names = face_engine.engine.get_registered_names()
    return jsonify({"students": names})

@app.route('/face_image/<name>')
def get_face_image(name):
    return send_from_directory(config.KNOWN_FACES_DIR, f"{name}.jpg")

@app.route('/get_attendance')
def get_attendance():
    data = attendance_service.get_today_records()
    return jsonify(data)

@app.route('/attendance_files')
def get_attendance_files():
    attendance_service.init_attendance_file()
    files = attendance_service.get_available_attendance_files(
        limit_days=config.LOG_RETENTION_DAYS
    )
    return jsonify({
        "files": files,
        "retention_days": config.LOG_RETENTION_DAYS
    })

@app.route('/download_attendance')
def download_attendance():
    attendance_service.cleanup_old_logs()
    date_str = request.args.get('date') or datetime.now().strftime("%Y-%m-%d")
    file_path = attendance_service.get_attendance_file_path_by_date(date_str)
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Ensure today's file exists even before the first check-in.
    if file_path is None and date_str == today_str:
        attendance_service.init_attendance_file()
        file_path = attendance_service.get_attendance_file_path_by_date(date_str)

    if file_path is None:
        return jsonify({
            "success": False,
            "message": f"No attendance file found for {date_str}."
        }), 404

    download_name = f"attendance_{date_str}_google_sheets.csv"
    return send_file(
        file_path,
        mimetype="text/csv",
        as_attachment=True,
        download_name=download_name
    )

@app.route('/clock_in', methods=['POST'])
def do_clock_in():
    data = request.get_json() or {}
    override = data.get('override', False)
    name_to_log = None
    with lock:
        name_to_log = current_name
        
    if name_to_log == "Unknown":
        return jsonify({"success": False, "message": "No recognized face."})
    success, msg, is_conflict = attendance_service.check_in(name_to_log, override)
    return jsonify({"success": success, "message": msg, "is_conflict": is_conflict})

@app.route('/clock_out', methods=['POST'])
def do_clock_out():
    data = request.get_json() or {}
    override = data.get('override', False)
    name_to_log = None
    with lock:
        name_to_log = current_name

    if name_to_log == "Unknown":
        return jsonify({"success": False, "message": "No recognized face."})
    success, msg, is_conflict = attendance_service.check_out(name_to_log, override)
    return jsonify({"success": success, "message": msg, "is_conflict": is_conflict})

@app.route('/register', methods=['POST'])
def do_register():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({"success": False, "message": "Name is required."})
    
    with lock:
        registration_request["name"] = name
        registration_request["result"] = None
        registration_request["pending"] = True
    
    start_time = time.time()
    while time.time() - start_time < 5:
        with lock:
            if registration_request["result"] is not None:
                return jsonify(registration_request["result"])
        time.sleep(0.1)
        
    return jsonify({"success": False, "message": "Registration timeout. Camera may be busy."})

@app.route('/delete_student/<name>', methods=['DELETE'])
def do_delete_student(name):
    success, msg = face_engine.engine.delete_student(name)
    if success:
        attendance_service.delete_student_from_today_log(name)
    return jsonify({"success": success, "message": msg})

@app.route('/rename_student', methods=['POST'])
def do_rename_student():
    data = request.get_json()
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    if not old_name or not new_name:
        return jsonify({"success": False, "message": "Missing names."})
    success, msg = face_engine.engine.rename_student(old_name, new_name)
    if success:
        attendance_service.rename_student_in_today_log(old_name, new_name)
    return jsonify({"success": success, "message": msg})

if __name__ == '__main__':
    cleanup_result = attendance_service.cleanup_old_logs()
    deleted_count = len(cleanup_result.get("deleted_files", []))
    if deleted_count:
        print(f"Retention cleanup removed {deleted_count} old attendance files.")

    # Start the background camera thread
    t = threading.Thread(target=camera_thread, daemon=True)
    t.start()
    
    print(f"Starting stabilized server at http://127.0.0.1:5050")
    app.run(host='127.0.0.1', port=5050, debug=False, threaded=True)

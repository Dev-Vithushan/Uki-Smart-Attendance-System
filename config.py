import os

# Camera settings
CAMERA_INDEX = 0  # Default webcam

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWN_FACES_DIR = os.path.join(BASE_DIR, "known_faces")
ATTENDANCE_LOG_DIR = os.path.join(BASE_DIR, "attendance_logs")

# Verification
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
os.makedirs(ATTENDANCE_LOG_DIR, exist_ok=True)

# Application settings
WINDOW_TITLE = "FaceFind Attendance System"
WINDOW_GEOMETRY = "800x650"

# Attendance retention
LOG_RETENTION_DAYS = 15

import os
import pandas as pd
from datetime import datetime
from config import ATTENDANCE_LOG_DIR
import face_engine

def get_today_file_path():
    """
    Returns the path to today's attendance CSV file within a monthly subdirectory.
    Example: attendance_logs/March/attendance_2026-03-31.csv
    """
    now = datetime.now()
    month_name = now.strftime("%B")
    date_str = now.strftime("%Y-%m-%d")
    
    # Create month folder if missing
    month_dir = os.path.join(ATTENDANCE_LOG_DIR, month_name)
    if not os.path.exists(month_dir):
        os.makedirs(month_dir)
        
    filename = f"attendance_{date_str}.csv"
    return os.path.join(month_dir, filename)

def init_attendance_file():
    """
    Ensures today's attendance file exists with headers and ALL registered students from the Master List.
    """
    path = get_today_file_path()
    
    # Check if exists or is empty
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        # Get all registered students from the MASTER LIST
        registered_list = face_engine.engine.get_registered_names()
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Pre-fill data
        rows = []
        for name in registered_list:
            rows.append({
                "Name": name,
                "Date": date_str,
                "Status": "Absent",
                "Clock-In": "",
                "Clock-Out": ""
            })
            
        df = pd.DataFrame(rows, columns=["Name", "Date", "Status", "Clock-In", "Clock-Out"])
        df.to_csv(path, index=False)
    return path

def check_in(name, override=False):
    """
    Logs a clock-in time for the given student (Updates their existing row).
    """
    name = name.strip().title()
    
    try:
        path = init_attendance_file()
        df = pd.read_csv(path)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M:%S")
        
        # Find the record for today
        mask = (df["Name"].str.title() == name) & (df["Date"] == date_str)
        
        if not mask.any():
            # In case student was registered AFTER the file was initialized today
            new_row = {"Name": name, "Date": date_str, "Status": "Present", "Clock-In": time_str, "Clock-Out": ""}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(path, index=False)
            return True, f"Successfully clocked in at {time_str}.", False

        # If already Present and not overriding
        idx = df[mask].index[-1]
        if df.at[idx, "Status"] == "Present" and not override:
             return False, f"Already clocked in at {df.at[idx, 'Clock-In']}.", True
            
        # Update existing row
        df.at[idx, "Status"] = "Present"
        df.at[idx, "Clock-In"] = time_str
        df.at[idx, "Name"] = name
        df.to_csv(path, index=False)
        
        msg = f"Clock-in overridden to {time_str}." if override else f"Successfully clocked in at {time_str}."
        return True, msg, False
    except Exception as e:
        return False, f"Error during clock-in: {e}", False

def check_out(name, override=False):
    """
    Logs a clock-out time for the given student (Updates their existing row).
    """
    name = name.strip().title()

    try:
        path = init_attendance_file()
        df = pd.read_csv(path)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M:%S")
        
        mask = (df["Name"].str.title() == name) & (df["Date"] == date_str)
        if not mask.any():
            return False, f"Could not find an active record for {name}.", False
            
        idx = df[mask].index[-1]
        
        # If they missed Clock-In but are Clocking-Out, we mark them Present
        if df.at[idx, "Status"] != "Present":
             df.at[idx, "Status"] = "Present"
        
        # Check if they already clocked out
        if pd.notna(df.at[idx, "Clock-Out"]) and df.at[idx, "Clock-Out"] != "" and not override:
            return False, f"Already clocked out at {df.at[idx, 'Clock-Out']}.", True

        # Update the clock-out time
        df.at[idx, "Clock-Out"] = time_str
        df.at[idx, "Name"] = name
        df.to_csv(path, index=False)
        
        msg = f"Clock-out overridden to {time_str}." if override else f"Successfully clocked out at {time_str}."
        return True, msg, False
    except Exception as e:
        return False, f"Error during clock-out: {e}", False

def get_today_records():
    """
    Returns today's attendance records, statistics, and absent list using MASTER LIST for truth.
    """
    try:
        path = init_attendance_file()
        df = pd.read_csv(path)
        df = df.fillna("")
        
        # Standardize for comparison
        df["Name"] = df["Name"].apply(lambda x: str(x).strip().title())
        
        # Current Master List (The Truth)
        current_master = [n.strip().title() for n in face_engine.engine.get_registered_names()]
        
        # Filter the DataFrame to ONLY show people still in the Master List
        df = df[df["Name"].isin(current_master)]
        
        records = df[df["Status"] == "Present"].to_dict('records')
        absent_names = df[df["Status"] == "Absent"]["Name"].tolist()
        
        total_registered = len(current_master)
        total_present = len(records)
            
        percentage = 0
        if total_registered > 0:
            percentage = round((total_present / total_registered) * 100, 1)

        return {
            "records": records,
            "absent_names": sorted(absent_names),
            "stats": {
                "total_registered": total_registered,
                "total_present": total_present,
                "percentage": percentage
            }
        }
    except Exception as e:
        print(f"Error fetching monthly records: {e}")
        return {"records": [], "absent_names": [], "stats": {"total_registered": 0, "total_present": 0, "percentage": 0}}

def delete_student_from_today_log(name):
    """
    Removes a student's row from today's log.
    """
    name = name.strip().title()
    try:
        path = get_today_file_path()
        if os.path.exists(path):
            df = pd.read_csv(path)
            df = df[df["Name"].str.title() != name]
            df.to_csv(path, index=False)
            return True
    except Exception as e:
        print(f"Error deleting from log: {e}")
    return False

def rename_student_in_today_log(old_name, new_name):
    """
    Updates a student's name in today's log.
    """
    old_name = old_name.strip().title()
    new_name = new_name.strip().title()
    try:
        path = get_today_file_path()
        if os.path.exists(path):
            df = pd.read_csv(path)
            df.loc[df["Name"].str.title() == old_name, "Name"] = new_name
            df.to_csv(path, index=False)
            return True
    except Exception as e:
        print(f"Error renaming in log: {e}")
    return False

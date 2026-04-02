import os
import pandas as pd
from datetime import datetime, timedelta
from config import ATTENDANCE_LOG_DIR, LOG_RETENTION_DAYS
import face_engine

ATTENDANCE_FILE_PREFIX = "attendance_"
ATTENDANCE_FILE_SUFFIX = ".csv"


def _extract_date_from_filename(filename):
    """Extracts a date object from filenames like attendance_2026-04-02.csv."""
    if not (
        filename.startswith(ATTENDANCE_FILE_PREFIX)
        and filename.endswith(ATTENDANCE_FILE_SUFFIX)
    ):
        return None

    date_part = filename[
        len(ATTENDANCE_FILE_PREFIX): -len(ATTENDANCE_FILE_SUFFIX)
    ]
    try:
        return datetime.strptime(date_part, "%Y-%m-%d").date()
    except ValueError:
        return None


def _iter_attendance_files():
    """Yields parsed attendance files from all monthly folders."""
    for root, _, files in os.walk(ATTENDANCE_LOG_DIR):
        for filename in files:
            file_date = _extract_date_from_filename(filename)
            if file_date is None:
                continue

            full_path = os.path.join(root, filename)
            month = os.path.basename(root)
            yield file_date, full_path, filename, month


def cleanup_old_logs(retention_days=LOG_RETENTION_DAYS):
    """
    Removes attendance files older than retention_days (inclusive window).
    Example: retention_days=15 keeps today and the previous 14 days.
    """
    try:
        retention_days = int(retention_days)
    except (TypeError, ValueError):
        retention_days = LOG_RETENTION_DAYS

    if retention_days < 1:
        retention_days = 1

    cutoff_date = datetime.now().date() - timedelta(days=retention_days - 1)
    deleted_files = []

    for file_date, full_path, _, _ in _iter_attendance_files():
        if file_date < cutoff_date:
            try:
                os.remove(full_path)
                deleted_files.append(full_path)
            except OSError as e:
                print(f"Failed deleting old log {full_path}: {e}")

    # Remove empty month folders after file cleanup.
    for root, dirs, files in os.walk(ATTENDANCE_LOG_DIR, topdown=False):
        if root == ATTENDANCE_LOG_DIR:
            continue
        if not dirs and not files:
            try:
                os.rmdir(root)
            except OSError:
                pass

    return {
        "deleted_files": deleted_files,
        "retention_days": retention_days,
        "cutoff_date": cutoff_date.isoformat(),
    }


def get_available_attendance_files(limit_days=None):
    """Returns available attendance CSV files sorted by newest date first."""
    collected = []
    for file_date, full_path, filename, month in _iter_attendance_files():
        collected.append(
            (
                file_date,
                {
                    "date": file_date.isoformat(),
                    "filename": filename,
                    "month": month,
                    "relative_path": os.path.relpath(full_path, ATTENDANCE_LOG_DIR),
                },
            )
        )

    collected.sort(key=lambda item: item[0], reverse=True)

    if limit_days is not None:
        try:
            limit_days = int(limit_days)
        except (TypeError, ValueError):
            limit_days = None

        if limit_days is not None and limit_days > 0:
            cutoff_date = datetime.now().date() - timedelta(days=limit_days - 1)
            collected = [item for item in collected if item[0] >= cutoff_date]

    return [item[1] for item in collected]


def get_attendance_file_path_by_date(date_str):
    """Returns the full CSV path for a YYYY-MM-DD date, or None if missing."""
    try:
        requested_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None

    expected_month = requested_date.strftime("%B")
    expected_filename = f"{ATTENDANCE_FILE_PREFIX}{requested_date.isoformat()}{ATTENDANCE_FILE_SUFFIX}"
    expected_path = os.path.join(ATTENDANCE_LOG_DIR, expected_month, expected_filename)
    if os.path.exists(expected_path):
        return expected_path

    # Fallback search to handle migrated folders.
    for file_date, full_path, _, _ in _iter_attendance_files():
        if file_date == requested_date:
            return full_path

    return None


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
    cleanup_old_logs()
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

# 🎓 Uki Smart Attendance System - Developer Guide

Welcome to the **Uki Smart Attendance System**. This is a production-ready, face-recognition-based attendance monitoring dashboard designed for macOS and Linux.

## 🚀 Key Features

- **🖼️ Real-Time Face Recognition**: Continuous camera monitoring with synchronized registration.
- **📊 Live Analytics Dashboard**: Real-time tracking of **Registered Students**, **Present Count**, and **Attendance Percentage**.
- **🚩 Smart Absent Tracker**: Automatically calculates and lists students who haven't clocked in for the day.
- **📂 Professional Logging**: Attendance files are organized into **Monthly Subfolders** (e.g., `attendance_logs/March/`).
- **🗂️ Master Repository**: Uses `students_master.csv` as a single source of truth for all student data, ensuring 100% data integrity.
- **🛠️ Self-Healing Data**: Automatically restores CSV headers and synchronizes deletions across all logs.

---

## 🛠️ Prerequisites

Before running the application, ensure your machine has:

1. **Python 3.9+**
2. **CMake**: Required to build the `face-recognition` library.
   - macOS: `brew install cmake`
   - Ubuntu: `sudo apt-get install cmake`
3. **C++ Compiler**: (e.g., Xcode Command Line Tools on Mac or `build-essential` on Linux).

---

## ⚙️ Installation & Setup (Multi-Platform)

### 1. Prerequisite Installations

#### 🍏 macOS
```bash
brew install cmake
```

#### 🐧 Ubuntu / Debian
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake
sudo apt-get install -y libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev
```

#### 🪟 Windows
1. **Install Python 3.9+** from [python.org](https://www.python.org/).
2. **Install CMake**: `pip install cmake`
3. **Install Visual Studio Build Tools**: 
   - Download from [visualstudio.microsoft.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
   - During installation, check the **"Desktop development with C++"** workload. This is mandatory for the `face-recognition` library.

### 2. Project Initialization (All Platforms)
```bash
# Clone the repository
git clone https://github.com/Dev-Vithushan/Uki-Smart-Attendance-System.git
cd Uki-Smart-Attendance-System

# Create and activate virtual environment
# Windows:
python -m venv venv
venv\Scripts\activate

# macOS / Ubuntu:
python3 -m venv venv
source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt
```
> [!IMPORTANT]
> This project uses `opencv-python-headless` for server stability and the `face-recognition` library which may take 5-10 minutes to compile during first install.

---

## 🏃 Running the Application

To start the server and the camera engine:

```bash
# Ensure no other service is using port 5050 (common on macOS)
lsof -ti:5050 | xargs kill -9 

# Start the app
python3 app.py
```

Access the dashboard at: **[http://localhost:5050](http://localhost:5050)**

---

## 📂 Project Structure

```text
Uki-Smart-Attendance-System/
├── app.py                 # Flask server & background camera thread
├── face_engine.py         # Face detection, encoding, & Master Repo logic
├── attendance_service.py   # CSV logging, monthly organization, & stats
├── config.py              # Central configuration (Camera index, paths)
├── templates/
│   └── index.html         # Responsive frontend dashboard (JS-driven)
├── known_faces/           # Storage for registered student images (.jpg)
├── attendance_logs/       # Monthly subfolders with daily CSV logs
└── students_master.csv    # MASTER DATABASE (Single source of truth)
```

---

## 🛡️ Database & Integrity

### The Master Repository (`students_master.csv`)
This system does NOT just rely on filenames. The `students_master.csv` manages the list of all students. 
- **Registration**: Capture a face → Creates `.jpg` → Adds to Master List.
- **Deletion**: Deleting a student → Removes `.jpg` → Removes from Master List → Cleans up Today's Log.
- **Renaming**: Renames `.jpg` → Updates Master Record → Updates all today's attendance entries.

---

## ❓ Troubleshooting

- **"Port 5050 already in use"**: On macOS Sequoia/Sonoma, the "AirPlay Receiver" uses port 5050. Run the kill command provided above or disable "AirPlay Receiver" in System Settings.
- **Camera Permission**: Ensure your Terminal/IDE has **Camera Access** in macOS System Settings > Privacy & Security.
- **No Face Recognized**: Ensure lighting is sufficient and you are looking directly at the camera.

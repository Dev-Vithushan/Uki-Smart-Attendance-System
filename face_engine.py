import face_recognition
import cv2
import numpy as np
import os
import pandas as pd
from datetime import datetime
from config import KNOWN_FACES_DIR

# Master student list path
MASTER_LIST_PATH = os.path.join(os.getcwd(), 'students_master.csv')

class FaceEngine:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self._init_master_list()
        self.load_known_faces()

    def _init_master_list(self):
        """
        Ensures the master student list exists. Synchronizes with filesystem if missing.
        """
        if not os.path.exists(MASTER_LIST_PATH):
            # Sync from existing folder if CSV is missing
            names = []
            for filename in os.listdir(KNOWN_FACES_DIR):
                if filename.endswith(".jpg"):
                    name = os.path.splitext(filename)[0].strip().title()
                    names.append({"Name": name, "RegDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            
            df = pd.DataFrame(names, columns=["Name", "RegDate"])
            df.to_csv(MASTER_LIST_PATH, index=False)
            print("Master student list initialized from filesystem.")

    def load_known_faces(self):
        """
        Loads images and encodings from the master list/filesystem.
        """
        self.known_face_encodings = []
        self.known_face_names = []
        
        # We load based on what's in the master list to ensure sync
        df = pd.read_csv(MASTER_LIST_PATH)
        for _, row in df.iterrows():
            name = row["Name"]
            image_path = os.path.join(KNOWN_FACES_DIR, f"{name}.jpg")
            
            if os.path.exists(image_path):
                try:
                    image = face_recognition.load_image_file(image_path)
                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        self.known_face_encodings.append(encodings[0])
                        self.known_face_names.append(name)
                except Exception as e:
                    print(f"Error loading {name}: {e}")

    def get_registered_names(self):
        """Returns names from the master list."""
        df = pd.read_csv(MASTER_LIST_PATH)
        return df["Name"].tolist()

    def register_face(self, frame, name):
        """
        Registers a face by saving the image and updating the master list.
        """
        name = name.strip().title()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if not face_locations:
            return False, "No face detected in frame."

        image_path = os.path.join(KNOWN_FACES_DIR, f"{name}.jpg")
        cv2.imwrite(image_path, frame)
        
        # Update Master List
        df = pd.read_csv(MASTER_LIST_PATH)
        if name not in df["Name"].values:
            new_row = {"Name": name, "RegDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(MASTER_LIST_PATH, index=False)
            
        self.load_known_faces()
        return True, f"Student {name} registered successfully."

    def delete_student(self, name):
        """
        Removes student from filesystem and master list.
        """
        name = name.strip().title()
        image_path = os.path.join(KNOWN_FACES_DIR, f"{name}.jpg")
        
        # Remove from Master List
        df = pd.read_csv(MASTER_LIST_PATH)
        df = df[df["Name"].str.title() != name]
        df.to_csv(MASTER_LIST_PATH, index=False)
        
        # Remove file
        if os.path.exists(image_path):
            os.remove(image_path)
            
        self.load_known_faces()
        return True, f"Student {name} deleted successfully from system."

    def rename_student(self, old_name, new_name):
        """
        Renames student in filesystem and master list.
        """
        old_name = old_name.strip().title()
        new_name = new_name.strip().title()
        
        old_path = os.path.join(KNOWN_FACES_DIR, f"{old_name}.jpg")
        new_path = os.path.join(KNOWN_FACES_DIR, f"{new_name}.jpg")
        
        # Update Master List
        df = pd.read_csv(MASTER_LIST_PATH)
        df.loc[df["Name"].str.title() == old_name, "Name"] = new_name
        df.to_csv(MASTER_LIST_PATH, index=False)
        
        # Rename file
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            
        self.load_known_faces()
        return True, f"Student renamed from {old_name} to {new_name}."

    def identify_faces(self, frame):
        """
        Identifies faces in the camera frame.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        face_names = []
        for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.5)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = self.known_face_names[first_match_index]

            face_names.append((name, (top, right, bottom, left)))

        return face_names

# Standard globally shared instance
engine = FaceEngine()

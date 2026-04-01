import os
import pickle
import threading
import time
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import config

# OAuth 2.0 Scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveService:
    def __init__(self):
        self.creds = None
        self.service = None
        self.upload_lock = threading.Lock()  # Thread safety
        self.pending_uploads = {}  # Track pending uploads to avoid duplicates
        self._authenticate()

    def _authenticate(self):
        """Authenticates using OAuth 2.0 flow (Token or Client Secrets)."""
        # 1. Load existing token if it exists
        if os.path.exists(config.TOKEN_FILE):
            try:
                with open(config.TOKEN_FILE, 'rb') as token:
                    self.creds = pickle.load(token)
                
                # Check if credentials are still valid
                if self.creds and not self.creds.valid:
                    if self.creds.expired and self.creds.refresh_token:
                        try:
                            self.creds.refresh(Request())
                        except Exception as e:
                            print(f"Token refresh failed: {e}")
                            self.creds = None
                
                if self.creds:
                    self.service = build('drive', 'v3', credentials=self.creds)
                    print("✓ OAuth token loaded successfully")
                    return
            except Exception as e:
                print(f"Error loading token: {e}")
                self.creds = None
        
        # If no token exists, just warn but don't block app startup
        print(f"⚠ No OAuth token found. Run 'python setup_oauth.py' to authorize first.")

    def _get_new_credentials(self):
        """Initiates the OAuth 2.0 flow to get new credentials."""
        if not os.path.exists(config.CLIENT_SECRETS_FILE):
            print(f"Error: {config.CLIENT_SECRETS_FILE} not found. Please follow the setup guide.")
            return None
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(config.CLIENT_SECRETS_FILE, SCOPES)
            # This will open a browser window for the user
            return flow.run_local_server(port=0)
        except Exception as e:
            print(f"OAuth Flow Error: {e}")
            return None

    def _find_file(self, filename, folder_id):
        """Checks if a Google Sheet with the given name exists in the target folder."""
        if not self.service:
            return None
            
        try:
            # Search for Google Sheets files (not CSV)
            query = f"name = '{filename}' and mimeType = 'application/vnd.google-apps.spreadsheet' and '{folder_id}' in parents and trashed = false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name, mimeType)').execute()
            files = results.get('files', [])
            
            if files:
                # Return the first matching file ID
                print(f"Found existing sheet: {filename}")
                return files[0]['id']
            else:
                print(f"No existing sheet found for: {filename}")
                return None
        except Exception as e:
            print(f"Drive search error: {e}")
            return None

    def _find_or_create_folder(self, folder_name, parent_id):
        """Finds a folder by name or creates it if it doesn't exist."""
        if not self.service:
            return parent_id
            
        try:
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            else:
                # Create folder
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_id]
                }
                folder = self.service.files().create(body=file_metadata, fields='id').execute()
                print(f"Drive Sync: Created folder '{folder_name}'")
                return folder.get('id')
        except Exception as e:
            print(f"Drive folder error: {e}")
            return parent_id

    def upload_file(self, local_path, folder_id=None):
        """Uploads CSV file to Google Drive and converts it to Google Sheets format."""
        with self.upload_lock:
            if not self.service:
                self._authenticate()
                if not self.service:
                    print("❌ Drive Sync: Not authenticated")
                    return False

            parent_id = folder_id or config.GOOGLE_DRIVE_FOLDER_ID
            if parent_id == "YOUR_FOLDER_ID_HERE":
                print("Drive Sync Warning: Folder ID not set in config.py")
                return False

            # Extract date and filename info
            filename = os.path.basename(local_path)
            folder_name = None
            try:
                date_str = filename.split('_')[1].split('.')[0]
                from datetime import datetime
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                folder_name = date_obj.strftime('%B-%y')
            except Exception:
                path_parts = local_path.split(os.sep)
                if len(path_parts) >= 2:
                    folder_name = path_parts[-2]

            # Create/Find month folder
            if folder_name:
                parent_id = self._find_or_create_folder(folder_name, parent_id)

            # Remove .csv extension for the Google Sheets name
            sheet_name = filename.replace('.csv', '')
            
            # Check if file already exists in Drive
            file_id = self._find_file(sheet_name, parent_id)
            
            try:
                # Upload CSV and convert to Google Sheets
                media = MediaFileUpload(local_path, mimetype='text/csv', resumable=False)
                
                if file_id:
                    # Update existing sheet - this will refresh the data
                    self.service.files().update(fileId=file_id, media_body=media).execute()
                    print(f"✓ Drive Sync: Updated {sheet_name} in {folder_name}")
                    return True
                else:
                    # Create new Google Sheet from CSV
                    file_metadata = {
                        'name': sheet_name,
                        'mimeType': 'application/vnd.google-apps.spreadsheet',
                        'parents': [parent_id]
                    }
                    file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                    print(f"✓ Drive Sync: Created {sheet_name} in {folder_name}")
                    return True
            except Exception as e:
                print(f"❌ Drive upload error: {e}")
                return False

# Create a singleton instance
sync_service = GoogleDriveService()

def sync_to_drive_async(file_path):
    """Triggers a background thread to sync the file to Google Drive."""
    thread = threading.Thread(target=sync_service.upload_file, args=(file_path,))
    thread.daemon = True
    thread.start()

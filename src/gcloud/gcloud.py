import hashlib
import io
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config


class SharedDrive:
    def __init__(
        self,
        shared_folder=config.GDRIVE_DATABASE,
        local_data_dir=config.DEFAULT_DATA_DIR,
    ):
        self.service = self._authenticate()
        self.shared_folder = shared_folder
        self.local_data_dir = local_data_dir

    def _authenticate(self):
        SCOPES = ["https://www.googleapis.com/auth/drive"]
        creds = None
        if os.path.exists(config.GCLOUD_ACCESS_TOKEN):
            creds = Credentials.from_authorized_user_file(
                config.GCLOUD_ACCESS_TOKEN, SCOPES
            )
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.GCLOUD_SECRET, SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(config.GCLOUD_ACCESS_TOKEN, "w") as token:
                token.write(creds.to_json())

        return build("drive", "v3", credentials=creds)

    def sync_all(self):
        self._sync_dir_recursive(self.local_data_dir, self.shared_folder)

    def _sync_dir_recursive(self, local_dir, parent_folder_id):
        remote_subfolders = self._get_remote_subfolders(parent_folder_id)

        for file_path in local_dir.iterdir():
            if file_path.is_file():
                self._sync_file(file_path, parent_folder_id=parent_folder_id)
            elif file_path.is_dir():
                subfolder_name = file_path.name
                subfolder_id = remote_subfolders.get(subfolder_name)
                if not subfolder_id:
                    subfolder_id = self._create_remote_subfolder(
                        subfolder_name, parent_folder_id
                    )
                self._sync_dir_recursive(file_path, parent_folder_id=subfolder_id)

    def _sync_file(self, local_file_path, parent_folder_id):
        local_file_name = local_file_path.name
        drive_files = (
            self.service.files()
            .list(
                q=f"'{parent_folder_id}' in parents and name='{local_file_name}'",
                fields="files(id, name, md5Checksum)",
            )
            .execute()
            .get("files", [])
        )

        if drive_files:
            drive_file = drive_files[0]
            local_file_md5 = hashlib.md5(local_file_path.read_bytes()).hexdigest()
            if drive_file["md5Checksum"] != local_file_md5:
                media = MediaFileUpload(local_file_path, resumable=True)
                updated_file = (
                    self.service.files()
                    .update(fileId=drive_file["id"], media_body=media, fields="id")
                    .execute()
                )
                print(f"Updated file ID: {updated_file.get('id')}")
        else:
            file_metadata = {"name": local_file_name, "parents": [parent_folder_id]}
            media = MediaFileUpload(local_file_path, resumable=True)
            uploaded_file = (
                self.service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            print(f"Uploaded file ID: {uploaded_file.get('id')}")

    def _get_remote_subfolders(self, parent_folder_id):
        subfolders = {}
        results = (
            self.service.files()
            .list(
                q=f"'{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)",
            )
            .execute()
        )
        items = results.get("files", [])
        for item in items:
            subfolders[item["name"]] = item["id"]
        return subfolders

    def _create_remote_subfolder(self, subfolder_name, parent_folder_id):
        folder_metadata = {
            "name": subfolder_name,
            "parents": [parent_folder_id],
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = (
            self.service.files().create(body=folder_metadata, fields="id").execute()
        )
        return folder.get("id")

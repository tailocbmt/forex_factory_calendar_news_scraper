from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account


class DriveUploader:
    def __init__(
            self,
            service_account_file="credentials.json",
            root_folder_id="1SIG6fkN9l4DCYHFCW7PzTpWGr_WsGwYh"
    ):
        """
        Initializes the DriveUploader with authentication and service setup.

        :param service_account_file: Path to the Google service account credentials JSON file.
        :param root_folder_id: ID of the root folder where files and subfolders will be managed.
        """
        self.service_account_file = service_account_file
        self.root_folder_id = root_folder_id
        self.creds = self.authenticate()
        self.service = build("drive", "v3", credentials=self.creds)

    def authenticate(self):
        """Authenticates using a Google service account."""
        return service_account.Credentials.from_service_account_file(
            self.service_account_file,
            scopes=[
                "https://www.googleapis.com/auth/drive"]
        )

    def search_drive(self, parent_folder_id, **params):
        """
        Searches for a file or folder in Google Drive.

        :param parent_folder_id: The ID of the parent folder where the search is performed.
        :param params: Dictionary containing either 'file_name' or 'folder_name'.
        :return: File or folder ID if found, else None.
        """
        name = params.get('file_name') or params.get('folder_name', '')
        mime_type = 'application/vnd.google-apps.folder' if 'folder_name' in params else ''

        query = f"name = '{name}' and '{parent_folder_id}' in parents and trashed = false"
        if mime_type:
            query += f" and mimeType = '{mime_type}'"

        results = self.service.files().list(q=query, fields="files(id)").execute()
        files = results.get("files", [])
        return files[0]["id"] if files else None

    def create_folder(self, folder_name, parent_folder_id=None):
        """
        Creates a folder in Google Drive if it doesn't exist.

        :param folder_name: Name of the folder to create.
        :param parent_folder_id: The ID of the parent folder (default is root).
        :return: The ID of the created or existing folder.
        """
        parent_folder_id = parent_folder_id or self.root_folder_id
        folder_metadata = {
            "name": folder_name,
            "parents": [parent_folder_id],
            "mimeType": "application/vnd.google-apps.folder"
        }
        folder = self.service.files().create(body=folder_metadata, fields="id").execute()
        print(f"Created folder '{folder_name}' with ID: {folder.get('id')}")
        return folder.get("id")

    def delete_permanently(self, file_id):
        """
        Permanently deletes a file from Google Drive.

        :param file_id: ID of the file to delete.
        """
        self.service.files().delete(fileId=file_id).execute()
        print(f"Deleted existing file with ID: {file_id}")

    def update_file(self, file_path):
        """
        Uploads a file to a specific Google Drive folder, replacing it if it already exists.

        :param file_path: Path to the file to upload.
        :return: The ID of the uploaded file.
        """
        file_name = file_path.split("/")[-1]

        # Check if file exists; delete it if found
        existing_file_id = self.search_drive(
            parent_folder_id=self.root_folder_id, file_name=file_name)

        # Define metadata for the new file
        media = MediaFileUpload(file_path, mimetype="text/csv")

        # Upload the new file
        created_file = {}
        if existing_file_id:
            file_metadata = {
                "name": file_name,
                "addParents": [self.root_folder_id]
            }
            created_file = self.service.files().update(
                fileId=existing_file_id,
                body=file_metadata,
                media_body=media,
                fields="id").execute()
        else:
            file_metadata = {
                "name": file_name,
                "parents": [self.root_folder_id]
            }
            created_file = self.service.files().create(
                body=file_metadata, media_body=media, fields="id").execute()

        print(
            f"File uploaded successfully to folder, File ID: {created_file.get('id')}")
        return created_file.get("id")

    def upload_or_replace_file(self, file_path, folder_name):
        """
        Uploads a file to a specific Google Drive folder, replacing it if it already exists.

        :param file_path: Path to the file to upload.
        :param folder_name: Name of the folder where the file will be uploaded.
        :return: The ID of the uploaded file.
        """
        file_name = file_path.split("/")[-1]

        # Check if folder exists; create it if not
        folder_id = self.search_drive(
            parent_folder_id=self.root_folder_id, folder_name=folder_name)
        if not folder_id:
            folder_id = self.create_folder(folder_name)

        # Check if file exists; delete it if found
        existing_file_id = self.search_drive(
            parent_folder_id=folder_id, file_name=file_name)
        if existing_file_id:
            self.delete_permanently(existing_file_id)

        # Define metadata for the new file
        file_metadata = {
            "name": file_name,
            "parents": [folder_id]
        }
        media = MediaFileUpload(file_path, mimetype="text/csv")

        # Upload the new file
        created_file = self.service.files().create(
            body=file_metadata, media_body=media, fields="id").execute()

        print(
            f"File uploaded successfully to folder '{folder_name}', File ID: {created_file.get('id')}")
        return created_file.get("id")


# Example Usage
if __name__ == "__main__":
    uploader = DriveUploader(service_account_file="credentials.json")

    # Example: Upload or replace a CSV file
    file_path = "your_file.csv"  # Change this to your CSV file path
    # Change this to your desired Google Drive folder name
    folder_name = "My Drive Folder"
    uploader.upload_or_replace_file(
        file_path,
        folder_name)

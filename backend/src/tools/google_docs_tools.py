import os, re
import tempfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.utils import get_google_credentials


class GoogleDocsManager:
    def __init__(self):
        # Disable cache_discovery to suppress oauth2client deprecation warning
        self.docs_service = build("docs", "v1", credentials=get_google_credentials(), cache_discovery=False)
        self.drive_service = build("drive", "v3", credentials=get_google_credentials(), cache_discovery=False)

    def folder_has_files(self, folder_path: str) -> bool:
        """
        Check if the given Drive folder (by path) already contains any files.
        Returns True if there is at least one file, False otherwise.
        """
        try:
            folder_id, _ = self.ensure_folder_path(folder_path, make_shareable=False)
            if not folder_id:
                return False
            query = f"'{folder_id}' in parents and trashed=false"
            results = (
                self.drive_service.files()
                .list(q=query, spaces="drive", pageSize=1, fields="files(id)")
                .execute()
            )
            files = results.get("files", [])
            return bool(files)
        except Exception as e:
            print(f"Failed to check files in Drive folder '{folder_path}': {e}")
            return False

    def document_exists_in_folder(self, folder_path: str, title: str) -> bool:
        """
        Check if a document with the given title already exists in the specified folder path.
        """
        if not title:
            return False
        try:
            folder_id, _ = self.ensure_folder_path(folder_path, make_shareable=False)
            if not folder_id:
                return False
            escaped_title = title.replace("'", "\\'")
            query = (
                f"name='{escaped_title}' and '{folder_id}' in parents and trashed=false"
            )
            results = (
                self.drive_service.files()
                .list(q=query, spaces="drive", pageSize=1, fields="files(id)")
                .execute()
            )
            files = results.get("files", [])
            return bool(files)
        except Exception as e:
            print(
                f"Failed to check existence of document '{title}' "
                f"in Drive folder '{folder_path}': {e}"
            )
            return False

    def add_document(
        self,
        content,
        doc_title,
        folder_name,
        make_shareable=False,
        folder_shareable=False,
        markdown=False,
    ):
        """
        Create a Google Document and save it in the specified folder.
        """
        try:
            # Ensure the folder exists (supports nested paths like "Root/Sub/Leaf")
            if "/" in folder_name:
                folder_id, folder_url = self._get_or_create_folder_by_path(
                    folder_name, make_shareable=folder_shareable
                )
            else:
                folder_id, folder_url = self._get_or_create_folder(
                    folder_name, make_shareable=folder_shareable
                )
            if not folder_id:
                raise ValueError("Failed to get or create the folder.")

            if markdown:
                # Convert Markdown to Google Doc
                doc_id = self.convert_markdown_to_google_doc(content, doc_title)
            else:
                # Create a new Google Document and add content
                doc = (
                    self.docs_service.documents()
                    .create(body={"title": doc_title})
                    .execute()
                )
                doc_id = doc.get("documentId")

                # Add content to the document
                requests = [{"insertText": {"location": {"index": 1}, "text": content}}]
                self.docs_service.documents().batchUpdate(
                    documentId=doc_id, body={"requests": requests}
                ).execute()

            # Move the document to the folder
            self.drive_service.files().update(
                fileId=doc_id,
                addParents=folder_id,
                removeParents="root",
                fields="id, parents",
            ).execute()

            shareable_url = None
            if make_shareable:
                shareable_url = self._make_document_shareable(doc_id)

            document_url = f"https://docs.google.com/document/d/{doc_id}"
            return {
                "document_url": document_url,
                "shareable_url": shareable_url,
                "folder_url": folder_url,
            }
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_document(self, doc_url):
        """
        Retrieve the content of a Google Document by its URL.
        """
        try:
            # Extract the document ID from the URL
            match = re.search(r"/d/([a-zA-Z0-9-_]+)", doc_url)
            if not match:
                raise ValueError("Invalid Google Docs URL format.")
            doc_id = match.group(1)

            # Fetch the document
            document = self.docs_service.documents().get(documentId=doc_id).execute()
            content = ""
            for element in document.get("body", {}).get("content", []):
                if "paragraph" in element:
                    for text_run in element["paragraph"].get("elements", []):
                        content += text_run.get("textRun", {}).get("content", "")

            return content
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def _get_or_create_folder(self, folder_name, make_shareable=False):
        """
        Get the ID and link of an existing folder with the specified name, or create one if it doesn't exist.
        """
        try:
            # Search for the folder
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            results = (
                self.drive_service.files()
                .list(q=query, spaces="drive", fields="files(id, name, webViewLink)")
                .execute()
            )
            files = results.get("files", [])

            if files:
                # Folder exists
                folder = files[0]
                folder_id = folder["id"]
                folder_link = folder.get("webViewLink")
            else:
                # Folder doesn't exist, create it
                file_metadata = {
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                }
                folder = (
                    self.drive_service.files()
                    .create(body=file_metadata, fields="id, webViewLink")
                    .execute()
                )
                folder_id = folder["id"]
                folder_link = folder.get("webViewLink")

            # Make the folder shareable if required
            if make_shareable:
                self.drive_service.permissions().create(
                    fileId=folder_id,
                    body={"type": "anyone", "role": "reader"},
                    fields="id",
                ).execute()

            return folder_id, folder_link
        except Exception as e:
            print(f"An error occurred while retrieving or creating the folder: {e}")
            return None, None

    def _get_or_create_folder_by_path(self, path, make_shareable=False):
        """
        Create or get a nested folder path like 'Root/Sub/Leaf' and return the final folder ID and link.
        """
        try:
            parts = [p.strip() for p in path.split("/") if p.strip()]
            if not parts:
                return self._get_or_create_folder(path, make_shareable=make_shareable)

            parent_id = "root"
            last_folder_link = None
            for i, name in enumerate(parts):
                # Find folder with this name under current parent
                escaped_name = name.replace("'", "\\'")
                query = (
                    "mimeType='application/vnd.google-apps.folder' "
                    f"and name='{escaped_name}' "
                    f"and '{parent_id}' in parents and trashed=false"
                )
                results = (
                    self.drive_service.files()
                    .list(
                        q=query, spaces="drive", fields="files(id, name, webViewLink)"
                    )
                    .execute()
                )
                files = results.get("files", [])
                if files:
                    folder = files[0]
                    parent_id = folder["id"]
                    last_folder_link = folder.get("webViewLink")
                else:
                    file_metadata = {
                        "name": name,
                        "mimeType": "application/vnd.google-apps.folder",
                        "parents": [parent_id],
                    }
                    folder = (
                        self.drive_service.files()
                        .create(body=file_metadata, fields="id, webViewLink")
                        .execute()
                    )
                    parent_id = folder["id"]
                    last_folder_link = folder.get("webViewLink")

                # Only make the final leaf folder shareable if requested
                if make_shareable and i == len(parts) - 1:
                    self.drive_service.permissions().create(
                        fileId=parent_id,
                        body={"type": "anyone", "role": "reader"},
                        fields="id",
                    ).execute()

            return parent_id, last_folder_link
        except Exception as e:
            print(f"An error occurred while creating nested folder path '{path}': {e}")
            return None, None

    def ensure_folder_path(self, folder_path, make_shareable=False):
        """
        Public helper to ensure a folder (optionally nested) exists.
        Returns (folder_id, folder_url) or (None, None) on failure.
        """
        try:
            if "/" in folder_path:
                return self._get_or_create_folder_by_path(
                    folder_path, make_shareable=make_shareable
                )
            return self._get_or_create_folder(
                folder_path, make_shareable=make_shareable
            )
        except Exception as e:
            print(f"Failed to ensure Drive folder '{folder_path}': {e}")
            return None, None

    def _make_document_shareable(self, doc_id):
        """Make a document shareable with anyone who has the link."""
        try:
            self.drive_service.permissions().create(
                fileId=doc_id, body={"type": "anyone", "role": "reader"}, fields="id"
            ).execute()
            file_info = (
                self.drive_service.files()
                .get(fileId=doc_id, fields="webViewLink")
                .execute()
            )
            return file_info.get("webViewLink")
        except Exception as e:
            print(f"Failed to make document shareable: {e}")
            return None

    def convert_markdown_to_google_doc(self, markdown_content, title):
        temp_file_path = None
        try:
            fd, temp_file_path = tempfile.mkstemp(suffix=".md")
            os.close(fd)
            with open(temp_file_path, "w", encoding="utf-8", newline="") as f:
                f.write(markdown_content)

            file_metadata = {
                "name": title,
                "mimeType": "application/vnd.google-apps.document",
            }
            media = MediaFileUpload(
                temp_file_path, mimetype="text/markdown", resumable=False
            )
            resp = (
                self.drive_service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            return resp.get("id")
        except Exception as e:
            print(f"Failed to convert Markdown to Google Doc: {e}")
            return None
        finally:
            if temp_file_path:
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass
    def upload_file(self, file_path, file_name, folder_name, make_shareable=False):
        """
        Upload a binary file to Google Drive.
        """
        try:
            # Ensure the folder exists
            if "/" in folder_name:
                folder_id, folder_url = self._get_or_create_folder_by_path(
                    folder_name, make_shareable=True
                )
            else:
                folder_id, folder_url = self._get_or_create_folder(
                    folder_name, make_shareable=True
                )
            
            if not folder_id:
                raise ValueError("Failed to get or create the folder.")

            file_metadata = {
                "name": file_name,
                "parents": [folder_id]
            }
            
            # Determine mime type based on extension
            mime_type = "application/octet-stream"
            if file_name.endswith(".xlsx"):
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif file_name.endswith(".csv"):
                mime_type = "text/csv"
                
            media = MediaFileUpload(
                file_path, mimetype=mime_type, resumable=True
            )
            
            file = (
                self.drive_service.files()
                .create(body=file_metadata, media_body=media, fields="id, webViewLink")
                .execute()
            )
            
            file_id = file.get("id")
            file_link = file.get("webViewLink")
            
            if make_shareable:
                self._make_document_shareable(file_id)
                
            return file_link
            
        except Exception as e:
            print(f"Failed to upload file to Drive: {e}")
            return None

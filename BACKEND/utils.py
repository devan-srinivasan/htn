#For Google Docs / Google Drive Integration
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
#For initial authentication
from google_auth_oauthlib.flow import InstalledAppFlow

#Get scopes for the API
PROJECT_SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]
#Path to credentials
credentials_filepath = "client_secrets.json"
#Authentication flow
authentication_flow = InstalledAppFlow.from_client_secrets_file(credentials_filepath, scopes = PROJECT_SCOPES)
#Begin flow for token transfer + authorization
CREDENTIALS = authentication_flow.run_local_server()

#SET UP CLIENTS FOR GOOGLE DOCS AND DRIVE
google_drive_client = build("drive", "v3", credentials = CREDENTIALS)
google_docs_client = build("docs", "v1", credentials = CREDENTIALS)

def createGoogleDoc(extracted_text : str, image_filepath : str):
    #Create new Google doc
    new_document = google_docs_client.documents().create().execute()
    new_document_id = new_document["documentId"]
    #Format request
    request = [
        {
            "insertText" : {
                "location" : {
                    "index" : 1,
                },
                "text" : extracted_text,
            },
        },
    ]
    #Send and complete request
    google_docs_client.documents().batchUpdate(documentId = new_document_id, body = {"requests" : request}).execute()
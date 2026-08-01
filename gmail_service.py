import os
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def connect_gmail():

    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


def get_email_body(payload):

    # Simple email
    data = payload.get("body", {}).get("data")

    if data:
        return base64.urlsafe_b64decode(
            data
        ).decode("utf-8", errors="ignore")

    # Multipart email
    for part in payload.get("parts", []):

        if part.get("mimeType") == "text/plain":

            data = part.get("body", {}).get("data")

            if data:
                return base64.urlsafe_b64decode(
                    data
                ).decode("utf-8", errors="ignore")

        # Search nested parts
        body = get_email_body(part)

        if body:
            return body

    return "No readable email body found."


def get_latest_emails(limit=20):

    service = connect_gmail()

    results = service.users().messages().list(
        userId="me",
        maxResults=limit
    ).execute()

    messages = results.get("messages", [])

    emails = []

    for message in messages:

        msg = service.users().messages().get(
            userId="me",
            id=message["id"],
            format="full"
        ).execute()

        payload = msg["payload"]

        sender = "Unknown"
        subject = "No Subject"

        for header in payload.get("headers", []):

            if header["name"].lower() == "from":
                sender = header["value"]

            elif header["name"].lower() == "subject":
                subject = header["value"]

        emails.append({
            "id": message["id"],
            "sender": sender,
            "subject": subject,
            "body": get_email_body(payload)
        })

    return emails
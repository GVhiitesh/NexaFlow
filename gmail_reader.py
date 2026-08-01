import os
import base64
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from email_classifier import classify_email
from notification_filter import should_notify
from whatsapp_sender import send_whatsapp_message
from processed_emails import is_processed, save_processed_email


# ============================================================
# SETTINGS
# ============================================================

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Fetch latest 20 emails from Gmail
GMAIL_FETCH_LIMIT = 20

# But process maximum 5 NEW emails per run
MAX_EMAILS_PER_RUN = 5

# Wait between AI requests to reduce rate-limit problems
AI_DELAY_SECONDS = 5


# ============================================================
# GMAIL AUTHENTICATION
# ============================================================

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


# Connect to Gmail
service = build(
    "gmail",
    "v1",
    credentials=creds
)


# ============================================================
# EMAIL BODY EXTRACTOR
# ============================================================

def get_email_body(payload):

    # Simple email
    if "data" in payload.get("body", {}):

        data = payload["body"]["data"]

        return base64.urlsafe_b64decode(
            data
        ).decode(
            "utf-8",
            errors="ignore"
        )

    # Multipart email
    for part in payload.get("parts", []):

        # Prefer plain-text email body
        if part.get("mimeType") == "text/plain":

            data = part.get(
                "body",
                {}
            ).get("data")

            if data:

                return base64.urlsafe_b64decode(
                    data
                ).decode(
                    "utf-8",
                    errors="ignore"
                )

        # Search nested email parts
        body = get_email_body(part)

        if body:
            return body

    return "No readable email body found."


# ============================================================
# GET LATEST EMAILS
# ============================================================

print("\n📧 InboxIQ starting...")

results = service.users().messages().list(
    userId="me",
    maxResults=GMAIL_FETCH_LIMIT
).execute()

messages = results.get("messages", [])

print(f"Found {len(messages)} recent emails.")

processed_this_run = 0


# ============================================================
# PROCESS EMAILS
# ============================================================

for message in messages:

    email_id = message["id"]


    # --------------------------------------------------------
    # SKIP EMAILS WE ALREADY PROCESSED
    # --------------------------------------------------------

    if is_processed(email_id):

        print(
            f"\n⏭️ Already processed: {email_id}"
        )

        continue


    # --------------------------------------------------------
    # DOWNLOAD EMAIL
    # --------------------------------------------------------

    try:

        msg = service.users().messages().get(
            userId="me",
            id=email_id,
            format="full"
        ).execute()

    except Exception as e:

        print(
            f"❌ Failed to download email {email_id}: {e}"
        )

        continue


    payload = msg["payload"]
    headers = payload.get("headers", [])


    # --------------------------------------------------------
    # EXTRACT EMAIL INFORMATION
    # --------------------------------------------------------

    sender = "Unknown"
    subject = "No Subject"

    for header in headers:

        if header["name"].lower() == "from":
            sender = header["value"]

        elif header["name"].lower() == "subject":
            subject = header["value"]


    body = get_email_body(payload)


    # --------------------------------------------------------
    # DISPLAY EMAIL
    # --------------------------------------------------------

    print("\n" + "=" * 60)

    print("Email ID:", email_id)
    print("From:", sender)
    print("Subject:", subject)

    print("\nBody:")
    print(body[:500])


    # --------------------------------------------------------
    # AI CLASSIFICATION
    # --------------------------------------------------------

    print("\n🤖 Analyzing with InboxIQ AI...")

    try:

        result = classify_email(
            sender,
            subject,
            body[:3000]
        )

    except Exception as e:

        print("\n❌ AI classification failed:")
        print(e)

        # Do not mark as processed.
        # InboxIQ can retry this email later.
        continue


    # --------------------------------------------------------
    # DISPLAY AI RESULT
    # --------------------------------------------------------

    print("\n--- InboxIQ Result ---")

    print(
        "Important:",
        result.get("important")
    )

    print(
        "Score:",
        result.get("importance_score")
    )

    print(
        "Category:",
        result.get("category")
    )

    print(
        "Summary:",
        result.get("summary")
    )

    print(
        "Action Required:",
        result.get("action_required")
    )

    print(
        "Action:",
        result.get("action")
    )

    print(
        "Deadline:",
        result.get("deadline")
    )


    # --------------------------------------------------------
    # NOTIFICATION DECISION
    # --------------------------------------------------------

    if should_notify(result):

        print(
            "\n🚨 WHATSAPP NOTIFICATION REQUIRED"
        )


        # Build WhatsApp message
        whatsapp_message = f"""🚨 InboxIQ Alert

📧 {subject}

From: {sender}

Summary:
{result.get('summary')}

Importance: {result.get('importance_score')}/100

Category: {result.get('category')}

Action:
{result.get('action')}

Deadline:
{result.get('deadline') or 'None'}
"""


        # ----------------------------------------------------
        # SEND WHATSAPP
        # ----------------------------------------------------

        print(
            "\n📱 Sending WhatsApp notification..."
        )

        try:

            success = send_whatsapp_message(
                whatsapp_message
            )

        except Exception as e:

            print(
                f"❌ WhatsApp sender error: {e}"
            )

            success = False


        # ----------------------------------------------------
        # WHATSAPP SUCCESS
        # ----------------------------------------------------

        if success:

            print(
                "✅ WhatsApp notification sent."
            )

            save_processed_email(
                email_id
            )

            print(
                "✅ Email marked as processed."
            )


        # ----------------------------------------------------
        # WHATSAPP FAILURE
        # ----------------------------------------------------

        else:

            print(
                "❌ WhatsApp notification failed."
            )

            print(
                "🔄 Email NOT marked as processed."
            )

            print(
                "InboxIQ will retry it later."
            )


    # --------------------------------------------------------
    # NO NOTIFICATION REQUIRED
    # --------------------------------------------------------

    else:

        print(
            "\n🔕 No WhatsApp notification needed."
        )

        save_processed_email(
            email_id
        )

        print(
            "✅ Email marked as processed."
        )


    # --------------------------------------------------------
    # COUNT THIS EMAIL
    # --------------------------------------------------------

    processed_this_run += 1

    print("\n" + "=" * 60)


    # --------------------------------------------------------
    # STOP AFTER MAXIMUM EMAIL LIMIT
    # --------------------------------------------------------

    if processed_this_run >= MAX_EMAILS_PER_RUN:

        print(
            f"\n🛑 Maximum of "
            f"{MAX_EMAILS_PER_RUN} emails reached."
        )

        break


    # --------------------------------------------------------
    # WAIT BEFORE NEXT GEMINI REQUEST
    # --------------------------------------------------------

    print(
        f"\n⏳ Waiting {AI_DELAY_SECONDS} seconds "
        f"before next email..."
    )

    time.sleep(
        AI_DELAY_SECONDS
    )


# ============================================================
# FINISHED
# ============================================================

print("\n========================================")

print(
    f"✅ InboxIQ finished."
)

print(
    f"New emails handled this run: "
    f"{processed_this_run}"
)

print("========================================\n")
import os
import requests
from dotenv import load_dotenv

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
RECIPIENT = os.getenv("WHATSAPP_RECIPIENT")

# ============================================================
# SEND WHATSAPP MESSAGE
# ============================================================

def send_whatsapp_message(message):
    url = (
        f"https://graph.facebook.com/v25.0/"
        f"{PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": RECIPIENT,
        "type": "text",
        "text": {
            "body": message
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=30
    )

    if response.ok:
        print("✅ WhatsApp message sent!")
        print("Status:", response.status_code)
        print("Response:")
        print(response.text)
        return True

    print("❌ WhatsApp error:")
    print("Status:", response.status_code)
    print("Response:")
    print(response.text)
    return False


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("Starting WhatsApp test...")

    send_whatsapp_message(
        "🚨 InboxIQ Test\n\n"
        "WhatsApp integration is working!"
    )
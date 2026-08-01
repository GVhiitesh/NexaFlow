import json
import os

FILE_NAME = "processed_emails.json"


def load_processed_emails():
    if not os.path.exists(FILE_NAME):
        return set()

    with open(FILE_NAME, "r", encoding="utf-8") as file:
        return set(json.load(file))


def is_processed(email_id):
    processed = load_processed_emails()
    return email_id in processed


def save_processed_email(email_id):
    processed = load_processed_emails()

    processed.add(email_id)

    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(list(processed), file, indent=2)
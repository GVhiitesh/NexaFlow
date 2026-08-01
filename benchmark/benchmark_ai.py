import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# -----------------------------
# PATHS
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "dataset" / "email_evaluation_dataset.json"
RESULTS_PATH = BASE_DIR / "benchmark" / "gemini_results.json"

# -----------------------------
# GEMINI SETUP
# -----------------------------

load_dotenv(BASE_DIR / ".env")
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

# -----------------------------
# LOAD DATASET
# -----------------------------

with open(DATASET_PATH, "r", encoding="utf-8") as file:
    emails = json.load(file)

print(f"Loaded {len(emails)} emails.")

# -----------------------------
# LOAD PREVIOUS RESULTS
# -----------------------------

if RESULTS_PATH.exists():
    with open(RESULTS_PATH, "r", encoding="utf-8") as file:
        results = json.load(file)

    print(f"Loaded {len(results)} previous results.")
else:
    results = []

# IDs already successfully processed
processed_ids = {result["id"] for result in results}

# Only process unfinished emails
remaining_emails = [
    email for email in emails
    if email["id"] not in processed_ids
]

print(f"Remaining emails: {len(remaining_emails)}")

# -----------------------------
# SETTINGS
# -----------------------------

BATCH_SIZE = 10
MAX_RETRIES = 3

# -----------------------------
# PROCESS BATCHES
# -----------------------------

for start in range(0, len(remaining_emails), BATCH_SIZE):

    batch = remaining_emails[start:start + BATCH_SIZE]

    email_data = []

    for email in batch:
        email_data.append({
            "id": email["id"],
            "sender": email["sender"],
            "subject": email["subject"],
            "body": email["body"]
        })

    prompt = f"""
Analyze each of the following emails.

For every email determine:

- important: true or false
- importance_score: integer from 0 to 100
- category: short lowercase category
- action_required: true or false
- deadline: YYYY-MM-DD or null

Return ONLY a valid JSON array.

Example:

[
  {{
    "id": 1,
    "important": true,
    "importance_score": 90,
    "category": "internship",
    "action_required": true,
    "deadline": "2026-07-25"
  }}
]

Return one result for EVERY email.
Do not include markdown.
Do not include explanations outside the JSON.

Emails:

{json.dumps(email_data, indent=2)}
"""

    success = False

    for attempt in range(MAX_RETRIES):

        try:

            print(
                f"\nProcessing IDs "
                f"{batch[0]['id']} - {batch[-1]['id']} "
                f"(Attempt {attempt + 1})"
            )

            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )

            predictions = json.loads(response.text)

            # Save predictions
            for prediction in predictions:

                # Avoid duplicates
                if prediction["id"] not in processed_ids:

                    results.append(prediction)
                    processed_ids.add(prediction["id"])

            # Save immediately after successful batch
            with open(RESULTS_PATH, "w", encoding="utf-8") as file:
                json.dump(results, file, indent=2)

            print(
                f"Batch successful. "
                f"Total saved: {len(results)}"
            )

            success = True
            break

        except Exception as e:

            print(f"Error: {e}")

            if attempt < MAX_RETRIES - 1:

                wait_time = 30 * (attempt + 1)

                print(
                    f"Waiting {wait_time} seconds "
                    f"before retry..."
                )

                time.sleep(wait_time)

    if not success:

        print(
            f"Skipping batch "
            f"{batch[0]['id']}-{batch[-1]['id']} "
            f"for now."
        )

    # Delay before next batch
    time.sleep(10)

# -----------------------------
# CALCULATE RESULTS
# -----------------------------

important_correct = 0
category_correct = 0
action_correct = 0
false_negatives = 0
evaluated = 0

# Create lookup table
email_lookup = {
    email["id"]: email
    for email in emails
}

for prediction in results:

    email_id = prediction["id"]

    if email_id not in email_lookup:
        continue

    expected = email_lookup[email_id]["expected"]

    evaluated += 1

    # Importance
    if prediction["important"] == expected["important"]:
        important_correct += 1

    # False negatives
    if expected["important"] and not prediction["important"]:
        false_negatives += 1

    # Category
    if prediction["category"].lower() == expected["category"].lower():
        category_correct += 1

    # Action
    if prediction["action_required"] == expected["action_required"]:
        action_correct += 1

# -----------------------------
# FINAL REPORT
# -----------------------------

print("\n========== GEMINI BENCHMARK ==========")

print(f"Successfully processed: {evaluated}/{len(emails)}")

if evaluated > 0:

    print(
        f"Importance Accuracy: "
        f"{important_correct}/{evaluated} "
        f"({important_correct / evaluated * 100:.2f}%)"
    )

    print(
        f"Category Accuracy: "
        f"{category_correct}/{evaluated} "
        f"({category_correct / evaluated * 100:.2f}%)"
    )

    print(
        f"Action Accuracy: "
        f"{action_correct}/{evaluated} "
        f"({action_correct / evaluated * 100:.2f}%)"
    )

    print(f"False Negatives: {false_negatives}")
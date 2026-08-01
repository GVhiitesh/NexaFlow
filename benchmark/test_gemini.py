import os
import json
from dotenv import load_dotenv
from google import genai

# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Connect to Gemini
client = genai.Client(api_key=api_key)

prompt = """
Analyze the following email.

Sender: placements@vit.ac.in
Subject: Microsoft Internship Applications Open
Body: Microsoft internship applications are now open.
Interested students must apply before July 25, 2026.

Return ONLY valid JSON in exactly this structure:

{
  "important": true,
  "importance_score": 95,
  "category": "internship",
  "summary": "Short summary here",
  "action_required": true,
  "action": "Required action here",
  "deadline": "2026-07-25",
  "reason": "Short reason here"
}

Do not include markdown or any text outside the JSON.
"""

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents=prompt
)

# Convert AI response into Python dictionary
result = json.loads(response.text)

print("Gemini JSON response:")
print(json.dumps(result, indent=2))
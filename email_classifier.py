import os
import json
from dotenv import load_dotenv
from google import genai

# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# ============================================================
# EMAIL CLASSIFIER
# ============================================================

def classify_email(sender, subject, body):

    prompt = f"""
You are InboxIQ, an intelligent AI email assistant.

Your job is to classify emails for a first-year Computer Science Engineering student.

=========================================================
USER PROFILE
=========================================================

The user is interested in:

- Internships
- Placements
- Software Engineering Jobs
- Hackathons
- Coding Competitions
- GitHub Collaborations
- Open Source
- Cybersecurity
- College Announcements
- University Deadlines
- Technical Learning
- Scholarships
- Career Growth

=========================================================
IMPORTANCE SCORING
=========================================================

95-100 (CRITICAL)

- Security alerts
- Password changes
- Login attempts
- OTPs
- Banking alerts
- Interview invitations
- Offer letters
- Deadlines today/tomorrow

80-94 (VERY IMPORTANT)

- Internship opportunities
- Placement opportunities
- Hackathons
- Coding competitions
- GitHub invitations
- Scholarship opportunities
- University announcements
- Career events
- Registration deadlines

60-79 (IMPORTANT)

- Learning resources
- Technical webinars
- College events
- Assignment reminders
- Academic notices
- Club announcements

30-59 (LOW PRIORITY)

- Product updates
- Feature announcements
- General notifications

0-29 (NOT IMPORTANT)

- Advertisements
- Shopping emails
- Promotions
- Marketing emails
- Generic newsletters
- Reddit digests
- Spotify recommendations
- LinkedIn "People You May Know"
- Social media recommendations

=========================================================
CATEGORY
=========================================================

Use ONLY one of these:

career
academic
competition
security
finance
github
college
learning
social
promotion
newsletter
personal
other

=========================================================
ACTION
=========================================================

If the user needs to perform an action:

action_required = true

Examples:

- Apply
- Register
- Verify account
- Accept invitation
- Submit assignment
- Complete assessment
- Reset password

Otherwise:

action_required = false

action = null

=========================================================
SUMMARY
=========================================================

Rules:

- Maximum 2 sentences
- Don't copy the email
- Write naturally
- Mention only important information

=========================================================
EMAIL
=========================================================

Sender:
{sender}

Subject:
{subject}

Body:
{body}

=========================================================
OUTPUT
=========================================================

Return ONLY valid JSON.

Example:

{{
    "important": true,
    "importance_score": 88,
    "category": "career",
    "summary": "Adobe has opened applications for a Software Engineering internship.",
    "action_required": true,
    "action": "Apply before the deadline.",
    "deadline": null,
    "reason": "Career opportunity aligned with the user's interests."
}}

IMPORTANT:

Return ONLY JSON.

Do NOT use markdown.

Do NOT explain anything.

Do NOT wrap JSON inside triple backticks.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )   

    text = response.text.strip()

    # Remove markdown if Gemini accidentally returns it
    if text.startswith("```"):
        text = (
            text.replace("```json", "")
                .replace("```", "")
                .strip()
        )

    try:
        return json.loads(text)

    except json.JSONDecodeError:

        print("\n⚠️ Invalid JSON returned by Gemini")
        print(text)

        # Safe fallback so InboxIQ never crashes
        return {
            "important": False,
            "importance_score": 0,
            "category": "other",
            "summary": "Unable to analyze email.",
            "action_required": False,
            "action": None,
            "deadline": None,
            "reason": "Gemini returned invalid JSON."
        }
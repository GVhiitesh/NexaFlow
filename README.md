# NexaFlow

NexaFlow is an AI-powered email intelligence system that monitors Gmail, analyzes incoming emails using Google's Gemini AI, and sends WhatsApp notifications for emails that require immediate attention.

The goal of this project is to reduce notification overload by identifying important emails, generating concise summaries, extracting deadlines and required actions, and notifying the user only when necessary.

---

## Features

- Monitors Gmail for new emails
- Cleans HTML email content for better analysis
- Uses Gemini AI to classify email importance
- Generates short summaries of emails
- Extracts deadlines and action items
- Filters out low-priority emails before sending them to the AI
- Sends WhatsApp notifications for important emails
- Prevents duplicate notifications
- Runs continuously in the background

---

## How It Works

```
New Email
    |
    v
Gmail API
    |
    v
Email Cleaning
    |
    v
Pre-filter
    |
    v
Gemini AI
    |
    +-------------------------+
    |                         |
Importance Score        Email Summary
    |                         |
Action Extraction     Deadline Detection
    |                         |
    +------------+------------+
                 |
                 v
      Notification Decision
                 |
                 v
      WhatsApp Notification
```

---

## Project Structure

```text
NexaFlow/
│
├── main.py
├── gmail_reader.py
├── gmail_service.py
├── email_classifier.py
├── email_cleaner.py
├── pre_filter.py
├── notification_filter.py
├── processed_emails.py
├── whatsapp_sender.py
├── test_whatsapp.py
├── requirements.txt
├── README.md
│
├── data/
├── docs/
└── utils/
```

---

## Technologies Used

- Python
- Google Gemini API
- Gmail API
- WhatsApp Cloud API
- Google OAuth 2.0
- BeautifulSoup
- python-dotenv
- Git
- GitHub

---

## Installation

Clone the repository:

```bash
git clone https://github.com/GVhiitesh/NexaFlow.git
```

Move into the project directory:

```bash
cd NexaFlow
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Create a `.env` file and add your API credentials.

```env
GEMINI_API_KEY=YOUR_API_KEY
WHATSAPP_ACCESS_TOKEN=YOUR_ACCESS_TOKEN
WHATSAPP_PHONE_NUMBER_ID=YOUR_PHONE_NUMBER_ID
WHATSAPP_RECIPIENT=YOUR_PHONE_NUMBER
```

Place your Google OAuth credentials file in the project directory.

```
credentials.json
```

Run the project:

```bash
python main.py
```

---

## Screenshots

### Email Analysis

(Add screenshot)

### WhatsApp Notification

(Add screenshot)

---

## Current Status

The backend is fully functional and supports Gmail monitoring, AI-based email classification, and WhatsApp notifications.

The dashboard interface has been designed and will be integrated in a future version.

---

## Future Improvements

- Dashboard with analytics
- Email history
- Search and filtering
- Calendar integration
- Personalized notification preferences
- Multiple notification channels
- Cloud deployment

---

## Author

G.V. Hiitesh

GitHub: https://github.com/GVhiitesh

---

## License

This project is licensed under the MIT License.

import os
import time
try:
    from sendgrid import SendGridAPIClient
except ImportError:               # local dev without SendGrid wheel
    SendGridAPIClient = None
try:
    from sendgrid.helpers.mail import Mail
except ImportError:               # local dev without SendGrid wheel
    Mail = None
from functools import lru_cache
try:
    from google.cloud import firestore
except ImportError:               # local dev without Firestore wheel
    firestore = None
import os

# Use the actual API key for authentication
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

DLQ_COLLECTION = "emails_dlq"

@lru_cache
def get_firestore_client():
    try:
        return firestore.Client()
    except Exception:
        # Allow local runs with emulator only
        if os.getenv("FIRESTORE_EMULATOR_HOST"):
            return firestore.Client(project="test-project")
        raise


def send_email(to, subject, html, text, max_retries=3):
    message = Mail(
        from_email="no-reply@emaillm.com",
        to_emails=to,
        subject=subject,
        html_content=html,
        plain_text_content=text,
    )
    attempt = 0
    while attempt < max_retries:
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            if response.status_code >= 200 and response.status_code < 300:
                return response
            else:
                raise Exception(f"SendGrid error: {response.status_code}")
        except Exception as e:
            attempt += 1
            if attempt == max_retries:
                # Move to DLQ
                get_firestore_client().collection(DLQ_COLLECTION).add({
                    "to": to,
                    "subject": subject,
                    "html": html,
                    "text": text,
                    "error": str(e),
                    "timestamp": firestore.SERVER_TIMESTAMP,
                })
                raise
            time.sleep(2 ** attempt)  # exponential backoff

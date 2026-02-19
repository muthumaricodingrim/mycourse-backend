import os
import base64
import logging
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service():
    """Builds and returns the Gmail API service."""
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        logger.error("GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, or GMAIL_REFRESH_TOKEN missing in .env")
        return None

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )

    if creds.expired:
        try:
            creds.refresh(Request())
        except Exception as e:
            logger.error(f"Failed to refresh Gmail token: {e}")
            return None

    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Failed to build Gmail service: {e}")
        return None

def send_email(to_email: str, subject: str, body: str) -> None:
    """Sends an email using the Gmail API."""
    sender = os.getenv("GMAIL_SENDER")
    if not sender:
        logger.error("GMAIL_SENDER missing in .env")
        return

    service = get_gmail_service()
    if not service:
        logger.error("Gmail service not available. Email not sent.")
        return

    try:
        message = MIMEText(body)
        message["to"] = to_email
        message["from"] = sender
        message["subject"] = subject

        # Encode the message safely
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        
        send_request = service.users().messages().send(userId="me", body={"raw": raw_message})
        send_request.execute()
        
        logger.info(f"Email sent successfully to {to_email} using Gmail API")
    except HttpError as error:
        logger.error(f"An error occurred while sending email via Gmail API: {error}")
    except Exception as e:
        logger.info(f"Unexpected error: {e}")

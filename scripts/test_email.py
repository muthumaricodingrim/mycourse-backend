import os
import sys
from dotenv import load_dotenv

# Add the backend directory to sys.path to import our service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.email_service import send_email

def test_send():
    load_dotenv()
    
    recipient = input("Enter recipient email for test: ")
    subject = "Test Email from Gmail API"
    body = "This is a test email to verify the Gmail API integration. If you receive this, your setup is working!"
    
    print(f"Attempting to send email to {recipient}...")
    try:
        send_email(recipient, subject, body)
        print("✅ SUCCESS: Email sent successfully!")
    except Exception as e:
        print(f"❌ FAILURE: {e}")

if __name__ == "__main__":
    test_send()

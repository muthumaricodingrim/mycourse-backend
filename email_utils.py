
import os
import logging
from aiosmtplib import send
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_confirmation_email(recipient_email, first_name, education_level, experience_level, registration_id, course_name):
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM]):
        logger.error("SMTP configuration is missing. Email not sent.")
        return False

    subject = "Registration Confirmed – Payment Pending"
    
    body = f"""Hello {first_name},

Your registration has been successfully received.

Education Level: {education_level}
Experience Level: {experience_level}
Course: {course_name}
Registration ID: {registration_id}

Your payment status: Pending

Please proceed to complete your payment to confirm your enrollment.

Thank you.
"""

    msg = MIMEMultipart()
    msg["From"] = SMTP_FROM
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        await send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            use_tls=(SMTP_PORT == 465),
            start_tls=(SMTP_PORT == 587),
        )
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {e}")
        return False

async def send_payment_success_email(recipient_email, first_name, course_name, batch, amount, transaction_id):
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM]):
        logger.error("SMTP configuration is missing. Payment success email not sent.")
        return False

    subject = "Payment Successful – Enrollment Confirmed"
    
    body = f"""Hello {first_name},

Congratulations! Your payment of INR {amount} has been successfully processed.

Course: {course_name}
Batch: {batch}
Transaction ID: {transaction_id}

Your enrollment is now confirmed. Welcome to the course!

Thank you,
Team CodingRim
"""

    msg = MIMEMultipart()
    msg["From"] = SMTP_FROM
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        await send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            use_tls=(SMTP_PORT == 465),
            start_tls=(SMTP_PORT == 587),
        )
        logger.info(f"Payment success email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send payment success email to {recipient_email}: {e}")
        return False

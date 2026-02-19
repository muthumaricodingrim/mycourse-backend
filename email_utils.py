import logging
from services.email_service import send_email

logger = logging.getLogger(__name__)

async def send_confirmation_email(recipient_email, first_name, education_level, experience_level, registration_id, course_name):
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

    try:
        send_email(recipient_email, subject, body)
        logger.info(f"Confirmation email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send confirmation email to {recipient_email}: {e}")
        return False

async def send_payment_success_email(recipient_email, first_name, course_name, batch, amount, transaction_id):
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

    try:
        send_email(recipient_email, subject, body)
        logger.info(f"Payment success email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send payment success email to {recipient_email}: {e}")
        return False

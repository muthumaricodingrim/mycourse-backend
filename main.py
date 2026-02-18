
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import uuid
import logging
import razorpay
from database import init_db, get_db, Enrollment
from email_utils import send_confirmation_email, send_payment_success_email
import phonenumbers
from phonenumbers import NumberParseException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Database
init_db()

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    logger.info("✅ Razorpay client initialized.")
else:
    logger.warning("⚠️ Razorpay keys missing in .env. Payment functionality will fail.")

app = FastAPI()

# Enable CORS to allow requests from the React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EnrollmentRequest(BaseModel):
    firstName: str
    lastName: str
    email: str
    mobile: str
    educationLevel: str
    experienceLevel: str
    courseName: str
    batch: str

class OrderRequest(BaseModel):
    registration_id: str
    amount: int  # in paise

class PaymentVerificationRequest(BaseModel):
    registration_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.post("/enroll")
async def enroll_student(request: EnrollmentRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Endpoint to save Step 1 + Step 2 data and trigger notification.
    """
    # Validate Phone Number
    try:
        # Request mobile should be in E.164 format (e.g., +919876543210)
        parsed_number = phonenumbers.parse(request.mobile, None)
        
        # 1. Global validity check
        if not phonenumbers.is_valid_number(parsed_number):
            raise HTTPException(status_code=400, detail="Enter a valid number")
        
        # 2. Strict India (+91) validation: must be exactly 10 digits
        if phonenumbers.region_code_for_number(parsed_number) == "IN":
            national_number_str = str(parsed_number.national_number)
            if len(national_number_str) != 10:
                raise HTTPException(status_code=400, detail="Enter a valid number")
        
        # 3. Final format check (must match what was parsed)
        formatted_mobile = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        if formatted_mobile != request.mobile:
             # This handles cases where user might have added extra digits that 'parse' ignored
             # but we want to be strict about the exact input matching the canonical format.
             raise HTTPException(status_code=400, detail="Enter a valid number")

    except Exception as e:
        logger.error(f"Phone validation failed: {e}")
        raise HTTPException(status_code=400, detail="Enter a valid number")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail="Phone number validation failed.")

    try:
        # Generate unique registration ID
        reg_id = f"GR-{uuid.uuid4().hex[:8].upper()}"
        
        # Save to database
        db_enrollment = Enrollment(
            registration_id=reg_id,
            first_name=request.firstName,
            last_name=request.lastName,
            email=request.email,
            mobile=request.mobile,
            education_level=request.educationLevel,
            experience_level=request.experienceLevel,
            course_name=request.courseName,
            batch=request.batch,
            payment_status="Pending"
        )
        db.add(db_enrollment)
        db.commit()
        db.refresh(db_enrollment)
        
        logger.info(f"💾 Enrollment saved: {reg_id} for {request.email}")

        # Queue confirmation email
        background_tasks.add_task(
            handle_email_notification,
            db_enrollment.id,
            request.email,
            request.firstName,
            request.educationLevel,
            request.experienceLevel,
            reg_id,
            request.courseName
        )
        
        return {
            "success": True,
            "message": "Registration received. Payment is pending.",
            "registration_id": reg_id,
            "status": "Pending"
        }
    except Exception as e:
        logger.error(f"Error during enrollment: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/create-order")
async def create_order(request: OrderRequest, db: Session = Depends(get_db)):
    """
    Step 3: Create Razorpay Order
    """
    if not client:
        raise HTTPException(status_code=500, detail="Razorpay client not configured.")

    enrollment = db.query(Enrollment).filter(Enrollment.registration_id == request.registration_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found.")

    try:
        # Create Order in Razorpay
        data = {
            "amount": request.amount,
            "currency": "INR",
            "receipt": request.registration_id
        }
        razor_order = client.order.create(data=data)
        
        # Save order ID to database
        enrollment.razorpay_order_id = razor_order['id']
        enrollment.paid_amount = request.amount // 100 # stored in INR
        db.commit()

        return {
            "success": True,
            "order_id": razor_order['id'],
            "amount": request.amount,
            "currency": "INR",
            "key_id": RAZORPAY_KEY_ID
        }
    except Exception as e:
        logger.error(f"Error creating Razorpay order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify-payment")
async def verify_payment(request: PaymentVerificationRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Step 3: Verify Razorpay Signature and Finalize
    """
    if not client:
        raise HTTPException(status_code=500, detail="Razorpay client not configured.")

    enrollment = db.query(Enrollment).filter(Enrollment.registration_id == request.registration_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found.")

    try:
        # Verify Signature
        params_dict = {
            'razorpay_order_id': request.razorpay_order_id,
            'razorpay_payment_id': request.razorpay_payment_id,
            'razorpay_signature': request.razorpay_signature
        }
        client.utility.verify_payment_signature(params_dict)
        
        # Update database
        enrollment.payment_status = "Completed"
        enrollment.razorpay_payment_id = request.razorpay_payment_id
        enrollment.razorpay_signature = request.razorpay_signature
        db.commit()

        logger.info(f"✅ Payment Verified for {request.registration_id}")

        # Send success email as background task
        background_tasks.add_task(
            send_payment_success_email,
            enrollment.email,
            enrollment.first_name,
            enrollment.course_name,
            enrollment.batch,
            enrollment.paid_amount,
            request.razorpay_payment_id
        )

        return {"success": True, "message": "Payment verified and enrollment confirmed."}
    except razorpay.errors.SignatureVerificationError:
        enrollment.payment_status = "Failed"
        db.commit()
        logger.warning(f"❌ Signature Verification Failed for {request.registration_id}")
        return {"success": False, "message": "Invalid payment signature."}
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def handle_email_notification(enrollment_id, email, name, edu, exp, reg_id, course):
    """
    Background worker to send email and update status in DB.
    """
    success = await send_confirmation_email(email, name, edu, exp, reg_id, course)
    
    # Update email_sent_status in database
    db = next(get_db())
    try:
        enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
        if enrollment:
            enrollment.email_sent_status = success
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

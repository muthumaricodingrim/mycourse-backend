
import os
import uuid
import datetime
import logging
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase DATABASE_URL should be in format: 
# postgresql+psycopg2://USER:PASSWORD@HOST:PORT/postgres?sslmode=require
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.warning("DATABASE_URL not set. Falling back to local PostgreSQL.")
    DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/course_reg"

# Production settings for SQLAlchemy
# pooling for postgres on supabase
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"} if "localhost" not in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    registration_id = Column(String, unique=True, index=True, default=lambda: f"GR-{uuid.uuid4().hex[:8].upper()}")
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, index=True)
    mobile = Column(String)
    education_level = Column(String)
    experience_level = Column(String)
    course_name = Column(String)
    batch = Column(String)
    payment_status = Column(String, default="Pending")
    email_sent_status = Column(Boolean, default=False)
    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    razorpay_signature = Column(String, nullable=True)
    paid_amount = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables initialized (if they didn't exist).")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

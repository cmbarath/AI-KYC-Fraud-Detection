import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class KYCApplication(Base):
    __tablename__ = "kyc_applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_number = Column(String(32), unique=True, index=True, nullable=False)
    
    # Synthetic Applicant Details
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    date_of_birth = Column(String(10), nullable=False)  # YYYY-MM-DD
    email = Column(String(128), index=True, nullable=False)
    phone_number = Column(String(32), index=True, nullable=False)
    
    # Synthetic Identity Document Reference
    id_type = Column(String(32), nullable=False)  # DEMO_NATIONAL_ID / DEMO_PASSPORT / DEMO_DRIVERS_LICENSE
    id_number = Column(String(64), index=True, nullable=False)  # Synthetic ID
    id_hash = Column(String(64), index=True, nullable=False)   # SHA-256 for duplicate lookup
    
    # Address details
    address_line = Column(String(256), nullable=False)
    city = Column(String(64), nullable=False)
    state = Column(String(64), nullable=False)
    country = Column(String(64), nullable=False, default="Simulatedland")
    
    # Financial profile
    declared_income = Column(String(32), nullable=True, default="50000")
    employment_type = Column(String(64), nullable=True, default="Salaried")
    
    # Status: SUBMITTED, PENDING_REVIEW, APPROVED, REJECTED, FLAGGED
    status = Column(String(32), default="SUBMITTED", index=True, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    documents = relationship("Document", back_populates="applicant", cascade="all, delete-orphan")
    evaluations = relationship("FraudEvaluation", back_populates="applicant", cascade="all, delete-orphan")
    transactions = relationship("TransactionRecord", back_populates="applicant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="applicant", cascade="all, delete-orphan")

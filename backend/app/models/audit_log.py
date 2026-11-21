import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    applicant_id = Column(String(36), ForeignKey("kyc_applications.id"), nullable=True, index=True)
    
    event_type = Column(String(64), nullable=False)  # e.g., REGISTRATION, OCR_PROCESSED, FRAUD_EVALUATED, STATUS_CHANGE
    actor = Column(String(64), default="SYSTEM")      # SYSTEM, ADMIN, USER
    description = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    applicant = relationship("KYCApplication", back_populates="audit_logs")

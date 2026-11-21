import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    applicant_id = Column(String(36), ForeignKey("kyc_applications.id"), nullable=False, index=True)
    
    document_type = Column(String(32), nullable=False)  # DEMO_ID_FRONT, DEMO_ID_BACK, DEMO_ADDRESS_PROOF
    file_name = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), index=True, nullable=False)  # SHA-256 for tamper/duplication detection
    
    # OCR Extraction Results
    extracted_text = Column(Text, nullable=True)
    extracted_name = Column(String(128), nullable=True)
    extracted_id_number = Column(String(64), nullable=True)
    extracted_dob = Column(String(32), nullable=True)
    
    # Matching Scores (0.0 to 1.0)
    name_match_score = Column(Float, default=0.0)
    id_match_score = Column(Float, default=0.0)
    dob_match_score = Column(Float, default=0.0)
    overall_match_score = Column(Float, default=0.0)
    
    is_verified = Column(Boolean, default=False)
    verification_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    applicant = relationship("KYCApplication", back_populates="documents")

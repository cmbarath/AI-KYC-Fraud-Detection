import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class TransactionRecord(Base):
    __tablename__ = "transaction_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    applicant_id = Column(String(36), ForeignKey("kyc_applications.id"), nullable=False, index=True)
    
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="USD")
    transaction_type = Column(String(32), default="TRANSFER")  # TRANSFER, WITHDRAWAL, PAYMENT
    merchant_category = Column(String(64), default="General")
    
    # Context signals
    ip_address = Column(String(45), nullable=True)
    device_id = Column(String(64), nullable=True)
    location_city = Column(String(64), nullable=True)
    
    # Anomaly Flags
    is_anomalous = Column(Boolean, default=False)
    anomaly_score = Column(Float, default=0.0)
    anomaly_reasons = Column(Text, nullable=True)  # JSON string of triggered anomaly rules
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    applicant = relationship("KYCApplication", back_populates="transactions")

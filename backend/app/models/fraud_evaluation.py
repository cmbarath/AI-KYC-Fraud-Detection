import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class FraudEvaluation(Base):
    __tablename__ = "fraud_evaluations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    applicant_id = Column(String(36), ForeignKey("kyc_applications.id"), nullable=False, index=True)
    
    # ML Scoring
    fraud_probability = Column(Float, nullable=False)   # 0.00 to 1.00
    risk_score = Column(Integer, nullable=False)          # 0 to 100
    risk_tier = Column(String(16), nullable=False)        # LOW, MEDIUM, HIGH, CRITICAL
    
    # Model tracking
    model_name = Column(String(64), default="XGBoost_Classifier")
    model_version = Column(String(32), default="v1.0")
    
    # Explainability Data
    top_risk_factors = Column(Text, nullable=True)        # JSON string of top positive/negative drivers
    shap_summary = Column(Text, nullable=True)            # JSON string of SHAP values
    
    # Automated Action
    automated_decision = Column(String(32), default="MANUAL_REVIEW")  # AUTO_APPROVE, MANUAL_REVIEW, REJECT
    
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    @property
    def model_used(self):
        return self.model_name

    applicant = relationship("KYCApplication", back_populates="evaluations")

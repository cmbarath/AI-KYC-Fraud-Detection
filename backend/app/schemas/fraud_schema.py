from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class FraudEvaluationRequest(BaseModel):
    applicant_id: Optional[str] = None
    age: int = Field(..., ge=18, le=100)
    declared_income: float = Field(..., ge=0)
    id_type: str = Field(default="DEMO_NATIONAL_ID")
    employment_type: str = Field(default="Salaried")
    channel: str = Field(default="Web")
    ocr_name_match_score: float = Field(default=1.0, ge=0.0, le=1.0)
    ocr_id_match_score: float = Field(default=1.0, ge=0.0, le=1.0)
    ocr_dob_match_score: float = Field(default=1.0, ge=0.0, le=1.0)
    tampered_document_flag: int = Field(default=0, ge=0, le=1)
    ip_risk_score: float = Field(default=0.10, ge=0.0, le=1.0)
    device_reuse_count: int = Field(default=1, ge=1)
    disposable_email: int = Field(default=0, ge=0, le=1)
    registration_velocity: int = Field(default=1, ge=1)
    address_mismatch_flag: int = Field(default=0, ge=0, le=1)
    model_name: Optional[str] = Field(default="random_forest")

class SHAPFeatureContribution(BaseModel):
    feature: str
    label: str
    shap_value: float
    transformed_value: float
    direction: str

class FraudEvaluationResponse(BaseModel):
    evaluation_id: Optional[str] = None
    applicant_id: Optional[str] = None
    fraud_probability: float  # Uncalibrated model-estimated class-1 probability
    risk_score: int
    risk_tier: str  # LOW, MEDIUM, HIGH, CRITICAL
    automated_decision: str  # AUTO_APPROVE, MANUAL_REVIEW, REJECT
    model_used: str
    top_risk_drivers: List[SHAPFeatureContribution]
    top_risk_mitigators: List[SHAPFeatureContribution]
    evaluated_at: datetime

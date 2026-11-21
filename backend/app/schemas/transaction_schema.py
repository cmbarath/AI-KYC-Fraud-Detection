from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TransactionCheckRequest(BaseModel):
    applicant_id: Optional[str] = None
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD")
    transaction_type: str = Field(default="TRANSFER")  # TRANSFER, WITHDRAWAL, PAYMENT
    merchant_category: str = Field(default="Retail")
    ip_address: Optional[str] = Field(default="192.168.1.10")
    device_id: Optional[str] = Field(default="dev_mobile_001")
    location_city: Optional[str] = Field(default="Metropolis")
    applicant_declared_income: Optional[float] = Field(default=60000.0)

class TransactionCheckResponse(BaseModel):
    transaction_id: Optional[str] = None
    is_anomalous: bool
    anomaly_score: float  # 0.0 to 1.0
    risk_level: str  # NORMAL, SUSPICIOUS, SEVERE
    anomaly_reasons: List[str]
    timestamp: datetime

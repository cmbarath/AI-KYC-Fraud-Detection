from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class KYCRegistrationRequest(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=64, description="Synthetic applicant first name")
    last_name: str = Field(..., min_length=2, max_length=64, description="Synthetic applicant last name")
    date_of_birth: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="DOB in YYYY-MM-DD")
    email: str = Field(..., min_length=5, max_length=128, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Applicant email address")
    phone_number: str = Field(..., min_length=7, max_length=20, description="Applicant phone number")
    id_type: str = Field(..., description="DEMO_NATIONAL_ID, DEMO_PASSPORT, or DEMO_DRIVERS_LICENSE")
    id_number: str = Field(..., min_length=4, max_length=32, description="Synthetic identity number")
    address_line: str = Field(..., min_length=5, max_length=256)
    city: str = Field(..., min_length=2, max_length=64)
    state: str = Field(..., min_length=2, max_length=64)
    country: str = Field(default="Simulatedland", max_length=64)
    declared_income: Optional[str] = Field(default="50000")
    employment_type: Optional[str] = Field(default="Salaried")
    channel: Optional[str] = Field(default="Web")
    ip_address: Optional[str] = Field(default="127.0.0.1")
    device_id: Optional[str] = Field(default="dev_browser_mock")

class KYCApplicationResponse(BaseModel):
    id: str
    application_number: str
    first_name: str
    last_name: str
    date_of_birth: str
    email: str
    phone_number: str
    id_type: str
    id_number: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ApplicationStatusUpdate(BaseModel):
    status: str = Field(..., description="APPROVED, REJECTED, PENDING_REVIEW, or FLAGGED")
    notes: Optional[str] = Field(default=None)

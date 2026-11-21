import uuid
import hashlib
import random
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.kyc_application import KYCApplication
from backend.app.models.audit_log import AuditLog
from backend.app.schemas.kyc_schema import (
    KYCRegistrationRequest,
    KYCApplicationResponse
)
from backend.app.security import require_application_access

router = APIRouter(
    prefix="/kyc",
    tags=["KYC Registration"],
    dependencies=[Depends(require_application_access)],
)

@router.post("/register", response_model=KYCApplicationResponse, status_code=status.HTTP_201_CREATED)
def register_kyc_application(req: KYCRegistrationRequest, db: Session = Depends(get_db)):
    # Generate unique synthetic application number
    app_num = f"KYC-{datetime.utcnow().year}-{random.randint(10000, 99999)}"

    # Generate SHA-256 hash of synthetic ID number for duplicate detection
    id_hash = hashlib.sha256(req.id_number.strip().upper().encode()).hexdigest()

    new_app = KYCApplication(
        application_number=app_num,
        first_name=req.first_name.strip(),
        last_name=req.last_name.strip(),
        date_of_birth=req.date_of_birth,
        email=req.email.strip().lower(),
        phone_number=req.phone_number.strip(),
        id_type=req.id_type,
        id_number=req.id_number.strip().upper(),
        id_hash=id_hash,
        address_line=req.address_line.strip(),
        city=req.city.strip(),
        state=req.state.strip(),
        country=req.country.strip(),
        declared_income=req.declared_income,
        employment_type=req.employment_type,
        status="SUBMITTED"
    )

    db.add(new_app)
    db.commit()
    db.refresh(new_app)

    # Record initial audit entry
    audit = AuditLog(
        applicant_id=new_app.id,
        event_type="APPLICATION_SUBMITTED",
        actor="APPLICANT_PORTAL",
        description=f"Synthetic KYC registration submitted. App No: {app_num}. ID Type: {req.id_type}.",
        metadata_json=f'{{"ip": "{req.ip_address}", "channel": "{req.channel}"}}'
    )
    db.add(audit)
    db.commit()

    return new_app

@router.get("/{applicant_id}")
def get_application_details(applicant_id: str, db: Session = Depends(get_db)):
    app = db.query(KYCApplication).filter(KYCApplication.id == applicant_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    docs = [
        {
            "id": d.id,
            "document_type": d.document_type,
            "file_name": d.file_name,
            "extracted_name": d.extracted_name,
            "extracted_id_number": d.extracted_id_number,
            "overall_match_score": d.overall_match_score,
            "is_verified": d.is_verified,
            "created_at": d.created_at
        }
        for d in app.documents
    ]

    evals = [
        {
            "id": e.id,
            "risk_score": e.risk_score,
            "risk_tier": e.risk_tier,
            "fraud_probability": e.fraud_probability,
            "model_used": getattr(e, "model_name", "Random_Forest"),
            "automated_decision": e.automated_decision,
            "evaluated_at": e.evaluated_at
        }
        for e in app.evaluations
    ]

    return {
        "applicant": {
            "id": app.id,
            "application_number": app.application_number,
            "first_name": app.first_name,
            "last_name": app.last_name,
            "date_of_birth": app.date_of_birth,
            "email": app.email,
            "phone_number": app.phone_number,
            "id_type": app.id_type,
            "id_number": app.id_number,
            "address": f"{app.address_line}, {app.city}, {app.state}, {app.country}",
            "declared_income": app.declared_income,
            "status": app.status,
            "created_at": app.created_at
        },
        "documents": docs,
        "evaluations": evals
    }

@router.get("/lookup/{app_number}")
def lookup_by_number(app_number: str, db: Session = Depends(get_db)):
    app = db.query(KYCApplication).filter(KYCApplication.application_number == app_number.strip()).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application number not found")
    return get_application_details(app.id, db)

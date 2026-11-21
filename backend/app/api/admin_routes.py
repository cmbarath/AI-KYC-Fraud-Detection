import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models.kyc_application import KYCApplication
from backend.app.models.fraud_evaluation import FraudEvaluation
from backend.app.models.transaction import TransactionRecord
from backend.app.models.audit_log import AuditLog
from backend.app.schemas.kyc_schema import ApplicationStatusUpdate
from backend.app.security import require_admin_access

router = APIRouter(
    prefix="/admin",
    tags=["Admin Operations & Analytics"],
    dependencies=[Depends(require_admin_access)],
)

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    total_apps = db.query(KYCApplication).count()
    approved = db.query(KYCApplication).filter(KYCApplication.status == "APPROVED").count()
    rejected = db.query(KYCApplication).filter(KYCApplication.status == "REJECTED").count()
    flagged = db.query(KYCApplication).filter(KYCApplication.status == "FLAGGED").count()
    pending = db.query(KYCApplication).filter(KYCApplication.status.in_(["SUBMITTED", "PENDING_REVIEW"])).count()

    # Risk Tier Breakdown
    low_risk = db.query(FraudEvaluation).filter(FraudEvaluation.risk_tier == "LOW").count()
    med_risk = db.query(FraudEvaluation).filter(FraudEvaluation.risk_tier == "MEDIUM").count()
    high_risk = db.query(FraudEvaluation).filter(FraudEvaluation.risk_tier == "HIGH").count()
    crit_risk = db.query(FraudEvaluation).filter(FraudEvaluation.risk_tier == "CRITICAL").count()

    # Transaction Anomalies
    total_tx = db.query(TransactionRecord).count()
    anomalous_tx = db.query(TransactionRecord).filter(TransactionRecord.is_anomalous == True).count()

    fraud_rate = round(((high_risk + crit_risk) / max(1, (low_risk + med_risk + high_risk + crit_risk))) * 100, 1)

    return {
        "kpis": {
            "total_applications": total_apps,
            "approved_applications": approved,
            "rejected_applications": rejected,
            "flagged_applications": flagged,
            "pending_review": pending,
            "total_transactions": total_tx,
            "anomalous_transactions": anomalous_tx,
            "estimated_fraud_rate_pct": fraud_rate
        },
        "risk_tier_counts": {
            "LOW": low_risk,
            "MEDIUM": med_risk,
            "HIGH": high_risk,
            "CRITICAL": crit_risk
        }
    }

@router.get("/applications")
def list_applications(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(KYCApplication)
    
    if status and status != "ALL":
        query = query.filter(KYCApplication.status == status)

    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            (KYCApplication.application_number.ilike(search_fmt)) |
            (KYCApplication.first_name.ilike(search_fmt)) |
            (KYCApplication.last_name.ilike(search_fmt)) |
            (KYCApplication.email.ilike(search_fmt)) |
            (KYCApplication.id_number.ilike(search_fmt))
        )

    total = query.count()
    apps = query.order_by(desc(KYCApplication.created_at)).offset(offset).limit(limit).all()

    results = []
    for app in apps:
        latest_eval = db.query(FraudEvaluation).filter(FraudEvaluation.applicant_id == app.id).order_by(desc(FraudEvaluation.evaluated_at)).first()
        results.append({
            "id": app.id,
            "application_number": app.application_number,
            "name": f"{app.first_name} {app.last_name}",
            "email": app.email,
            "phone_number": app.phone_number,
            "id_type": app.id_type,
            "id_number": app.id_number,
            "status": app.status,
            "risk_score": latest_eval.risk_score if latest_eval else None,
            "risk_tier": latest_eval.risk_tier if latest_eval else "UNSCORED",
            "created_at": app.created_at.strftime("%Y-%m-%d %H:%M")
        })

    return {"total": total, "applications": results}

@router.patch("/applications/{applicant_id}/status")
def update_application_status(
    applicant_id: str,
    update: ApplicationStatusUpdate,
    db: Session = Depends(get_db)
):
    app = db.query(KYCApplication).filter(KYCApplication.id == applicant_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    old_status = app.status
    app.status = update.status
    app.notes = update.notes
    app.updated_at = datetime.utcnow()

    # Log audit trail
    audit = AuditLog(
        applicant_id=applicant_id,
        event_type="STATUS_OVERRIDE",
        actor="ADMIN_REVIEWER",
        description=f"Status changed from '{old_status}' to '{update.status}'. Notes: {update.notes or 'None'}.",
        metadata_json=f'{{"old_status": "{old_status}", "new_status": "{update.status}"}}'
    )
    db.add(audit)
    db.commit()
    db.refresh(app)

    return {"message": "Status updated successfully", "new_status": app.status}

@router.get("/audit-logs/{applicant_id}")
def get_applicant_audit_logs(applicant_id: str, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).filter(AuditLog.applicant_id == applicant_id).order_by(desc(AuditLog.created_at)).all()
    return [
        {
            "id": log.id,
            "event_type": log.event_type,
            "actor": log.actor,
            "description": log.description,
            "metadata": json.loads(log.metadata_json) if log.metadata_json else {},
            "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for log in logs
    ]

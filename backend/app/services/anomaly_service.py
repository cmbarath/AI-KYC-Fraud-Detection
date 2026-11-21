from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.schemas.transaction_schema import TransactionCheckRequest, TransactionCheckResponse
from backend.app.models.transaction import TransactionRecord
from backend.app.models.audit_log import AuditLog
import json

HIGH_RISK_MERCHANTS = ["crypto_exchange", "offshore_remittance", "casino_gaming", "high_value_luxury"]

class AnomalyService:
    @staticmethod
    def detect_transaction_anomalies(db: Session, req: TransactionCheckRequest) -> TransactionCheckResponse:
        anomaly_reasons: List[str] = []
        score = 0.0

        monthly_income = (req.applicant_declared_income or 60000.0) / 12.0

        # Rule 1: Extreme Transaction Amount relative to declared income
        if req.amount > (monthly_income * 3.0):
            score += 0.45
            anomaly_reasons.append(
                f"Transaction amount (${req.amount:,.2f}) exceeds 300% of estimated monthly income (${monthly_income:,.2f})."
            )
        elif req.amount > (monthly_income * 1.5):
            score += 0.25
            anomaly_reasons.append(
                f"Elevated amount (${req.amount:,.2f}) significantly surpasses typical monthly threshold."
            )

        # Rule 2: Round number withdrawal pattern (common structuring indicator)
        if req.amount >= 5000 and req.amount % 1000 == 0:
            score += 0.20
            anomaly_reasons.append(f"Structured round-sum transaction detected (${req.amount:,.2f}).")

        # Rule 3: High Risk Merchant Category
        if req.merchant_category.lower().replace(" ", "_") in HIGH_RISK_MERCHANTS:
            score += 0.25
            anomaly_reasons.append(f"High-risk merchant industry category: '{req.merchant_category}'.")

        # Rule 4: International / Untrusted IP
        if req.ip_address and (req.ip_address.startswith("10.") or req.ip_address.startswith("192.168.")):
            # Local private range
            pass
        elif req.location_city and req.location_city.lower() in ["unknown", "proxy_node", "tor_exit"]:
            score += 0.35
            anomaly_reasons.append("Connection originating from high-risk or masked proxy network.")

        final_score = min(1.0, round(score, 2))
        is_anomalous = final_score >= 0.40

        if final_score >= 0.70:
            risk_level = "SEVERE"
        elif final_score >= 0.40:
            risk_level = "SUSPICIOUS"
        else:
            risk_level = "NORMAL"

        tx_record = None
        if req.applicant_id:
            tx_record = TransactionRecord(
                applicant_id=req.applicant_id,
                amount=req.amount,
                currency=req.currency,
                transaction_type=req.transaction_type,
                merchant_category=req.merchant_category,
                ip_address=req.ip_address,
                device_id=req.device_id,
                location_city=req.location_city,
                is_anomalous=is_anomalous,
                anomaly_score=final_score,
                anomaly_reasons=json.dumps(anomaly_reasons),
                timestamp=datetime.utcnow()
            )
            db.add(tx_record)

            if is_anomalous:
                audit = AuditLog(
                    applicant_id=req.applicant_id,
                    event_type="TRANSACTION_ANOMALY_TRIGGERED",
                    actor="SYSTEM_ANOMALY_ENGINE",
                    description=f"Transaction ${req.amount:,.2f} flagged as {risk_level} (Score: {final_score}). Reasons: {'; '.join(anomaly_reasons)}",
                    metadata_json=json.dumps({"amount": req.amount, "score": final_score, "reasons": anomaly_reasons})
                )
                db.add(audit)

            db.commit()
            if tx_record:
                db.refresh(tx_record)

        return TransactionCheckResponse(
            transaction_id=tx_record.id if tx_record else None,
            is_anomalous=is_anomalous,
            anomaly_score=final_score,
            risk_level=risk_level,
            anomaly_reasons=anomaly_reasons,
            timestamp=datetime.utcnow()
        )

anomaly_service = AnomalyService()

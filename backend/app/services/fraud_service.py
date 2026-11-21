import os
import json
import joblib
import hashlib
from datetime import datetime
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.kyc_application import KYCApplication
from backend.app.models.fraud_evaluation import FraudEvaluation
from backend.app.models.audit_log import AuditLog
from backend.app.schemas.fraud_schema import FraudEvaluationRequest, FraudEvaluationResponse
from ml_engine.src.data_preprocessor import KYCDataPreprocessor
from ml_engine.src.explainer import FraudExplainer

class FraudService:
    def __init__(self):
        self.models = {}
        self.preprocessor = None
        self.explainer = None
        self._load_models()

    def _load_models(self):
        model_dir = settings.MODEL_DIR
        preprocessor_path = os.path.join(model_dir, "preprocessor.joblib")
        if os.path.exists(preprocessor_path):
            self.preprocessor = KYCDataPreprocessor.load(preprocessor_path)

        for name in ["random_forest", "xgboost", "logistic_regression"]:
            path = os.path.join(model_dir, f"{name}_model.joblib")
            if os.path.exists(path):
                self.models[name] = joblib.load(path)

        # Default explainer using random_forest or xgboost
        preferred = "random_forest" if "random_forest" in self.models else "xgboost"
        if preferred in self.models:
            self.explainer = FraudExplainer(model_name=preferred)

    def calculate_duplicate_counts(
        self,
        db: Session,
        applicant_id: str,
        id_number: str,
        phone: str,
        email: str
    ) -> Tuple[int, int, int]:
        """
        Scans SQLite database to count existing occurrences of identity identifiers.
        Excludes the current application from each count.
        """
        id_hash = hashlib.sha256(id_number.strip().upper().encode()).hexdigest()
        id_query = db.query(KYCApplication).filter(KYCApplication.id_hash == id_hash)
        phone_query = db.query(KYCApplication).filter(KYCApplication.phone_number == phone.strip())
        email_query = db.query(KYCApplication).filter(KYCApplication.email == email.strip().lower())

        if applicant_id:
            id_query = id_query.filter(KYCApplication.id != applicant_id)
            phone_query = phone_query.filter(KYCApplication.id != applicant_id)
            email_query = email_query.filter(KYCApplication.id != applicant_id)

        dup_id_count = id_query.count()
        dup_phone_count = phone_query.count()
        dup_email_count = email_query.count()
        return dup_id_count, dup_phone_count, dup_email_count

    def evaluate_risk(self, db: Session, req: FraudEvaluationRequest) -> FraudEvaluationResponse:
        requested_model = req.model_name.lower() if req.model_name else "random_forest"
        model_key = requested_model if requested_model in self.models else "random_forest"
        model = self.models.get(model_key)
        
        if not model or not self.preprocessor:
            self._load_models()
            model_key = model_key if model_key in self.models else "random_forest"
            model = self.models.get(model_key) or next(iter(self.models.values()), None)

        # If applicant_id exists, lookup database for real duplicate identity signals
        dup_id = 0
        dup_phone = 0
        dup_email = 0
        if req.applicant_id:
            applicant = db.query(KYCApplication).filter(KYCApplication.id == req.applicant_id).first()
            if applicant:
                dup_id, dup_phone, dup_email = self.calculate_duplicate_counts(
                    db,
                    applicant.id,
                    applicant.id_number,
                    applicant.phone_number,
                    applicant.email
                )

        # Build feature dictionary
        features = {
            "age": req.age,
            "declared_income": req.declared_income,
            "id_type": req.id_type,
            "employment_type": req.employment_type,
            "channel": req.channel,
            "ocr_name_match_score": req.ocr_name_match_score,
            "ocr_id_match_score": req.ocr_id_match_score,
            "ocr_dob_match_score": req.ocr_dob_match_score,
            "tampered_document_flag": req.tampered_document_flag,
            "duplicate_id_count": dup_id,
            "duplicate_phone_count": dup_phone,
            "duplicate_email_count": dup_email,
            "ip_risk_score": req.ip_risk_score,
            "device_reuse_count": req.device_reuse_count,
            "disposable_email": req.disposable_email,
            "registration_velocity": req.registration_velocity,
            "address_mismatch_flag": req.address_mismatch_flag
        }

        # Transform and Predict
        import pandas as pd
        df_single = pd.DataFrame([features])
        X_trans = self.preprocessor.transform(df_single)
        
        # Display estimate: probability is an uncalibrated model estimate,
        # not a calibrated fraud probability or legal KYC determination.
        prob = float(model.predict_proba(X_trans)[0][1])
        risk_score = int(round(prob * 100))

        # Risk Classification Tiers
        if risk_score <= settings.RISK_THRESHOLD_LOW:
            risk_tier = "LOW"
            decision = "AUTO_APPROVE"
        elif risk_score <= settings.RISK_THRESHOLD_MEDIUM:
            risk_tier = "MEDIUM"
            decision = "MANUAL_REVIEW"
        elif risk_score <= settings.RISK_THRESHOLD_HIGH:
            risk_tier = "HIGH"
            decision = "MANUAL_REVIEW"
        else:
            risk_tier = "CRITICAL"
            decision = "REJECT"

        # Generate SHAP attribution with the same model used for prediction.
        try:
            prediction_explainer = FraudExplainer(model_name=model_key)
        except Exception:
            prediction_explainer = self.explainer
        explanation = prediction_explainer.explain_instance(features, top_n=4) if prediction_explainer else {
            "top_risk_drivers": [],
            "top_risk_mitigators": []
        }

        top_drivers = explanation.get("top_risk_drivers", [])
        top_mitigators = explanation.get("top_risk_mitigators", [])

        # Persist evaluation record if linked to applicant
        eval_record = None
        if req.applicant_id:
            eval_record = FraudEvaluation(
                applicant_id=req.applicant_id,
                fraud_probability=prob,
                risk_score=risk_score,
                risk_tier=risk_tier,
                model_name=model_key,
                automated_decision=decision,
                top_risk_factors=json.dumps(top_drivers),
                shap_summary=json.dumps(explanation.get("all_contributions", []))
            )
            db.add(eval_record)
            
            # Log audit event
            audit = AuditLog(
                applicant_id=req.applicant_id,
                event_type="FRAUD_EVALUATED",
                actor="SYSTEM_ML",
                description=f"Model {model_key} calculated Risk Score: {risk_score}/100 ({risk_tier}). Automated Decision: {decision}.",
                metadata_json=json.dumps({"risk_score": risk_score, "tier": risk_tier, "decision": decision})
            )
            db.add(audit)
            db.commit()
            db.refresh(eval_record)

        return FraudEvaluationResponse(
            evaluation_id=eval_record.id if eval_record else None,
            applicant_id=req.applicant_id,
            fraud_probability=round(prob, 4),
            risk_score=risk_score,
            risk_tier=risk_tier,
            automated_decision=decision,
            model_used=model_key,
            top_risk_drivers=top_drivers,
            top_risk_mitigators=top_mitigators,
            evaluated_at=datetime.utcnow()
        )

fraud_service = FraudService()

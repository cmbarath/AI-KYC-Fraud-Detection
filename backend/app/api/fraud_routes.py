import os
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.fraud_schema import FraudEvaluationRequest, FraudEvaluationResponse
from backend.app.services.fraud_service import fraud_service
from backend.app.security import require_application_access

router = APIRouter(
    prefix="/fraud",
    tags=["Fraud Detection & XAI"],
    dependencies=[Depends(require_application_access)],
)

@router.post("/evaluate", response_model=FraudEvaluationResponse)
def evaluate_fraud_risk(req: FraudEvaluationRequest, db: Session = Depends(get_db)):
    try:
        response = fraud_service.evaluate_risk(db, req)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fraud Evaluation Engine Error: {str(e)}")

@router.get("/models")
def get_model_benchmarks():
    metrics_path = os.path.join(settings.MODEL_DIR, "model_metrics.json")
    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="Model metrics benchmark file not found.")
    
    with open(metrics_path, "r") as f:
        data = json.load(f)
    return data

@router.get("/feature-importance")
def get_feature_importance():
    if not fraud_service.explainer:
        raise HTTPException(status_code=503, detail="Explainer engine not loaded.")
    return {"feature_importance": fraud_service.explainer.get_global_feature_importance()}

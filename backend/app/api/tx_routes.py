from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.transaction_schema import TransactionCheckRequest, TransactionCheckResponse
from backend.app.services.anomaly_service import anomaly_service
from backend.app.security import require_application_access

router = APIRouter(
    prefix="/transactions",
    tags=["Transaction Anomaly Detection"],
    dependencies=[Depends(require_application_access)],
)

@router.post("/check", response_model=TransactionCheckResponse)
def check_transaction(req: TransactionCheckRequest, db: Session = Depends(get_db)):
    try:
        response = anomaly_service.detect_transaction_anomalies(db, req)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transaction Anomaly Engine Error: {str(e)}")

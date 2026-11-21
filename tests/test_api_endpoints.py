import os
import sys
import uuid

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from backend.app.config import settings
from backend.app.database import Base, get_db
from backend.app.main import app

import backend.app.models

settings.APP_API_TOKEN = "test-application-access-token"
settings.ADMIN_ACCESS_TOKEN = "test-separate-administrator-token"

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=test_engine)
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("Health check endpoint test: PASSED")

def test_kyc_registration_and_evaluation():
    # 1. Register synthetic applicant
    unique_id = uuid.uuid4().hex[:12]
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": "1992-06-15",
        "email": f"test_user_{unique_id}@example.test",
        "phone_number": f"+1555{unique_id[:7]}",
        "id_type": "DEMO_NATIONAL_ID",
        "id_number": f"SIM-{unique_id.upper()}",
        "address_line": "456 Innovation Way",
        "city": "Cyber City",
        "state": "Digital State",
        "country": "Simulatedland",
        "declared_income": "65000",
        "employment_type": "Salaried"
    }

    app_headers = {"X-API-Token": settings.APP_API_TOKEN}
    admin_headers = {"X-Admin-Access-Token": settings.ADMIN_ACCESS_TOKEN}
    reg_resp = client.post(
        "/api/v1/kyc/register",
        json=payload,
        headers=app_headers,
    )
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    app_id = data["id"]
    print(f"KYC registration test: PASSED (Created ID: {app_id})")

    # 2. Evaluate fraud risk
    eval_payload = {
        "applicant_id": app_id,
        "age": 32,
        "declared_income": 65000.0,
        "id_type": "DEMO_NATIONAL_ID",
        "employment_type": "Salaried",
        "channel": "Web",
        "ocr_name_match_score": 0.98,
        "ocr_id_match_score": 1.0,
        "ocr_dob_match_score": 1.0,
        "tampered_document_flag": 0,
        "ip_risk_score": 0.12,
        "device_reuse_count": 1,
        "disposable_email": 0,
        "registration_velocity": 1,
        "address_mismatch_flag": 0
    }

    eval_resp = client.post(
        "/api/v1/fraud/evaluate",
        json=eval_payload,
        headers=app_headers,
    )
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert "risk_score" in eval_data
    assert "top_risk_drivers" in eval_data
    print(f"Fraud evaluation test: PASSED (Score: {eval_data['risk_score']}/100, Tier: {eval_data['risk_tier']})")

    # 3. Check transaction anomaly
    tx_payload = {
        "applicant_id": app_id,
        "amount": 2500.0,
        "currency": "USD",
        "transaction_type": "TRANSFER",
        "merchant_category": "Retail",
        "applicant_declared_income": 65000.0
    }
    tx_resp = client.post(
        "/api/v1/transactions/check",
        json=tx_payload,
        headers=app_headers,
    )
    assert tx_resp.status_code == 200
    tx_data = tx_resp.json()
    assert "is_anomalous" in tx_data
    print(f"Transaction anomaly test: PASSED (Anomalous: {tx_data['is_anomalous']})")

    # 4. Check admin metrics
    admin_resp = client.get("/api/v1/admin/metrics", headers=admin_headers)
    assert admin_resp.status_code == 200
    metrics_data = admin_resp.json()
    assert metrics_data["kpis"]["total_applications"] >= 1
    print("Admin metrics test: PASSED")

if __name__ == "__main__":
    test_health()
    test_kyc_registration_and_evaluation()

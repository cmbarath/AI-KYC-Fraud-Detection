import hashlib
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.admin_routes import router as admin_router
from backend.app.api.fraud_routes import router as fraud_router
from backend.app.api.kyc_routes import router as kyc_router
from backend.app.api.ocr_routes import router as ocr_router
from backend.app.api.tx_routes import router as tx_router
from backend.app.config import settings
from backend.app.database import Base, get_db
from backend.app.models.document import Document

APP_TOKEN = "test-application-access-token"
ADMIN_TOKEN = "test-distinct-administrator-access-token"


def _registration_payload(suffix: str) -> dict:
    return {
        "first_name": "Synthetic",
        "last_name": "Applicant",
        "date_of_birth": "1990-05-14",
        "email": f"security-{suffix}@example.test",
        "phone_number": f"+1555{suffix[:7]}",
        "id_type": "DEMO_NATIONAL_ID",
        "id_number": f"SIM-{suffix[:12].upper()}",
        "address_line": "1 Synthetic Street",
        "city": "Example City",
        "state": "Test State",
        "country": "Simulatedland",
        "declared_income": "50000",
        "employment_type": "Salaried",
    }


def _create_test_app():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(kyc_router, prefix="/api/v1")
    app.include_router(ocr_router, prefix="/api/v1")
    app.include_router(fraud_router, prefix="/api/v1")
    app.include_router(tx_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = override_get_db

    @app.get("/api/v1/health")
    def health():
        return {"status": "healthy"}

    return app, engine, test_session


def test_health_is_public_and_application_routes_require_token(monkeypatch):
    monkeypatch.setattr(settings, "APP_API_TOKEN", APP_TOKEN)
    monkeypatch.setattr(settings, "ADMIN_ACCESS_TOKEN", ADMIN_TOKEN)
    app, engine, _ = _create_test_app()
    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/health").status_code == 200
            denied = client.post(
                "/api/v1/kyc/register",
                json=_registration_payload(uuid.uuid4().hex),
            )
            assert denied.status_code == 401

            applicant_id = str(uuid.uuid4())
            protected_requests = [
                client.post(
                    "/api/v1/ocr/upload-authorization",
                    json={
                        "applicant_id": applicant_id,
                        "filename": "identity.png",
                        "content_type": "image/png",
                        "file_size": 1024,
                    },
                ),
                client.post(
                    "/api/v1/ocr/process-upload",
                    json={
                        "applicant_id": applicant_id,
                        "object_path": f"{applicant_id}/{uuid.uuid4()}.png",
                        "filename": "identity.png",
                        "content_type": "image/png",
                        "document_type": "DEMO_ID_FRONT",
                        "form_name": "Synthetic Applicant",
                        "form_id": "SIM-SYNTHETIC",
                        "form_dob": "1990-05-14",
                    },
                ),
                client.get(
                    f"/api/v1/ocr/documents/{uuid.uuid4()}",
                    params={"applicant_id": applicant_id},
                ),
                client.post(
                    "/api/v1/fraud/evaluate",
                    json={"age": 30, "declared_income": 50000},
                ),
            ]
            assert [response.status_code for response in protected_requests] == [
                401,
                401,
                401,
                401,
            ]

            registered = client.post(
                "/api/v1/kyc/register",
                json=_registration_payload(uuid.uuid4().hex),
                headers={"X-API-Token": APP_TOKEN},
            )
            assert registered.status_code == 201
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_administration_requires_a_distinct_admin_token(monkeypatch):
    monkeypatch.setattr(settings, "APP_API_TOKEN", APP_TOKEN)
    monkeypatch.setattr(settings, "ADMIN_ACCESS_TOKEN", ADMIN_TOKEN)
    app, engine, _ = _create_test_app()
    try:
        with TestClient(app) as client:
            app_token_response = client.get(
                "/api/v1/admin/metrics",
                headers={"X-API-Token": APP_TOKEN},
            )
            assert app_token_response.status_code == 401

            admin_response = client.get(
                "/api/v1/admin/metrics",
                headers={"X-Admin-Access-Token": ADMIN_TOKEN},
            )
            assert admin_response.status_code == 200
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_admin_status_change_requires_admin_token_and_writes_audit_log(monkeypatch):
    monkeypatch.setattr(settings, "APP_API_TOKEN", APP_TOKEN)
    monkeypatch.setattr(settings, "ADMIN_ACCESS_TOKEN", ADMIN_TOKEN)
    app, engine, _ = _create_test_app()
    try:
        with TestClient(app) as client:
            applicant = client.post(
                "/api/v1/kyc/register",
                json=_registration_payload(uuid.uuid4().hex),
                headers={"X-API-Token": APP_TOKEN},
            ).json()
            status_url = f"/api/v1/admin/applications/{applicant['id']}/status"
            payload = {"status": "APPROVED", "notes": "Synthetic security test"}

            denied = client.patch(
                status_url,
                json=payload,
                headers={"X-API-Token": APP_TOKEN},
            )
            updated = client.patch(
                status_url,
                json=payload,
                headers={"X-Admin-Access-Token": ADMIN_TOKEN},
            )
            audit = client.get(
                f"/api/v1/admin/audit-logs/{applicant['id']}",
                headers={"X-Admin-Access-Token": ADMIN_TOKEN},
            )

            assert denied.status_code == 401
            assert updated.status_code == 200
            assert updated.json()["new_status"] == "APPROVED"
            assert any(item["event_type"] == "STATUS_OVERRIDE" for item in audit.json())
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_missing_access_token_configuration_fails_closed(monkeypatch):
    monkeypatch.setattr(settings, "APP_API_TOKEN", "")
    monkeypatch.setattr(settings, "ADMIN_ACCESS_TOKEN", "")
    app, engine, _ = _create_test_app()
    try:
        with TestClient(app) as client:
            app_response = client.post(
                "/api/v1/kyc/register",
                json=_registration_payload(uuid.uuid4().hex),
            )
            admin_response = client.get("/api/v1/admin/metrics")
            health_response = client.get("/api/v1/health")

            assert app_response.status_code == 503
            assert admin_response.status_code == 503
            assert health_response.status_code == 200
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_document_processing_and_retrieval_are_bound_to_applicant(monkeypatch):
    monkeypatch.setattr(settings, "APP_API_TOKEN", APP_TOKEN)
    monkeypatch.setattr(settings, "ADMIN_ACCESS_TOKEN", ADMIN_TOKEN)
    app, engine, test_session = _create_test_app()
    try:
        with TestClient(app) as client:
            headers = {"X-API-Token": APP_TOKEN}
            first = client.post(
                "/api/v1/kyc/register",
                json=_registration_payload(uuid.uuid4().hex),
                headers=headers,
            ).json()
            second = client.post(
                "/api/v1/kyc/register",
                json=_registration_payload(uuid.uuid4().hex),
                headers=headers,
            ).json()

            process_response = client.post(
                "/api/v1/ocr/process-upload",
                headers=headers,
                json={
                    "applicant_id": first["id"],
                    "object_path": f"{second['id']}/{uuid.uuid4()}.png",
                    "filename": "identity.png",
                    "content_type": "image/png",
                    "document_type": "DEMO_ID_FRONT",
                    "form_name": "Synthetic Applicant",
                    "form_id": "SIM-SYNTHETIC",
                    "form_dob": "1990-05-14",
                },
            )
            assert process_response.status_code == 403

            with test_session() as db:
                document = Document(
                    applicant_id=second["id"],
                    document_type="DEMO_ID_FRONT",
                    file_name="identity.png",
                    file_path=f"{second['id']}/{uuid.uuid4()}.png",
                    file_hash=hashlib.sha256(uuid.uuid4().bytes).hexdigest(),
                )
                db.add(document)
                db.commit()
                document_id = document.id

            retrieve_response = client.get(
                f"/api/v1/ocr/documents/{document_id}",
                params={"applicant_id": first["id"]},
                headers=headers,
            )
            assert retrieve_response.status_code == 404
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_legacy_multipart_upload_is_disabled_on_vercel(monkeypatch):
    monkeypatch.setattr(settings, "APP_API_TOKEN", APP_TOKEN)
    monkeypatch.setattr(settings, "ADMIN_ACCESS_TOKEN", ADMIN_TOKEN)
    monkeypatch.setenv("VERCEL", "1")
    app, engine, _ = _create_test_app()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ocr/upload",
                headers={"X-API-Token": APP_TOKEN},
                files={"file": ("legacy.png", b"unused", "image/png")},
                data={"document_type": "DEMO_ID_FRONT"},
            )
            assert response.status_code == 410
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_legacy_multipart_upload_remains_available_locally(monkeypatch):
    from backend.app.services.ocr_service import ocr_service

    def fake_extract_text_and_entities(image_path):
        assert Path(image_path).is_file()
        return {
            "raw_text": "synthetic test",
            "extracted_name": "Synthetic Applicant",
            "extracted_id_number": "SIM-1234",
            "extracted_dob": "1990-05-14",
            "quality_report": {
                "laplacian_variance": 1.0,
                "is_blurry": False,
                "edge_density": 0.1,
                "tamper_suspected": False,
            },
            "bounding_boxes": [],
        }

    monkeypatch.setattr(settings, "APP_API_TOKEN", APP_TOKEN)
    monkeypatch.setattr(settings, "ADMIN_ACCESS_TOKEN", ADMIN_TOKEN)
    monkeypatch.setattr(settings, "ENABLE_LEGACY_DOCUMENT_UPLOAD", True)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setattr(
        ocr_service,
        "extract_text_and_entities",
        fake_extract_text_and_entities,
    )
    app, engine, _ = _create_test_app()
    try:
        sample_path = (
            Path(__file__).resolve().parents[1]
            / "data_samples"
            / "sample_id_john_doe_pass.png"
        )
        with TestClient(app) as client, sample_path.open("rb") as image_file:
            response = client.post(
                "/api/v1/ocr/upload",
                headers={"X-API-Token": APP_TOKEN},
                files={
                    "file": (
                        sample_path.name,
                        image_file,
                        "image/png",
                    )
                },
                data={"document_type": "DEMO_ID_FRONT"},
            )
            assert response.status_code == 200
            assert response.json()["document_id"] is None
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_signed_upload_token_is_not_written_to_logs(monkeypatch, caplog):
    class FakeBucket:
        def create_signed_upload_url(self, path):
            assert path.endswith(".png")
            return {"token": "synthetic-signed-upload-token"}

    monkeypatch.setattr(settings, "APP_API_TOKEN", APP_TOKEN)
    monkeypatch.setattr(settings, "ADMIN_ACCESS_TOKEN", ADMIN_TOKEN)
    monkeypatch.setattr(
        "backend.app.api.ocr_routes.get_storage_bucket",
        lambda: FakeBucket(),
    )
    app, engine, _ = _create_test_app()
    try:
        with TestClient(app) as client:
            applicant = client.post(
                "/api/v1/kyc/register",
                json=_registration_payload(uuid.uuid4().hex),
                headers={"X-API-Token": APP_TOKEN},
            ).json()
            response = client.post(
                "/api/v1/ocr/upload-authorization",
                headers={"X-API-Token": APP_TOKEN},
                json={
                    "applicant_id": applicant["id"],
                    "filename": "identity.png",
                    "content_type": "image/png",
                    "file_size": 1024,
                    "document_type": "DEMO_ID_FRONT",
                },
            )
            assert response.status_code == 200
            assert response.json()["token"] == "synthetic-signed-upload-token"
            assert "synthetic-signed-upload-token" not in caplog.text
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_streamlit_client_sends_tokens_only_as_request_headers(monkeypatch):
    from unittest.mock import Mock

    from frontend.utils.api_client import APIClient

    monkeypatch.setenv("APP_API_TOKEN", APP_TOKEN)
    response = Mock(status_code=200)
    response.json.return_value = {"ok": True}
    response.raise_for_status.return_value = None

    post_mock = Mock(return_value=response)
    get_mock = Mock(return_value=response)
    with monkeypatch.context() as patch:
        patch.setattr("frontend.utils.api_client.requests.post", post_mock)
        patch.setattr("frontend.utils.api_client.requests.get", get_mock)
        client = APIClient("http://backend.test/api/v1")
        client.register_kyc({"first_name": "Synthetic"})
        client.get_admin_metrics(ADMIN_TOKEN)

        assert post_mock.call_args.kwargs["headers"] == {"X-API-Token": APP_TOKEN}
        assert get_mock.call_args.kwargs["headers"] == {
            "X-Admin-Access-Token": ADMIN_TOKEN
        }


def test_streamlit_client_reads_backend_url_from_streamlit_secrets(monkeypatch):
    from frontend.utils import api_client as api_client_module

    monkeypatch.delenv("BACKEND_API_URL", raising=False)
    monkeypatch.setattr(
        api_client_module,
        "_streamlit_secret",
        lambda name: "https://backend.example/api/v1" if name == "BACKEND_API_URL" else None,
    )

    client = api_client_module.APIClient()

    assert client.base_url == "https://backend.example/api/v1"


def test_streamlit_storage_client_rejects_secret_supabase_keys(monkeypatch):
    import base64
    import json

    import pytest

    from frontend.utils.api_client import APIClient

    monkeypatch.setenv("SUPABASE_URL", "https://project.example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "sb_publishable_synthetic-public-key")
    assert APIClient._frontend_supabase_config() == (
        "https://project.example.supabase.co",
        "sb_publishable_synthetic-public-key",
    )

    payload = base64.urlsafe_b64encode(
        json.dumps({"role": "service_role"}).encode()
    ).decode().rstrip("=")
    monkeypatch.setenv("SUPABASE_KEY", f"header.{payload}.signature")

    with pytest.raises(RuntimeError, match="publishable or anon key"):
        APIClient._frontend_supabase_config()

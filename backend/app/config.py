import os
import tempfile

from pydantic import Field
from pydantic_settings import BaseSettings

_DEFAULT_BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
_REQUIRED_MODEL_ARTIFACTS = (
    "preprocessor.joblib",
    "random_forest_model.joblib",
    "xgboost_model.joblib",
    "logistic_regression_model.joblib",
    "model_metrics.json",
)


def _default_data_dir() -> str:
    if os.getenv("VERCEL") == "1":
        return os.path.join(tempfile.gettempdir(), "ai-kyc-data")
    base_dir = os.getenv("BASE_DIR", _DEFAULT_BASE_DIR)
    return os.path.join(base_dir, "data_samples")


def _validate_model_artifacts(model_dir: str) -> None:
    missing = [
        filename
        for filename in _REQUIRED_MODEL_ARTIFACTS
        if not os.path.isfile(os.path.join(model_dir, filename))
    ]
    if missing:
        raise RuntimeError(
            f"Required packaged ML artifacts are missing from MODEL_DIR "
            f"{model_dir!r}: {', '.join(missing)}"
        )


def _validate_database_url(database_url: str, is_vercel: bool) -> None:
    if is_vercel and not database_url.startswith("postgres"):
        raise RuntimeError(
            "Vercel requires DATABASE_URL to use PostgreSQL; SQLite would write "
            "to the read-only application filesystem."
        )


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI KYC Verification & Fraud Detection System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Base Directories
    BASE_DIR: str = _DEFAULT_BASE_DIR
    DATA_DIR: str = Field(default_factory=_default_data_dir)
    MODEL_DIR: str = os.path.join(_DEFAULT_BASE_DIR, "ml_engine", "saved_models")
    
    # Default to SQLite for local development; PostgreSQL is selected in the cloud.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'backend', 'kyc_fraud.db')}"
    )
    DATABASE_SSL_MODE: str = os.getenv("DATABASE_SSL_MODE", "require")
    APP_API_TOKEN: str = ""
    ADMIN_ACCESS_TOKEN: str = ""
    ENABLE_LEGACY_DOCUMENT_UPLOAD: bool = True
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    SUPABASE_STORAGE_BUCKET: str = os.getenv(
        "SUPABASE_STORAGE_BUCKET",
        "kyc-documents"
    )
    MAX_DOCUMENT_SIZE_BYTES: int = 5 * 1024 * 1024
    
    # Risk Classification Thresholds
    RISK_THRESHOLD_LOW: int = 25
    RISK_THRESHOLD_MEDIUM: int = 55
    RISK_THRESHOLD_HIGH: int = 80
    
    class Config:
        env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        extra = "allow"

settings = Settings()

_validate_database_url(settings.DATABASE_URL, os.getenv("VERCEL") == "1")
_validate_model_artifacts(settings.MODEL_DIR)

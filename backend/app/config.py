import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI KYC Verification & Fraud Detection System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Base Directories
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    DATA_DIR: str = os.path.join(BASE_DIR, "data_samples")
    MODEL_DIR: str = os.path.join(BASE_DIR, "ml_engine", "saved_models")
    
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

# Ensure critical runtime directories exist
os.makedirs(settings.MODEL_DIR, exist_ok=True)
os.makedirs(settings.DATA_DIR, exist_ok=True)

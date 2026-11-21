import os
import sys

# Ensure root is in python path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
import backend.app.models
from backend.app.api.kyc_routes import router as kyc_router
from backend.app.api.ocr_routes import router as ocr_router
from backend.app.api.fraud_routes import router as fraud_router
from backend.app.api.tx_routes import router as tx_router
from backend.app.api.admin_routes import router as admin_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Identity Verification & Fraud Detection REST API (Educational Simulation)",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for Streamlit frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN] if settings.FRONTEND_ORIGIN else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(kyc_router, prefix=settings.API_V1_PREFIX)
app.include_router(ocr_router, prefix=settings.API_V1_PREFIX)
app.include_router(fraud_router, prefix=settings.API_V1_PREFIX)
app.include_router(tx_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "ONLINE",
        "documentation": "/docs",
        "notice": "DEMO & EDUCATIONAL SIMULATION ONLY • NO REAL IDENTITY CHECKS CONDUCTED"
    }

@app.get(f"{settings.API_V1_PREFIX}/health")
def health_check():
    database_type = (
        "postgresql"
        if settings.DATABASE_URL.startswith(("postgres", "postgresql"))
        else "sqlite"
    )
    return {
        "status": "healthy",
        "database": f"{database_type}_connected",
        "models_available": ["random_forest", "xgboost", "logistic_regression"],
        "ocr_engine": "EasyOCR_OpenCV"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

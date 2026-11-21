# AI-Based Identity Verification and Fraud Detection System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.53%2B-FF4B4B.svg)](https://streamlit.io/)
[![XGBoost](https://img.shields.io/badge/XGBoost-3.1%2B-EB5424.svg)](https://xgboost.readthedocs.io/)
[![EasyOCR](https://img.shields.io/badge/EasyOCR-1.7%2B-brightgreen.svg)](https://github.com/JaidedAI/EasyOCR)
[![Explainable_AI](https://img.shields.io/badge/XAI-SHAP-blueviolet.svg)](https://shap.readthedocs.io/)

> **Academic & Internship Project Notice**: This project is developed strictly as an educational and research simulation for an Artificial Intelligence internship project. All identity documents, applicant details, national ID numbers, and financial records used are **100% synthetic**. This system **does not** interface with actual government databases (such as Aadhaar, PAN, passport authorities) or real-world banking switches.

---

## 📌 Project Overview

In digital finance and onboarding, identity fraud, document tampering, synthetic identities, and transactional anomalies present severe systemic risks. This project delivers an end-to-end AI system that:
1. **Automates KYC Document Extraction**: Stores identity images in a private Supabase Storage bucket, performs OpenCV contrast enhancement, edge analysis, and blur detection, then extracts structured entities (Name, ID, DOB) using EasyOCR.
2. **Cross-Validates Form & Document Data**: Performs fuzzy string cross-matching using RapidFuzz to detect mismatches or spelling discrepancies.
3. **Detects Duplicates & Recycled Identities**: Hashing algorithms and SQLAlchemy database indexes detect repeated use of synthetic IDs, phone numbers, and disposable emails.
4. **Calculates a Prototype Fraud Risk Score**: Compares trained **Random Forest**, **XGBoost**, and **Logistic Regression** classifiers and allows runtime selection of one model. The Random Forest is the default runtime model. It converts the selected model's class-1 probability into a `0 to 100` demonstration score with **Low**, **Medium**, **High**, and **Critical** tiers. These thresholds are not calibrated regulatory risk classifications.
5. **Provides Explainable AI (XAI)**: Uses **SHAP (SHapley Additive exPlanations)** to output local feature attribution waterfall cards explaining why an applicant was flagged.
6. **Detects Transaction Anomalies**: Flags sudden amount spikes relative to declared income, round-number structuring, and unusual merchant categories.
7. **Offers an Executive Dark Dashboard**: An interactive, modern UI built with Streamlit and Plotly for compliance review, manual approvals, and model benchmarking.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend UI** | Streamlit (Dark Theme), Plotly Charts, Custom CSS |
| **Backend API** | FastAPI, Uvicorn, Pydantic V2 |
| **Computer Vision & OCR** | OpenCV, EasyOCR, Pillow |
| **Machine Learning Core** | Scikit-Learn, XGBoost, Random Forest, Logistic Regression |
| **Explainable AI (XAI)** | SHAP (TreeExplainer & Waterfall Attributions) |
| **Database & ORM** | Supabase PostgreSQL, local SQLite, SQLAlchemy 2.0 |
| **Private Document Storage** | Supabase Storage signed uploads |
| **Data & Fuzzy Matching** | Pandas, NumPy, RapidFuzz, Faker |

---

## 🏛️ System Architecture

```
[Streamlit Frontend] -- REST/JSON --> [FastAPI Backend] -- ORM --> [Supabase PostgreSQL]
        │                                  │
        └── signed upload token ──────────>│
        └── direct signed upload ─────────────────────────> [Private Supabase Storage]
                                           └── private download for OCR

FastAPI services: OpenCV preprocessing, EasyOCR extraction, RapidFuzz matching,
fraud scoring, SHAP explanations, and transaction anomaly checks.
```

---

## 📊 Model Comparison & Benchmark Results

Models were trained and evaluated on a synthetic benchmark dataset of 6,000 stratified KYC records (80/20 train/test split):

| Algorithm | ROC-AUC | PR-AUC | Precision | Recall | F1-Score |
|---|---|---|---|---|---|
| **Logistic Regression** | 0.9383 | 0.8903 | 95.00% | 87.82% | 0.9127 |
| **Random Forest** | 0.9365 | 0.9052 | 96.77% | 88.24% | 0.9231 |
| **XGBoost Classifier** | 0.9368 | 0.9177 | 96.33% | 88.24% | 0.9211 |

### Risk Tiers & Automated Decisions
The tiers below are prototype decision thresholds only. The class-1 probability has not been calibrated for real regulatory or identity-verification use.

- **0 - 25 (LOW Risk)**: `AUTO_APPROVE` — Low probability of identity fraud.
- **26 - 55 (MEDIUM Risk)**: `MANUAL_REVIEW` — Borderline flags or secondary check recommended.
- **56 - 80 (HIGH Risk)**: `MANUAL_REVIEW` — Multiple discrepancies or velocity spikes flagged.
- **81 - 100 (CRITICAL Risk)**: `REJECT` — Document tampering, duplicate identity, or severe risk factors detected.

---

## 📁 Project Directory Structure

```
AI_KYC_Fraud_Detection/
├── README.md                      # Documentation & project manual
├── requirements.txt               # Pinned Python package dependencies
├── run_backend.py                 # FastAPI backend launcher script
├── run_servers.bat                # Windows 1-click batch launcher
│
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app & routing
│   │   ├── config.py              # Configuration & directory paths
│   │   ├── database.py            # SQLite & SQLAlchemy engine
│   │   ├── init_db.py             # Schema initialization script
│   │   ├── models/                # SQLAlchemy ORM models (5 tables)
│   │   ├── schemas/               # Pydantic DTOs & validation schemas
│   │   ├── services/              # OCR, Fuzzy Matcher, ML Scoring, Anomaly
│   │   └── api/                   # REST API route handlers
│
├── frontend/
│   ├── app.py                     # Streamlit main entry page
│   ├── styles/custom.css          # Dark-theme CSS styling
│   ├── utils/
│   │   ├── api_client.py          # FastAPI HTTP client
│   │   └── plot_helpers.py        # Plotly charts (Gauges, SHAP, Benchmarks)
│   └── pages/
│       ├── 1_📝_KYC_Registration.py
│       ├── 2_🔍_Verify_Status.py
│       ├── 3_💳_Transaction_Check.py
│       └── 4_📊_Admin_Dashboard.py
│
├── ml_engine/
│   ├── data/
│   │   ├── generate_synthetic_data.py # Synthetic data generation
│   │   └── synthetic_kyc_dataset.csv
│   ├── src/
│   │   ├── data_preprocessor.py   # Scikit-Learn ColumnTransformer
│   │   ├── train_models.py        # Model training & benchmark script
│   │   └── explainer.py           # SHAP local & global explainer
│   └── saved_models/              # Serialized .joblib artifacts
│
├── data_samples/                  # Pre-generated synthetic ID cards
│   ├── sample_id_john_doe_pass.png
│   ├── sample_id_jane_smith_mismatch.png
│   └── sample_id_robert_tampered.png
│
└── tests/                         # Unit & integration tests
    ├── test_ocr_pipeline.py
    └── test_api_endpoints.py
```

---

## 🚀 Setup & Execution Guide

### 1. Prerequisites
- Python 3.12 installed
- Git installed (optional)

### 2. Install Dependencies
Open a terminal in the project directory:
```bash
pip install -r backend-requirements.txt
pip install -r frontend-requirements.txt
```

### 3. Supabase Storage Settings
The backend reads `backend/.env`. Configure `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (or `SUPABASE_SECRET_KEY`), and `SUPABASE_STORAGE_BUCKET=kyc-documents` there. The project URL may be supplied with or without a `/rest/v1` suffix.

Configure distinct, long random values for `APP_API_TOKEN` and `ADMIN_ACCESS_TOKEN` in the backend/Vercel environment. Configure only the matching `APP_API_TOKEN` in Streamlit Community Cloud secrets; never put `ADMIN_ACCESS_TOKEN` in shared Streamlit secrets. Application routes require `APP_API_TOKEN`, administrative routes require `ADMIN_ACCESS_TOKEN`, and the health endpoint remains public. An administrator enters the admin token in the Admin Dashboard; it is kept in that Streamlit session and sent only in server-to-server request headers.

Configure Vercel with `DATABASE_URL`, `DATABASE_SSL_MODE`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_STORAGE_BUCKET`, `APP_API_TOKEN`, `ADMIN_ACCESS_TOKEN`, and `VERCEL_SUPPORT_LARGE_FUNCTIONS=1`. Keep the Supabase service-role key and admin token in Vercel only.

Configure Streamlit Community Cloud secrets with `BACKEND_API_URL`, `APP_API_TOKEN`, `SUPABASE_URL`, and `SUPABASE_KEY`. `SUPABASE_KEY` must be a publishable/anon key; never put the backend service-role key or admin token in Streamlit settings. The `kyc-documents` bucket is private and limits objects to 5 MB JPEG/PNG images. Cloud document uploads use the signed direct-to-Storage flow; the legacy multipart endpoint is disabled on Vercel and remains available locally.

### 4. Quick Windows Launch (Recommended)
Double-click `run_servers.bat` or run:
```cmd
run_servers.bat
```
This automatically starts both the FastAPI backend and Streamlit frontend in separate console windows.

### 5. Manual Launch
#### Terminal 1 — Start the FastAPI Backend:
```bash
python run_backend.py
```
*API will run at `http://127.0.0.1:8000` with Swagger docs at `http://127.0.0.1:8000/docs`.*

#### Terminal 2 — Start the Streamlit Dashboard:
```bash
python -m streamlit run frontend/app.py --server.port 8501
```
*Frontend opens automatically in your browser at `http://localhost:8501`.*

---

## 🧪 Testing & Verification

Run the test suite to verify the OCR pipeline and all REST API endpoints:
```bash
# Test OCR extraction & fuzzy matching
python tests/test_ocr_pipeline.py

# Test all FastAPI endpoints and DB persistence
python tests/test_api_endpoints.py
```

---

## 👥 Authors & Academic Context
Developed for an **Artificial Intelligence Internship Project** demonstrating practical application of Computer Vision, Machine Learning classification, Explainable AI (SHAP), and Full-Stack dashboard engineering.

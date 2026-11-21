import os
import sys

FRONTEND_DIR = os.path.abspath(os.path.dirname(__file__))
if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

import streamlit as st
from utils.api_client import api_client

# Page Config
st.set_page_config(
    page_title="AI KYC & Fraud Detection System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_path = os.path.join(os.path.dirname(__file__), "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Sidebar System Health Status
with st.sidebar:
    st.markdown("### ⚙️ System Status")
    health = api_client.check_health()
    st.text(f"Health endpoint: {api_client.health_url or 'Invalid BACKEND_API_URL'}")
    if health.get("status") == "healthy":
        st.success("● Backend API: Connected & Ready")
        st.caption(health["diagnostic"])
        st.caption("DB: Configured backend | Engine: EasyOCR + XGB/RF")
    else:
        st.warning("⚠️ Backend API Offline or Unhealthy")
        st.caption(health["diagnostic"])
    
    st.divider()
    st.markdown("### 📌 Navigation")
    st.markdown("""
    - [1. KYC Registration](KYC_Registration)
    - [2. Verify Status](Verify_Status)
    - [3. Transaction Check](Transaction_Check)
    - [4. Admin Dashboard](Admin_Dashboard)
    """)
    st.divider()
    st.caption("AI Internship Project • Academic Demo")

# Main Header
st.title("🛡️ AI-Based Identity Verification & Fraud Detection")
st.markdown("Automating identity verification with Computer Vision (OpenCV + EasyOCR) and intelligent fraud pattern detection with Machine Learning (XGBoost, Random Forest, Logistic Regression) & Explainable AI (SHAP).")

# Mandatory Compliance & Educational Notice
st.markdown("""
<div class="disclaimer-banner">
    <strong>⚠️ Educational & Internship Simulation Notice:</strong><br>
    This project is an artificial intelligence demonstration prototype built strictly for research and academic evaluation.
    All identity documents, personal profiles, and transaction records are <strong>100% synthetic</strong> and generated using simulation tools.
    This system does <em>not</em> connect to real government registries (such as Aadhaar, PAN, passport agencies) or live banking networks.
</div>
""", unsafe_allow_html=True)

# Feature Highlights in Columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="kyc-card">
        <h3>📝 1. Smart KYC</h3>
        <p style="color: #94a3b8; font-size: 0.9rem;">
            Registration portal capturing applicant identity details, synthetic ID numbers, and financial profiles.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="kyc-card">
        <h3>👁️ 2. Vision OCR</h3>
        <p style="color: #94a3b8; font-size: 0.9rem;">
            OpenCV image quality checks and cleanup, EasyOCR entity extraction, and RapidFuzz form-to-document matching.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="kyc-card">
        <h3>🧠 3. ML Risk Engine</h3>
        <p style="color: #94a3b8; font-size: 0.9rem;">
            Single-model classification with Random Forest as the default, producing a 0–100 prototype risk score with SHAP local feature attribution.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="kyc-card">
        <h3>📊 4. Admin Ops</h3>
        <p style="color: #94a3b8; font-size: 0.9rem;">
            Dark-themed interactive analytics, model benchmarking, manual audit workflow, and anomaly tracking.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Technical Architecture Flow
st.subheader("📐 System Architecture & Data Flow")
st.markdown("""
```
[Applicant Form] + [Synthetic Document] 
       │
       ▼
 [OpenCV Preprocessing] ──▶ Laplacian Blur & Tamper Analysis
       │
       ▼
    [EasyOCR] ────────────▶ Entity Extraction (Name, ID, DOB)
       │
       ▼
 [Fuzzy Matcher Engine] ──▶ Normalized Cross-Validation (0.00 - 1.00)
       │
       ▼
 [ML Classifier Core] ────▶ Scikit-Learn / XGBoost Inference
       │
       ▼
 [Risk Scoring Engine] ───▶ Prototype 0 - 100 Score & 4 Tiers (Low, Med, High, Crit)
       │
       ▼
 [Explainable AI (SHAP)] ─▶ Waterfall of Driving & Mitigating Factors
       │
       ▼
[Database Storage & Ops] ──▶ Complete Audit Trail & Executive Dashboard
```
""")

st.info("👈 Use the left sidebar to navigate to the KYC Registration module or Admin Dashboard.")

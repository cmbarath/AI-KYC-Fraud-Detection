import os
import sys
from datetime import date, datetime
from pathlib import Path

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

import streamlit as st
from utils.api_client import api_client
from utils.plot_helpers import create_risk_gauge, create_shap_waterfall_bar

st.set_page_config(page_title="KYC Registration | AI KYC System", page_icon="📝", layout="wide")

# Custom CSS
css_path = os.path.join(os.path.dirname(__file__), "..", "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📝 KYC Identity Registration & Verification")
st.caption("Submit synthetic identity information and verify document authenticity with AI Computer Vision & ML.")

# Pre-fill Demo Buttons
st.markdown("##### ⚡ Quick Demo Loaders")
demo_col1, demo_col2, demo_col3 = st.columns(3)

if "form_data" not in st.session_state:
    st.session_state["form_data"] = {
        "first_name": "Johnathan",
        "last_name": "Doe",
        "dob": "1990-05-14",
        "email": "johnathan.doe@gmail.com",
        "phone": "+15559821447",
        "id_type": "DEMO_NATIONAL_ID",
        "id_number": "SIM-9821-4471",
        "address": "123 Tech Park Ave",
        "city": "Cyberia City",
        "state": "Cyber State",
        "income": 75000,
        "employment": "Salaried",
        "channel": "Web"
    }

with demo_col1:
    if st.button("🟢 Load Clean Demo Profile"):
        st.session_state["form_data"] = {
            "first_name": "Johnathan",
            "last_name": "Doe",
            "dob": "1990-05-14",
            "email": "johnathan.doe@gmail.com",
            "phone": "+15559821447",
            "id_type": "DEMO_NATIONAL_ID",
            "id_number": "SIM-9821-4471",
            "address": "123 Tech Park Ave",
            "city": "Cyberia City",
            "state": "Cyber State",
            "income": 75000,
            "employment": "Salaried",
            "channel": "Web"
        }
        st.rerun()

with demo_col2:
    if st.button("🟡 Load Mismatch Identity Profile"):
        st.session_state["form_data"] = {
            "first_name": "Alexander",
            "last_name": "Hamilton",
            "dob": "1988-01-11",
            "email": "alex.hamilton@tempmail.net",
            "phone": "+15551122334",
            "id_type": "DEMO_NATIONAL_ID",
            "id_number": "SIM-9999-0000",
            "address": "55 Broadway Street",
            "city": "New York",
            "state": "NY",
            "income": 40000,
            "employment": "Freelance",
            "channel": "Mobile_App"
        }
        st.rerun()

with demo_col3:
    if st.button("🔴 Load Suspicious Bot Profile"):
        st.session_state["form_data"] = {
            "first_name": "Robert",
            "last_name": "Vance",
            "dob": "1982-12-01",
            "email": "bot_user_99@mailinator.com",
            "phone": "+15557733112",
            "id_type": "DEMO_NATIONAL_ID",
            "id_number": "SIM-7733-1122",
            "address": "Unknown Alleyway",
            "city": "Proxy City",
            "state": "Offshore",
            "income": 20000,
            "employment": "Unemployed",
            "channel": "Web"
        }
        st.rerun()

st.divider()

# Form Inputs
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("1. Personal Details")
    fn = st.text_input("First Name", value=st.session_state["form_data"]["first_name"])
    ln = st.text_input("Last Name", value=st.session_state["form_data"]["last_name"])
    dob = st.text_input("Date of Birth (YYYY-MM-DD)", value=st.session_state["form_data"]["dob"])
    email = st.text_input("Email Address", value=st.session_state["form_data"]["email"])
    phone = st.text_input("Phone Number", value=st.session_state["form_data"]["phone"])

with c2:
    st.subheader("2. Identity Document & Financial Profile")
    id_type = st.selectbox(
        "ID Document Type",
        ["DEMO_NATIONAL_ID", "DEMO_PASSPORT", "DEMO_DRIVERS_LICENSE"],
        index=0
    )
    id_num = st.text_input("Synthetic ID Number", value=st.session_state["form_data"]["id_number"])
    addr = st.text_input("Address Line", value=st.session_state["form_data"]["address"])
    city = st.text_input("City", value=st.session_state["form_data"]["city"])
    state = st.text_input("State / Region", value=st.session_state["form_data"]["state"])
    income = st.number_input("Annual Declared Income ($)", value=st.session_state["form_data"]["income"], step=5000)
    emp_type = st.selectbox("Employment Type", ["Salaried", "Self-Employed", "Freelance", "Student", "Unemployed"], index=0)

st.divider()

# Document Upload Section
st.subheader("3. Document Upload & Vision OCR")
st.markdown("Select a pre-generated synthetic demo document or upload your own image:")

def _document_content_type(filename: str) -> str:
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(Path(filename).suffix.lower(), "")

sample_docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data_samples"))
sample_options = {
    "Matching Clean Pass (Johnathan Doe)": os.path.join(sample_docs_dir, "sample_id_john_doe_pass.png"),
    "Mismatched ID (Jane Smith)": os.path.join(sample_docs_dir, "sample_id_jane_smith_mismatch.png"),
    "Tampered Document (Robert Vance)": os.path.join(sample_docs_dir, "sample_id_robert_tampered.png"),
    "Upload Custom Image File": None
}

doc_choice = st.selectbox("Choose Document Source", list(sample_options.keys()))

image_bytes = None
image_filename = "document.png"
image_content_type = "image/png"

if sample_options[doc_choice] is not None:
    sample_path = sample_options[doc_choice]
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            image_bytes = f.read()
        image_filename = os.path.basename(sample_path)
        st.image(image_bytes, caption=f"Selected Demo Document: {image_filename}", width=500)
else:
    uploaded_file = st.file_uploader("Upload Identity Card Image (PNG, JPG)", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        image_bytes = uploaded_file.read()
        image_filename = uploaded_file.name
        image_content_type = _document_content_type(image_filename)
        st.image(image_bytes, caption="Uploaded Image", width=500)

# Verification & Submit Button
st.divider()
if st.button("🚀 Submit KYC & Run Complete AI Fraud Evaluation", type="primary"):
    if not image_bytes:
        st.error("Please provide or select an identity document image before proceeding.")
    elif len(image_bytes) > 5 * 1024 * 1024:
        st.error("Documents must be 5 MB or smaller.")
    elif not image_content_type:
        st.error("Only PNG and JPEG identity documents are supported.")
    else:
        try:
            api_client.validate_supabase_upload_config()
        except Exception as e:
            st.error(f"Document storage configuration error: {e}")
            st.stop()

        try:
            dob_date = datetime.strptime(dob.strip(), "%Y-%m-%d").date()
            if dob_date > date.today():
                st.error("Date of birth cannot be in the future.")
                st.stop()
            applicant_age = date.today().year - dob_date.year - (
                (date.today().month, date.today().day) < (dob_date.month, dob_date.day)
            )
            if applicant_age < 18 or applicant_age > 100:
                st.error("Applicant age must be between 18 and 100 for this prototype.")
                st.stop()
        except ValueError:
            st.error("Enter a valid Date of Birth in YYYY-MM-DD format.")
            st.stop()

        with st.spinner("Step 1/3: Registering Synthetic KYC Application..."):
            try:
                # 1. Register Application in DB
                reg_payload = {
                    "first_name": fn,
                    "last_name": ln,
                    "date_of_birth": dob,
                    "email": email,
                    "phone_number": phone,
                    "id_type": id_type,
                    "id_number": id_num,
                    "address_line": addr,
                    "city": city,
                    "state": state,
                    "country": "Simulatedland",
                    "declared_income": str(income),
                    "employment_type": emp_type,
                    "channel": "Web"
                }
                app_res = api_client.register_kyc(reg_payload)
                applicant_id = app_res["id"]
                app_number = app_res["application_number"]
                st.success(f"Application Created! Reference No: **{app_number}**")
            except Exception as e:
                st.error(f"Registration Error: {str(e)}")
                st.stop()

        with st.spinner("Step 2/3: Uploading to private storage, then running OCR and identity matching..."):
            try:
                # Upload directly to Supabase Storage using a short-lived signed token.
                authorization = api_client.create_document_upload_authorization({
                    "applicant_id": applicant_id,
                    "filename": image_filename,
                    "content_type": image_content_type,
                    "file_size": len(image_bytes),
                    "document_type": "DEMO_ID_FRONT",
                })
                api_client.upload_to_signed_document_path(
                    authorization=authorization,
                    file_bytes=image_bytes,
                )
                ocr_res = api_client.process_uploaded_document({
                    "applicant_id": applicant_id,
                    "object_path": authorization["object_path"],
                    "filename": image_filename,
                    "content_type": image_content_type,
                    "document_type": "DEMO_ID_FRONT",
                    "form_name": f"{fn} {ln}",
                    "form_id": id_num,
                    "form_dob": dob,
                })
                match_res = {
                    key: ocr_res[key]
                    for key in (
                        "name_match_score",
                        "id_match_score",
                        "dob_match_score",
                        "overall_match_score",
                        "is_verified",
                        "discrepancies",
                    )
                }

            except Exception as e:
                st.error(f"OCR Pipeline Error: {str(e)}")
                st.stop()

        with st.spinner("Step 3/3: Running Machine Learning Risk Engine & SHAP Explainability..."):
            try:
                # Evaluate Fraud Risk
                is_disposable = 1 if any(d in email.lower() for d in ["mailinator", "tempmail", "throwaway", "10minute"]) else 0
                tamper_flag = 1 if ocr_res["quality_report"]["tamper_suspected"] else 0
                ip_risk = 0.85 if is_disposable else 0.12

                eval_payload = {
                    "applicant_id": applicant_id,
                    "age": applicant_age,
                    "declared_income": float(income),
                    "id_type": id_type,
                    "employment_type": emp_type,
                    "channel": "Web",
                    "ocr_name_match_score": match_res["name_match_score"],
                    "ocr_id_match_score": match_res["id_match_score"],
                    "ocr_dob_match_score": match_res["dob_match_score"],
                    "tampered_document_flag": tamper_flag,
                    "ip_risk_score": ip_risk,
                    "device_reuse_count": 1 if not is_disposable else 3,
                    "disposable_email": is_disposable,
                    "registration_velocity": 1 if not is_disposable else 5,
                    "address_mismatch_flag": 1 if match_res["name_match_score"] < 0.60 else 0,
                    "model_name": "random_forest"
                }

                fraud_res = api_client.evaluate_fraud(eval_payload)

            except Exception as e:
                st.error(f"Fraud Scoring Error: {str(e)}")
                st.stop()

        # Display Comprehensive Verification Report
        st.divider()
        st.subheader("📋 Verification & Risk Assessment Results")

        res_col1, res_col2 = st.columns([1, 1])

        with res_col1:
            st.markdown("#### 👁️ Computer Vision & OCR Findings")
            st.markdown(f"**Extracted Name:** `{ocr_res.get('extracted_name') or 'Not Found'}`")
            st.markdown(f"**Extracted ID:** `{ocr_res.get('extracted_id_number') or 'Not Found'}`")
            st.markdown(f"**Extracted DOB:** `{ocr_res.get('extracted_dob') or 'Not Found'}`")
            st.caption("Image quality signals are heuristics, not proof of document authenticity or forgery.")
            
            st.markdown("##### Consistency Cross-Matching")
            st.progress(match_res["overall_match_score"], text=f"Overall Consistency: {match_res['overall_match_score'] * 100:.1f}%")
            st.caption(f"Name Match: {match_res['name_match_score']*100:.0f}% | ID Match: {match_res['id_match_score']*100:.0f}% | DOB Match: {match_res['dob_match_score']*100:.0f}%")
            
            if match_res["is_verified"]:
                st.success("✅ Document data matches form submission closely.")
            else:
                st.warning("⚠️ Discrepancies detected between document and form inputs.")
                for d in match_res["discrepancies"]:
                    st.write(f"- {d}")

            with st.expander("🔍 Image Quality & Tamper Diagnostics"):
                q = ocr_res["quality_report"]
                st.write(f"- **Sharpness (Laplacian Var):** {q['laplacian_variance']}")
                st.write(f"- **Blurry Image:** {'Yes' if q['is_blurry'] else 'No'}")
                st.write(f"- **Tampering Suspected:** {'⚠️ YES' if q['tamper_suspected'] else 'Clean'}")

        with res_col2:
            st.markdown("#### 🧠 Machine Learning Risk Classification")
            
            risk_tier = fraud_res["risk_tier"]
            risk_score = fraud_res["risk_score"]
            badge_class = f"badge-{risk_tier.lower()}"
            
            st.markdown(f"""
            <div style="margin-bottom: 12px;">
                <span class="{badge_class}">{risk_tier} RISK TIER</span> &nbsp;
                <strong>Action: {fraud_res['automated_decision'].replace('_', ' ')}</strong>
            </div>
            """, unsafe_allow_html=True)

            gauge_fig = create_risk_gauge(risk_score, risk_tier)
            st.plotly_chart(gauge_fig, use_container_width=True)

        # Explainable AI Waterfall Section
        st.markdown("#### 🔎 Explainable AI (SHAP) Factor Attribution")
        st.caption("How specific features influenced the ML model towards or against fraud classification:")
        
        shap_fig = create_shap_waterfall_bar(
            fraud_res.get("top_risk_drivers", []),
            fraud_res.get("top_risk_mitigators", [])
        )
        st.plotly_chart(shap_fig, use_container_width=True)

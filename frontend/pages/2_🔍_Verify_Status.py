import os
import sys

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

import streamlit as st
from utils.api_client import api_client

st.set_page_config(page_title="Verify Status | AI KYC System", page_icon="🔍", layout="wide")

# Custom CSS
css_path = os.path.join(os.path.dirname(__file__), "..", "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🔍 KYC Application Status & Audit History")
st.caption("Look up any application by its reference number to view complete verification records and audit logs.")

app_num_input = st.text_input("Enter Application Number (e.g., KYC-2026-XXXXX)", placeholder="KYC-2026-12345")

if st.button("Search Application", type="primary") or app_num_input:
    if not app_num_input.strip():
        st.warning("Please provide an application number.")
    else:
        with st.spinner("Fetching application data..."):
            try:
                res = api_client.lookup_application(app_num_input.strip())
                applicant = res["applicant"]
                documents = res["documents"]
                evaluations = res["evaluations"]

                st.divider()

                # Status Header
                status_color = {
                    "APPROVED": "#10b981",
                    "SUBMITTED": "#3b82f6",
                    "PENDING_REVIEW": "#f59e0b",
                    "REJECTED": "#ef4444",
                    "FLAGGED": "#dc2626"
                }.get(applicant["status"], "#94a3b8")

                st.markdown(f"""
                <div class="kyc-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h2 style="margin: 0; color: #f8fafc;">{applicant['first_name']} {applicant['last_name']}</h2>
                            <span style="color: #94a3b8; font-size: 0.9rem;">App No: {applicant['application_number']} | ID: {applicant['id_number']}</span>
                        </div>
                        <div>
                            <span style="background-color: {status_color}22; color: {status_color}; border: 1px solid {status_color}; padding: 6px 16px; border-radius: 20px; font-weight: bold;">
                                {applicant['status']}
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("👤 Applicant Profile")
                    st.write(f"- **Email:** `{applicant['email']}`")
                    st.write(f"- **Phone:** `{applicant['phone_number']}`")
                    st.write(f"- **Date of Birth:** `{applicant['date_of_birth']}`")
                    st.write(f"- **Address:** `{applicant['address']}`")
                    st.write(f"- **Declared Income:** `${float(applicant['declared_income']):,.2f}`")

                with col2:
                    st.subheader("🛡️ AI Risk & Evaluation History")
                    if evaluations:
                        latest_eval = evaluations[-1]
                        st.write(f"- **Risk Score:** `{latest_eval['risk_score']} / 100`")
                        st.write(f"- **Risk Tier:** `{latest_eval['risk_tier']}`")
                        st.write(f"- **Model Used:** `{latest_eval['model_used']}`")
                        st.write(f"- **System Decision:** `{latest_eval['automated_decision']}`")
                        st.write(f"- **Evaluated At:** `{latest_eval['evaluated_at']}`")
                    else:
                        st.info("No risk evaluations recorded yet.")

                # Documents Section
                st.subheader("📄 Verified Documents")
                if documents:
                    for d in documents:
                        st.markdown(f"""
                        <div class="kyc-card" style="padding: 12px;">
                            <strong>{d['file_name']}</strong> ({d['document_type']})<br>
                            <span style="font-size: 0.85rem; color: #94a3b8;">
                                Match Score: <strong>{d['overall_match_score']*100:.1f}%</strong> | Verified: {'✅ Yes' if d['is_verified'] else '⚠️ No'}
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write("No documents on file.")

                # Audit Trail
                st.subheader("📜 Audit & Activity Trail")
                admin_token = (
                    st.session_state.get("admin_token")
                    if st.session_state.get("admin_authenticated")
                    else None
                )
                if admin_token:
                    audit_logs = api_client.get_audit_logs(
                        applicant["id"],
                        admin_token=admin_token,
                    )
                    if audit_logs:
                        for log in audit_logs:
                            st.markdown(f"""
                            <div style="border-left: 3px solid #3b82f6; padding-left: 12px; margin-bottom: 12px;">
                                <span style="color: #94a3b8; font-size: 0.8rem;">{log['timestamp']} • [{log['actor']}]</span><br>
                                <strong>{log['event_type']}</strong>: {log['description']}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.write("No audit logs found.")
                else:
                    st.info("Administrative audit logs are visible after unlocking the Admin Dashboard.")

            except Exception as e:
                st.error(f"Application not found or lookup error: {str(e)}")

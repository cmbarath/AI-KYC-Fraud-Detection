import os
import sys
import requests

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

import streamlit as st
import pandas as pd
from utils.api_client import api_client
from utils.plot_helpers import (
    create_model_comparison_bar,
    create_risk_distribution_donut
)

st.set_page_config(page_title="Admin & Fraud Operations Dashboard", page_icon="📊", layout="wide")

# Custom CSS
css_path = os.path.join(os.path.dirname(__file__), "..", "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📊 KYC & Fraud Risk Operations Dashboard")
st.caption("Administrative monitoring, multi-model machine learning benchmarks, and application lifecycle governance.")

if not (
    st.session_state.get("admin_authenticated")
    and st.session_state.get("admin_token")
):
    st.session_state.pop("admin_authenticated", None)
    with st.form("admin_access_form"):
        supplied_admin_token = st.text_input(
            "Administrator access token",
            type="password",
            key="admin_token_input",
        )
        submit_admin_token = st.form_submit_button("Unlock admin dashboard")

    if submit_admin_token:
        if not supplied_admin_token:
            st.error("Enter the administrator token to continue.")
        else:
            try:
                api_client.get_admin_metrics(supplied_admin_token)
            except requests.HTTPError as error:
                if error.response is not None and error.response.status_code == 401:
                    st.error("Administrator access was denied.")
                else:
                    st.error("Could not verify administrator access with the backend.")
            except requests.RequestException:
                st.error("Could not connect to the administrative API.")
            else:
                st.session_state["admin_token"] = supplied_admin_token
                st.session_state["admin_authenticated"] = True
                st.rerun()

    st.info("Enter the administrator token to unlock this dashboard.")
    st.stop()

st.session_state.pop("admin_token_input", None)
admin_token = st.session_state["admin_token"]
if st.sidebar.button("Lock admin session"):
    st.session_state.pop("admin_token", None)
    st.session_state.pop("admin_authenticated", None)
    st.rerun()

try:
    metrics_data = api_client.get_admin_metrics(admin_token)
except requests.HTTPError:
    st.session_state.pop("admin_token", None)
    st.session_state.pop("admin_authenticated", None)
    st.session_state.pop("admin_token_input", None)
    st.error("Administrator access expired or was rejected. Unlock the dashboard again.")
    st.stop()
except requests.RequestException:
    st.error("Could not connect to the administrative API.")
    st.stop()

kpis = metrics_data.get("kpis", {})
tier_counts = metrics_data.get("risk_tier_counts", {})

# KPI Cards Row
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Total Applications</div>
        <div class="kpi-value">{kpis.get('total_applications', 0)}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Approved</div>
        <div class="kpi-value" style="color: #10b981;">{kpis.get('approved_applications', 0)}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Pending Review</div>
        <div class="kpi-value" style="color: #f59e0b;">{kpis.get('pending_review', 0)}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Flagged / Rejected</div>
        <div class="kpi-value" style="color: #ef4444;">{kpis.get('rejected_applications', 0) + kpis.get('flagged_applications', 0)}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Estimated Fraud Rate</div>
        <div class="kpi-value" style="color: #8b5cf6;">{kpis.get('estimated_fraud_rate_pct', 0.0)}%</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Charts Row
c_chart1, c_chart2 = st.columns([1, 1.3])

with c_chart1:
    donut_fig = create_risk_distribution_donut(tier_counts)
    st.plotly_chart(donut_fig, use_container_width=True)

with c_chart2:
    # Model Benchmark comparison
    try:
        models_meta = api_client.get_model_benchmarks()
        models_dict = models_meta.get("models", {})
        bar_fig = create_model_comparison_bar(models_dict)
        st.plotly_chart(bar_fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Model benchmark metrics not available: {str(e)}")

st.divider()

# Applications Management Table & Audit Review
st.subheader("📋 Application Review Queue")

filter_col1, filter_col2 = st.columns([1, 2])
with filter_col1:
    status_filter = st.selectbox("Filter Status", ["ALL", "SUBMITTED", "PENDING_REVIEW", "APPROVED", "REJECTED", "FLAGGED"])
with filter_col2:
    search_query = st.text_input("Search Applicant (Name, Application #, Email, ID)", placeholder="Type to search...")

apps_resp = api_client.list_applications(
    status=status_filter,
    search=search_query,
    admin_token=admin_token,
)
app_list = apps_resp.get("applications", [])

if app_list:
    df_apps = pd.DataFrame(app_list)
    st.dataframe(
        df_apps[["application_number", "name", "email", "id_type", "id_number", "risk_score", "risk_tier", "status", "created_at"]],
        use_container_width=True,
        hide_index=True
    )

    # Interactive Action Review Box
    st.markdown("#### ⚡ Quick Administrative Action")
    action_col1, action_col2, action_col3 = st.columns([1.5, 1.5, 1])

    app_options = {f"{a['application_number']} - {a['name']} ({a['status']})": a["id"] for a in app_list}
    selected_app_label = action_col1.selectbox("Select Application to Review", list(app_options.keys()))
    selected_app_id = app_options[selected_app_label]

    new_status = action_col2.selectbox("Set Decision Status", ["APPROVED", "REJECTED", "FLAGGED", "PENDING_REVIEW"])
    review_notes = st.text_input("Compliance Notes / Rationale", placeholder="e.g. Identity verified after visual check")

    if st.button("Apply Status Override"):
        try:
            update_res = api_client.update_application_status(
                selected_app_id,
                new_status,
                review_notes,
                admin_token=admin_token,
            )
            st.success(f"Application status updated to: {update_res['new_status']}")
            st.rerun()
        except Exception as e:
            st.error(f"Status update failed: {str(e)}")

else:
    st.info("No applications match the specified criteria.")

st.divider()

# Tabbed Deep-Dive: Explainability & Metrics
tab1, tab2 = st.tabs(["🧠 Global Explainable AI (SHAP)", "📈 Algorithm Benchmark Matrix"])

with tab1:
    st.markdown("##### Global Feature Importance in Fraud Detection")
    st.caption("Which behavioral and biometric variables contribute most heavily to flagging fraud across all records:")
    try:
        imp_data = api_client.get_feature_importance()
        imp_list = imp_data.get("feature_importance", [])
        if imp_list:
            df_imp = pd.DataFrame(imp_list)
            st.bar_chart(df_imp.set_index("label")["importance"])
    except Exception as e:
        st.write("Feature importance data currently unavailable.")

with tab2:
    st.markdown("##### Multi-Model Evaluation Matrix")
    try:
        models_meta = api_client.get_model_benchmarks()
        models_dict = models_meta.get("models", {})
        table_rows = []
        for m_name, m_stats in models_dict.items():
            table_rows.append({
                "Model Algorithm": m_name.replace("_", " ").title(),
                "ROC-AUC": f"{m_stats['roc_auc']:.4f}",
                "PR-AUC": f"{m_stats['pr_auc']:.4f}",
                "Precision": f"{m_stats['precision']:.4f}",
                "Recall": f"{m_stats['recall']:.4f}",
                "F1 Score": f"{m_stats['f1_score']:.4f}",
                "Accuracy": f"{m_stats['accuracy']:.4f}"
            })
        st.table(pd.DataFrame(table_rows))
    except Exception:
        st.write("Benchmark matrix currently unavailable.")

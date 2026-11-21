import os
import sys

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

import streamlit as st
from utils.api_client import api_client

st.set_page_config(page_title="Transaction Anomaly Check | AI KYC System", page_icon="💳", layout="wide")

# Custom CSS
css_path = os.path.join(os.path.dirname(__file__), "..", "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("💳 Transaction Anomaly & Behavior Detection")
st.caption("Evaluate financial transactions in real-time against applicant declared profiles to catch velocity spikes, structuring, and merchant anomalies.")

# Quick Presets
st.markdown("##### ⚡ Test Transaction Presets")
p1, p2, p3 = st.columns(3)

if "tx_data" not in st.session_state:
    st.session_state["tx_data"] = {
        "amount": 250.0,
        "type": "PAYMENT",
        "merchant": "Retail & Groceries",
        "income": 60000.0,
        "city": "Metropolis",
        "ip": "192.168.1.105"
    }

with p1:
    if st.button("🟢 Normal Retail Payment ($250)"):
        st.session_state["tx_data"] = {
            "amount": 250.0,
            "type": "PAYMENT",
            "merchant": "Retail & Groceries",
            "income": 60000.0,
            "city": "Metropolis",
            "ip": "192.168.1.105"
        }
        st.rerun()

with p2:
    if st.button("🟡 Structured Round Withdrawal ($10,000)"):
        st.session_state["tx_data"] = {
            "amount": 10000.0,
            "type": "WITHDRAWAL",
            "merchant": "ATM Network",
            "income": 50000.0,
            "city": "Metropolis",
            "ip": "192.168.1.50"
        }
        st.rerun()

with p3:
    if st.button("🔴 High-Risk Crypto Remittance ($45,000)"):
        st.session_state["tx_data"] = {
            "amount": 45000.0,
            "type": "TRANSFER",
            "merchant": "Crypto Exchange",
            "income": 40000.0,
            "city": "Proxy_Node",
            "ip": "185.220.101.5"
        }
        st.rerun()

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Transaction Parameters")
    amount = st.number_input("Transaction Amount ($)", value=float(st.session_state["tx_data"]["amount"]), min_value=1.0, step=100.0)
    tx_type = st.selectbox("Transaction Type", ["PAYMENT", "TRANSFER", "WITHDRAWAL"], index=["PAYMENT", "TRANSFER", "WITHDRAWAL"].index(st.session_state["tx_data"]["type"]))
    merchant = st.selectbox(
        "Merchant Category",
        ["Retail & Groceries", "General", "ATM Network", "Crypto Exchange", "Casino Gaming", "Offshore Remittance", "High Value Luxury"],
        index=0 if st.session_state["tx_data"]["merchant"] not in ["Retail & Groceries", "General", "ATM Network", "Crypto Exchange", "Casino Gaming", "Offshore Remittance", "High Value Luxury"] else ["Retail & Groceries", "General", "ATM Network", "Crypto Exchange", "Casino Gaming", "Offshore Remittance", "High Value Luxury"].index(st.session_state["tx_data"]["merchant"])
    )

with col2:
    st.subheader("Contextual & Network Signals")
    income = st.number_input("Applicant Declared Annual Income ($)", value=float(st.session_state["tx_data"]["income"]), step=5000.0)
    city = st.text_input("Origination City", value=st.session_state["tx_data"]["city"])
    ip = st.text_input("IP Address", value=st.session_state["tx_data"]["ip"])

st.divider()

if st.button("⚡ Run Real-Time Anomaly Analysis", type="primary"):
    with st.spinner("Analyzing transaction vectors..."):
        try:
            req_data = {
                "amount": float(amount),
                "currency": "USD",
                "transaction_type": tx_type,
                "merchant_category": merchant,
                "ip_address": ip,
                "location_city": city,
                "applicant_declared_income": float(income)
            }
            res = api_client.check_transaction(req_data)

            st.subheader("📊 Anomaly Assessment Findings")

            level = res["risk_level"]
            score = res["anomaly_score"]
            is_ano = res["is_anomalous"]

            badge_style = {
                "NORMAL": "badge-low",
                "SUSPICIOUS": "badge-medium",
                "SEVERE": "badge-critical"
            }.get(level, "badge-low")

            st.markdown(f"""
            <div class="kyc-card">
                <span class="{badge_style}" style="font-size: 1rem;">{level} TRANSACTION STATUS</span>
                <h3 style="margin-top: 10px;">Anomaly Probability Score: {score * 100:.0f}%</h3>
                <p style="color: #94a3b8;">Decision: <strong>{'FLAG FOR IMMEDIATE FREEZE / REVIEW' if is_ano else 'TRANSACTION CLEARED'}</strong></p>
            </div>
            """, unsafe_allow_html=True)

            if res["anomaly_reasons"]:
                st.markdown("##### 🚨 Triggered Anomaly Signals:")
                for reason in res["anomaly_reasons"]:
                    st.error(f"• {reason}")
            else:
                st.success("✅ No anomalous transaction signatures detected. Amount aligns with declared financial capacity.")

        except Exception as e:
            st.error(f"Transaction Engine Error: {str(e)}")

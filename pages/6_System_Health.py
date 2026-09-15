import streamlit as st
import os
from audit_log import load_all_audit_entries

# st.set_page_config(page_title="System Health", page_icon="📊", layout="wide")

st.title("📊 System Health & Analytics")
st.caption("Restricted access — for internal insurance organization use only")

# --- Password gate (same protection as Audit Trail) ---
if "system_health_authenticated" not in st.session_state:
    st.session_state["system_health_authenticated"] = False

if not st.session_state["system_health_authenticated"]:
    st.warning("This page is restricted to authorized insurance staff.")
    password = st.text_input("Enter access password", type="password", key="sh_password")
    if st.button("Access System Health"):
        correct_password = st.secrets.get("AUDIT_PASSWORD", os.getenv("AUDIT_PASSWORD", "admin123"))
        if password == correct_password:
            st.session_state["system_health_authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

# --- Authenticated view below this line ---

entries = load_all_audit_entries()

if not entries:
    st.info("No claims have been processed yet.")
    st.stop()

# --- Calculate metrics ---
total_claims = len(entries)
approved = len([e for e in entries if e.get("decision") == "APPROVED"])
escalated = len([e for e in entries if e.get("decision") == "ESCALATED"])
rejected = len([e for e in entries if e.get("decision") == "REJECTED"])
system_errors = len([e for e in entries if e.get("decision") == "SYSTEM_ERROR"])

high_fraud_risk = len([e for e in entries if e.get("fraud_risk") == "high"])
medium_fraud_risk = len([e for e in entries if e.get("fraud_risk") == "medium"])

# --- Top row: card layout with key numbers ---
st.markdown("### Overview")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Claims", total_claims)
with col2:
    st.metric("✅ Approved", approved)
with col3:
    st.metric("🔎 Escalated (awaiting human review)", escalated)
with col4:
    st.metric("❌ Rejected", rejected)
with col5:
    st.metric("⚠️ System Errors", system_errors)

st.markdown("---")

# --- Second row: rates and fraud signals ---
st.markdown("### Key Rates")
col6, col7, col8 = st.columns(3)

successful_claims = total_claims - system_errors
approval_rate = (approved / successful_claims * 100) if successful_claims else 0
escalation_rate = (escalated / successful_claims * 100) if successful_claims else 0
rejection_rate = (rejected / successful_claims * 100) if successful_claims else 0

with col6:
    st.metric("Approval Rate", f"{approval_rate:.1f}%")
with col7:
    st.metric("Escalation Rate", f"{escalation_rate:.1f}%")
with col8:
    st.metric("Rejection Rate", f"{rejection_rate:.1f}%")

st.markdown("---")

# --- Fraud risk signals ---
st.markdown("### Fraud Risk Signals")
col9, col10 = st.columns(2)
with col9:
    st.metric("🚩 High Fraud Risk Claims", high_fraud_risk)
with col10:
    st.metric("🟠 Medium Fraud Risk Claims", medium_fraud_risk)

if high_fraud_risk > 0:
    st.error(f"{high_fraud_risk} claim(s) flagged as high fraud risk — recommend priority review.")

st.markdown("---")

# --- Claims awaiting human review — actionable list ---
st.markdown("### 🔎 Claims Awaiting Human Review")
pending_claims = [e for e in entries if e.get("decision") == "ESCALATED"]

if not pending_claims:
    st.success("No claims currently awaiting review.")
else:
    for entry in pending_claims:
        with st.expander(f"**{entry['claim_id']}** — {entry.get('logged_at', '')[:19]}"):
            st.write(f"**Policy ID:** {entry.get('policy_id')}")
            st.write(f"**Estimated cost range:** {entry.get('estimated_cost_range')}")
            st.write(f"**Fraud risk:** {entry.get('fraud_risk')}")
            st.write("**Reasons for escalation:**")
            for r in entry.get("reasons", []):
                st.write(f"- {r}")
import streamlit as st
import os
import json
from audit_log import load_all_audit_entries, verify_chain_integrity

# st.set_page_config(page_title="Audit Trail", page_icon="🔒", layout="wide")

st.title("🔒 Audit Trail")
st.caption("Restricted access — for internal insurance organization use only")

if "audit_authenticated" not in st.session_state:
    st.session_state["audit_authenticated"] = False

if not st.session_state["audit_authenticated"]:
    st.warning("This page is restricted to authorized insurance staff.")
    password = st.text_input("Enter access password", type="password")
    if st.button("Access Audit Trail"):
        correct_password = st.secrets.get("AUDIT_PASSWORD", os.getenv("AUDIT_PASSWORD", "admin123"))
        if password == correct_password:
            st.session_state["audit_authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

integrity_ok = verify_chain_integrity()
if integrity_ok:
    st.success("✅ Audit log integrity verified — no tampering detected.")
else:
    st.error("⚠️ Audit log integrity check FAILED — entries may have been altered.")

entries = load_all_audit_entries()

if not entries:
    st.info("No claims have been processed yet.")
else:
    st.write(f"**Total claims logged:** {len(entries)}")
    st.markdown("---")

    for entry in reversed(entries):
        decision = entry.get("decision", "UNKNOWN")
        color = {"APPROVED": "green", "ESCALATED": "orange", "REJECTED": "red"}.get(decision, "gray")

        with st.expander(f"**{entry['claim_id']}** — :{color}[{decision}] — {entry.get('logged_at', '')[:19]}"):
            st.write(f"**Policy ID:** {entry.get('policy_id')}")
            st.write(f"**Verification status:** {entry.get('verification_status')}")
            st.write(f"**Documents submitted:** {', '.join(entry.get('documents_submitted', []))}")
            st.write(f"**Damaged parts:** {entry.get('damaged_parts')}")
            st.write(f"**Estimated cost range:** {entry.get('estimated_cost_range')}")
            st.write(f"**Fraud risk:** {entry.get('fraud_risk')}")
            st.write("**Decision reasons:**")
            for r in entry.get("reasons", []):
                st.write(f"- {r}")

            claim_json_path = os.path.join("claims", entry["claim_id"], "claim_record.json")
            if os.path.exists(claim_json_path):
                if st.button(f"View full report for {entry['claim_id']}", key=f"btn_{entry['claim_id']}"):
                    with open(claim_json_path, "r") as f:
                        full_record = json.load(f)
                    st.json(full_record)
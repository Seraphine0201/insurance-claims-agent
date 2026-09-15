import streamlit as st
import os
import json

# st.set_page_config(page_title="Track My Claim", page_icon="🔍", layout="wide")

st.title("🔍 Track My Claim")
st.caption("Enter your Claim ID to check the current status of your claim.")

claim_id_input = st.text_input("Claim ID", placeholder="e.g. CLAIM_00004")

if st.button("Check Status", type="primary"):
    if not claim_id_input.strip():
        st.error("Please enter a Claim ID.")
    else:
        claim_id_clean = claim_id_input.strip().upper()
        record_path = os.path.join("claims", claim_id_clean, "claim_record.json")

        if not os.path.exists(record_path):
            st.error(f"No claim found with ID '{claim_id_clean}'. Please double-check your Claim ID.")
        else:
            with open(record_path, "r") as f:
                record = json.load(f)

            decision_result = record.get("decision_result", {}) or {}
            decision = decision_result.get("decision", "UNKNOWN")

            status_display = {
                "APPROVED": ("✅ Approved", "green"),
                "ESCALATED": ("🔎 Under Review", "orange"),
                "REJECTED": ("❌ Rejected", "red"),
                "SYSTEM_ERROR": ("⚠️ Processing Issue", "gray"),
            }
            label, color = status_display.get(decision, ("Unknown", "gray"))

            st.markdown("---")
            st.subheader(f"Claim ID: {claim_id_clean}")
            st.markdown(f"### Status: :{color}[{label}]")

            if decision == "APPROVED":
                st.success(
                    "Your claim has been approved. The estimated payout is being processed."
                )
            elif decision == "ESCALATED":
                st.info(
                    "Your claim requires additional review by our team (for example, "
                    "damage cost verification or a licensed surveyor assessment). "
                    "We will contact you with updates."
                )
            elif decision == "REJECTED":
                st.warning(
                    "Your claim could not be approved at this time. Please contact "
                    "our support team for more details."
                )
            elif decision == "SYSTEM_ERROR":
                st.warning(
                    "There was a temporary issue processing your claim. Please try "
                    "resubmitting, or contact support if this continues."
                )

            st.caption(f"Last updated: {record.get('processed_at', 'N/A')[:19]}")
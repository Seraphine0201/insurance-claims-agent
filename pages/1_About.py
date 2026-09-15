import streamlit as st

# st.set_page_config(page_title="About", page_icon="ℹ️", layout="wide")

st.title("ℹ️ About This System")

st.markdown("""
### Third-Party Insurance Claims Triage System

This platform uses a coordinated team of five specialized AI agents to process
third-party motor insurance claims — from document upload to a final,
explainable decision.

#### How it works
1. **Intake** — reads uploaded documents (FIR, licence, PAN, Aadhaar, RC) using OCR and AI
2. **Verification** — checks the policy database, licence validity, and identity consistency
3. **Assessment** — analyzes damage photos and estimates repair cost
4. **Fraud Check** — cross-references claim history for suspicious patterns
5. **Decision** — combines everything into a final, reasoned outcome

#### Built-in safeguards
- Claims above ₹50,000 are always escalated to a licensed surveyor, per IRDAI regulation
- Low-confidence photo assessments are never auto-approved
- A policyholder's traffic violation never blocks an innocent third party's payout
- Every decision is logged in a tamper-evident audit trail

#### Disclaimer
This is a demonstration system built for portfolio purposes. It is not
connected to a live insurance provider, and no real claims are processed
or paid out through this platform.
""")
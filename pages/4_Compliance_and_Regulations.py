import streamlit as st

# st.set_page_config(page_title="Compliance & Regulations", page_icon="⚖️", layout="wide")

st.title("⚖️ Compliance & Regulations")
st.caption("This system is designed around real Indian motor insurance regulations, "
           "administered by the Insurance Regulatory and Development Authority of India (IRDAI).")

st.markdown("---")

st.subheader("The ₹50,000 Surveyor Threshold")
st.write(
    "Under IRDAI regulations, claims estimated **below ₹50,000** may be assessed "
    "using app-based or AI-driven tools, without requiring a licensed surveyor. "
    "Claims estimated at **₹50,000 or above** legally require a licensed surveyor "
    "to be assigned — their report, not an automated estimate or the claimant's "
    "photos alone, determines the final payout."
)
st.info(
    "This system automatically escalates any claim meeting or exceeding this "
    "threshold. It never issues a final automated approval above ₹50,000."
)

st.markdown("---")

st.subheader("Third-Party Cover is Mandatory")
st.write(
    "Third-party motor insurance is legally mandatory in India. It exists "
    "specifically to protect people and property that a policyholder may "
    "damage or injure — not the policyholder's own vehicle. A third party "
    "does not need their own insurance policy to be compensated; they claim "
    "directly against the at-fault driver's policy."
)

st.markdown("---")

st.subheader("'Pay and Recover' Principle")
st.write(
    "If the at-fault driver was found to have an invalid licence, or was in "
    "violation of traffic law (for example, drunk driving) at the time of the "
    "incident, this does **not** block the innocent third party's compensation. "
    "The insurer is expected to pay the third party first, and separately "
    "pursue recovery of costs from the policyholder afterward."
)

st.markdown("---")

st.subheader("Auditability & Recordkeeping")
st.write(
    "Every claim processed through this system — every document reviewed, "
    "every check performed, and every decision made — is recorded in a "
    "permanent, append-only audit log. Entries cannot be edited or deleted "
    "by anyone, including system administrators, ensuring a reliable record "
    "for regulatory review."
)

st.markdown("---")

st.subheader("Disclaimer")
st.write(
    "This platform is a demonstration system built to illustrate how AI-assisted "
    "claims triage can operate within real regulatory constraints. It is not "
    "affiliated with, or a live deployment for, any licensed insurance provider. "
    "Regulations referenced here reflect general IRDAI motor insurance rules and "
    "should not be relied upon as legal or financial advice."
)
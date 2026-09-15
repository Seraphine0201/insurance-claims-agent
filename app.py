import streamlit as st

st.set_page_config(page_title="Third-Party Claims Triage", page_icon="🚗", layout="wide")

process_claim_page = st.Page("streamlit_app.py", title="Process Claim", icon="🚗", default=True)
about_page = st.Page("pages/1_About.py", title="About", icon="ℹ️")
track_my_claim_page = st.Page("pages/2_Track_My_Claim.py", title="Track My Claim", icon="🔍")
faq_page = st.Page("pages/3_FAQ.py", title="FAQ", icon="❓")
compliance_and_regulations_page = st.Page("pages/4_Compliance_and_Regulations.py", title="Compliance and Regulations", icon="⚖️")
contact_page = st.Page("pages/5_Contact.py", title="Contact", icon="📞")
system_health_page = st.Page("pages/6_System_Health.py", title="System_Health", icon="📊")
audit_page = st.Page("pages/7_Audit.py", title="Audit Trail", icon="🔒")



pg = st.navigation({
    "Claim Hub": [
        process_claim_page,
        about_page,
        track_my_claim_page,
        faq_page,
        compliance_and_regulations_page,
        contact_page,
        system_health_page,
        audit_page,
    ]
})

pg.run()
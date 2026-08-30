import streamlit as st
import os
import shutil
import tempfile
from orchestrator import process_claim

REQUIRED_DOCUMENT_KEYWORDS = {
    "licence": "Driving Licence",
    "license": "Driving Licence",
    "pan": "PAN Card",
    "aadhaar": "Aadhaar Card",
    "aadhar": "Aadhaar Card",
    "rc": "Registration Certificate (RC)",
    "fir": "FIR",
}


def get_missing_documents(doc_files):
    """
    Check that all 5 required document types are present among the
    uploaded files (matched by filename keyword). Returns a list of
    missing document display names, or an empty list if all are present.
    """
    uploaded_names = [f.name.lower() for f in doc_files]

    found_types = set()
    for name in uploaded_names:
        for keyword, display_name in REQUIRED_DOCUMENT_KEYWORDS.items():
            if keyword in name:
                found_types.add(display_name)

    required_types = {"Driving Licence", "PAN Card", "Aadhaar Card", "Registration Certificate (RC)", "FIR"}
    missing = required_types - found_types
    return sorted(missing)

st.set_page_config(page_title="Third-Party Claims Triage", layout="wide")

st.title("🚗 Third-Party Insurance Claims Triage System")
st.caption("Multi-agent AI system — upload policyholder documents and damage photos to process a claim")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Policyholder Documents")
    st.caption("Upload: Driving Licence, PAN Card, Aadhaar Card, RC, and FIR")
    doc_files = st.file_uploader(
        "Upload documents",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="docs"
    )
    if doc_files:
        st.write("**Preview:**")
        preview_cols = st.columns(3)
        for i, f in enumerate(doc_files):
            with preview_cols[i % 3]:
                st.image(f, caption=f.name, use_container_width=True)
            

with col2:
    st.subheader("📸 Damage Photos")
    st.caption("Upload one or more photos of the third-party vehicle's damage")
    photo_files = st.file_uploader(
        "Upload damage photos",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="photos"
    )
    if photo_files:
        st.write("**Preview:**")
        preview_cols = st.columns(3)
        for i, f in enumerate(photo_files):
            with preview_cols[i % 3]:
                st.image(f, caption=f.name, use_container_width=True)

st.markdown("---")

if st.button("🔍 Process Claim", type="primary", use_container_width=True):
    missing_docs = get_missing_documents(doc_files) if doc_files else list(dict.fromkeys(REQUIRED_DOCUMENT_KEYWORDS.values()))

    if missing_docs:
        st.error(
            "Please upload all required documents. Missing: " + ", ".join(missing_docs)
        )
    elif not photo_files:
        st.error("Please upload at least one damage photo.")
    else:
        with st.spinner("Processing claim — running Intake, Verification, Assessment, Fraud, and Decision agents..."):
            # Save uploaded files to temporary folders, since our agents
            # work with file paths, not in-memory upload objects
            temp_dir = tempfile.mkdtemp()
            docs_folder = os.path.join(temp_dir, "input_docs")
            photos_folder = os.path.join(temp_dir, "input_photos")
            os.makedirs(docs_folder, exist_ok=True)
            os.makedirs(photos_folder, exist_ok=True)

            for f in doc_files:
                with open(os.path.join(docs_folder, f.name), "wb") as out:
                    out.write(f.getbuffer())

            for f in photo_files:
                with open(os.path.join(photos_folder, f.name), "wb") as out:
                    out.write(f.getbuffer())

            try:
                claim_record = process_claim(docs_folder, photos_folder)
                st.session_state["claim_record"] = claim_record
            except Exception as e:
                import sys, traceback
                print("UNEXPECTED ERROR:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                st.error(
                     "⚠️ Something went wrong while processing your claim. "
                     "Please try again, or contact support if this continues."
                )
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

if "claim_record" in st.session_state:
    record = st.session_state["claim_record"]
    decision = record["decision_result"]

    st.markdown("---")
    st.header(f"Claim ID: {record['claim_id']}")


    if decision["decision"] == "SYSTEM_ERROR":
        st.warning("⚠️ System is currently under maintenance. Please try again after some time.")
        for reason in decision["reasons"]:
            st.caption(reason)
        st.stop()   # ← stops execution here, so nothing below (tabs) ever runs

    

    decision_color = {
        "APPROVED": "green",
        "ESCALATED": "orange",
        "REJECTED": "red"
    }.get(decision["decision"], "gray")

    st.markdown(f"### Decision: :{decision_color}[{decision['decision']}]")

    st.subheader("Reasoning")
    for reason in decision["reasons"]:
        st.write(f"- {reason}")

    tab1, tab2, tab3, tab4 = st.tabs(["📄 Verification", "📸 Assessment", "🔍 Fraud Check", "📋 Full Record"])

    with tab1:
        v = record["verification_result"]
        st.write(f"**Matched Policy:** {v.get('policy_id')} (match confidence: {v.get('vehicle_match_confidence')}%)")
        st.write(f"**Policy valid on incident date:** {v.get('policy_valid')}")
        st.write(f"**Licence valid:** {v.get('licence_valid_on_incident_date')}")
        st.write(f"**Identity mismatches:** {v.get('identity_mismatches') or 'None'}")
        violation = v.get("violation_check", {})
        st.write(f"**Traffic violation:** {violation.get('violation_type') or 'None'}")
        st.write(f"**Status:** {v.get('verification_status')} — {v.get('reason')}")

    with tab2:
        a = record["assessment_result"]
        st.write(f"**Confidence:** {a.get('confidence')}")
        st.write(f"**Damaged parts:** {a.get('damaged_parts')}")
        st.write(f"**Estimated cost:** ₹{a['cost_estimate']['total_min']:,} – ₹{a['cost_estimate']['total_max']:,}")
        st.write(f"**Requires surveyor (>₹{a.get('surveyor_threshold'):,}):** {a.get('exceeds_surveyor_threshold')}")

    with tab3:
        fr = record["fraud_result"]
        poi = fr.get("point_of_impact_check", {})
        st.write(f"**Point of impact consistent:** {poi.get('consistent')} (match score: {poi.get('match_score')})")
        hist = fr.get("claim_history_check", {})
        st.write(f"**Claim history flags:** {hist.get('flags') or 'None'}")
        st.write(f"**Overall fraud risk:** {fr.get('overall_fraud_risk')}")

    with tab4:
        st.json(record)
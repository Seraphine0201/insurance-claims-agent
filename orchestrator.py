import os
import json
import glob
from datetime import datetime

from agents.intake_agent import process_document
from agents.verification_agent import verify_claim
from agents.assessment_agent import assess_damage
from agents.fraud_agent import run_fraud_check
from agents.decision_agent import make_decision
from audit_log import append_audit_entry

CLAIMS_FOLDER = "claims"
os.makedirs(CLAIMS_FOLDER, exist_ok=True)

# Maps a document filename keyword to the document_type label the Intake Agent expects
DOCUMENT_TYPE_HINTS = {
    "licence": "driving_licence",
    "license": "driving_licence",
    "pan": "pan_card",
    "aadhaar": "aadhaar_card",
    "aadhar": "aadhaar_card",
    "rc": "registration_certificate",
    "fir": "fir",
}


def generate_claim_id():
    """Look at existing claim folders and generate the next sequential ID,
    based on the highest number seen so far — not just a count, so it works
    correctly even if earlier claim folders were deleted."""
    existing = glob.glob(os.path.join(CLAIMS_FOLDER, "CLAIM_*"))
    highest_number = 0
    for folder_path in existing:
        folder_name = os.path.basename(folder_path)
        try:
            number = int(folder_name.replace("CLAIM_", ""))
            highest_number = max(highest_number, number)
        except ValueError:
            continue
    return f"CLAIM_{highest_number + 1:05d}"

def guess_document_type(filename):
    """Figure out what kind of document this is, based on its filename."""
    lower_name = filename.lower()
    for keyword, doc_type in DOCUMENT_TYPE_HINTS.items():
        if keyword in lower_name:
            return doc_type
    return "unknown_document"


def _system_error_record(claim_id, claim_folder, intake_results, reason):
    """Build and save a SYSTEM_ERROR claim record — used whenever a backend
    failure (e.g. API quota) happens, so it never gets confused with a real
    APPROVED/ESCALATED/REJECTED business decision."""
    decision_result = {
        "decision": "SYSTEM_ERROR",
        "reasons": [reason],
        "requires_surveyor": False,
        "recovery_from_policyholder": False,
    }
    claim_record = {
        "claim_id": claim_id,
        "processed_at": datetime.now().isoformat(),
        "intake_results": intake_results,
        "verification_result": None,
        "assessment_result": None,
        "fraud_result": None,
        "decision_result": decision_result,
    }
    record_path = os.path.join(claim_folder, "claim_record.json")
    with open(record_path, "w") as f:
        json.dump(claim_record, f, indent=2)
    print(f"Claim {claim_id}: SYSTEM_ERROR — {reason}")
    append_audit_entry(claim_record)
    return claim_record

def process_claim(input_docs_folder, input_photos_folder):
    """
    Full orchestration pipeline for one claim:
    Intake (all docs) -> Verification -> Assessment (all photos) -> Fraud -> Decision
    Returns the complete claim record and saves it to disk.
    """
    claim_id = generate_claim_id()
    claim_folder = os.path.join(CLAIMS_FOLDER, claim_id)
    os.makedirs(claim_folder, exist_ok=False)

    print(f"Processing new claim: {claim_id}")

    # --- Step 1: Intake — process every document in input_docs_folder ---
    intake_results = {}
    doc_files = [f for f in os.listdir(input_docs_folder)
                 if f.lower().endswith((".png", ".jpg", ".jpeg"))]

    for filename in doc_files:
        doc_path = os.path.join(input_docs_folder, filename)
        doc_type = guess_document_type(filename)
        print(f"  Intake: {filename} (detected as {doc_type})")
        result = process_document(doc_path, doc_type)
        intake_results[doc_type] = result["structured_data"]

    # Check if any document failed to process (e.g. due to API quota issues).
    # This is a SYSTEM problem, not a real claim decision — never let it
    # produce a misleading REJECTED/APPROVED outcome.
    failed_docs = [doc_type for doc_type, data in intake_results.items() if data.get("error")]
    if failed_docs:
        return _system_error_record(
            claim_id, claim_folder, intake_results,
            "Your documents could not be processed due to a "
            "temporary system issue. This is not a decision on your claim — "
            "please try again shortly."
        )

    fir_data = intake_results.get("fir")
    if not fir_data:
        raise ValueError("No FIR document found among uploaded documents — cannot proceed without an FIR.")
    
    # --- Step 2: Verification ---
    print("  Running Verification Agent...")
    verification_result = verify_claim(
        fir_data=fir_data,
        intake_results=intake_results,
        incident_date_str=fir_data.get("incident_date")
    )
    policy_id = verification_result.get("policy_id")

    # --- Step 3: Assessment — process every damage photo ---
    photo_files = [f for f in os.listdir(input_photos_folder)
                   if f.lower().endswith((".png", ".jpg", ".jpeg"))]

    all_damaged_parts = []
    assessment_results_per_photo = {}

    for filename in photo_files:
        photo_path = os.path.join(input_photos_folder, filename)
        print(f"  Assessment: {filename}")
        result = assess_damage(photo_path)
        assessment_results_per_photo[filename] = result
        all_damaged_parts.extend(result.get("damaged_parts", []))


    # Check if any damage photo failed to process (same reasoning as documents above)
    failed_photos = [fn for fn, r in assessment_results_per_photo.items() if r.get("error")]
    if failed_photos:
        # Merge intake_results in too, so the record shows what DID succeed
        intake_results["_assessment_results_per_photo"] = assessment_results_per_photo
        return _system_error_record(
            claim_id, claim_folder, intake_results,
            "Your damage photos could not be processed due to a "
            "temporary system issue. This is not a decision on your claim — "
            "please try again shortly."
        )

    # Combine cost estimates across all photos into one overall assessment
    combined_cost_min = sum(r["cost_estimate"]["total_min"] for r in assessment_results_per_photo.values())
    combined_cost_max = sum(r["cost_estimate"]["total_max"] for r in assessment_results_per_photo.values())
    worst_confidence = "high"
    for r in assessment_results_per_photo.values():
        if r["confidence"] == "low":
            worst_confidence = "low"
        elif r["confidence"] == "medium" and worst_confidence != "low":
            worst_confidence = "medium"

    combined_assessment_result = {
        "damaged_parts": all_damaged_parts,
        "confidence": worst_confidence,
        "cost_estimate": {"total_min": combined_cost_min, "total_max": combined_cost_max},
        "exceeds_surveyor_threshold": combined_cost_max >= 50000,
        "surveyor_threshold": 50000,
        "per_photo_results": assessment_results_per_photo,
    }

    # --- Step 4: Fraud check ---
    print("  Running Fraud Agent...")
    fraud_result = run_fraud_check(
        fir_data=fir_data,
        assessment_result=combined_assessment_result,
        policy_id=policy_id
    )

    # --- Step 5: Decision ---
    print("  Running Decision Agent...")
    decision_result = make_decision(verification_result, combined_assessment_result, fraud_result)

    # --- Combine everything into one claim record ---
    claim_record = {
        "claim_id": claim_id,
        "processed_at": datetime.now().isoformat(),
        "intake_results": intake_results,
        "verification_result": verification_result,
        "assessment_result": combined_assessment_result,
        "fraud_result": fraud_result,
        "decision_result": decision_result,
    }

    # Save to disk
    record_path = os.path.join(claim_folder, "claim_record.json")
    with open(record_path, "w") as f:
        json.dump(claim_record, f, indent=2)

    print(f"Claim {claim_id} processed. Decision: {decision_result['decision']}")
    print(f"Full record saved to: {record_path}")

    append_audit_entry(claim_record)

    return claim_record
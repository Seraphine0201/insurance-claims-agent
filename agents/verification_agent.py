import json
from datetime import datetime
from rapidfuzz import fuzz


def load_policies(filepath = "data/mock_policies.json"):
    """Load the mock insurer policy database from disk."""
    with open(filepath, "r") as f:
       return json.load(f)


def find_policy_by_vehicle(vehicle_number, policies, similarity_threshold=80):
    """
    Find a policy matching the at-fault vehicle number from the FIR.
    Uses fuzzy matching to tolerate OCR misreads (e.g., '0 read as '@' or 'O').
    Returns the best match if similarity is above the threshold.
    """
    if not vehicle_number:
        return None, None, 0

    best_match_id = None
    best_match_details = None
    best_score = 0

    for policy_id, details in policies.items():
        score = fuzz.ratio(vehicle_number.upper(), details["vehicle_number"].upper())
        if score > best_score:
            best_score = score
            best_match_id = policy_id
            best_match_details = details

    if best_score >= similarity_threshold:
        return best_match_id, best_match_details, best_score
    else:
        return None, None, best_score
          

def check_policy_validity(policy_details, incident_date_str):
    """Check if the incident date falls within the policy's active window."""
    incident_date = datetime.strptime(incident_date_str, "%d-%m-%Y")
    start_date = datetime.strptime(policy_details["policy_start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(policy_details["policy_end_date"], "%Y-%m-%d")
    return start_date <= incident_date <= end_date


def check_licence_validity(policy_details, licence_date_str):
    """Check if the driver's licence was valid on the incident date."""
    incident_date = datetime.strptime(licence_date_str, "%d-%m-%Y")
    expiry_date = datetime.strptime(policy_details["licence_expiry"], "%Y-%m-%d")
    return policy_details["licence_valid"] and (incident_date <= expiry_date)


def check_identity_consistency(intake_results, policy_details, similarity_threshold=80):
    """
    Compare name/licence number extracted from documents (Intake Agent Output)
    against what's on record in the policy database. Uses fuzzy matching to
    tolerate OCR misreads, consistent with vehicle number check.
    """
    mismatches = []

    for doc_type, data in intake_results.items():
        extracted_name = data.get("name")
        extracted_licence = data.get("license_number") or data.get("licence_number")

        if extracted_name:
            name_score = fuzz.ratio(extracted_name.strip().lower(), policy_details["policyholder_name"].strip().lower())
            if name_score < similarity_threshold:
                mismatches.append(
                    f"{doc_type}: name '{extracted_name}' does not sufficientlymatch policy record "
                    f"'{policy_details['policyholder_name']}' (similarity {name_score})"
                )

        if extracted_licence:
            licence_score = fuzz.ratio(extracted_licence.strip().upper(), policy_details["licence_number"].strip().upper())
            if licence_score < similarity_threshold:
                mismatches.append(
                    f"{doc_type}: licence number '{extracted_licence}' does not sufficiently match policy record "
                    f"'{policy_details['licence_number']}' (similarity {licence_score})"
                )        
        

    return mismatches


def verify_claim(fir_data, intake_results, incident_date_str):
    """
    Full verification pipeline.
    fir_data: structured data extracted from the FIR document
    intake_results: dict of {document_type: structured_data} for all uploaded docs
    incident_date_str: date of the accident, format DD-MM-YYYY
    """
    policies = load_policies()

    at_fault_vehicle = fir_data.get("vehicle_number")
    policy_id, policy_details, match_score = find_policy_by_vehicle(at_fault_vehicle, policies)

    if not policy_details:
        return {
            "verification_status": "REJECTED",
            "reason": f"No policy found for vehicle number {at_fault_vehicle} (best match score: {match_score})"
        }

    policy_valid = check_policy_validity(policy_details, incident_date_str)
    licence_valid = check_licence_validity(policy_details, incident_date_str)
    identity_mismatches = check_identity_consistency(intake_results, policy_details)
    violation_check = check_traffic_violations(fir_data.get("violation_noted"))

    result = {
        "policy_id": policy_id,
        "vehicle_match_confidence": match_score,
        "policy_valid": policy_valid,
        "licence_valid_on_incident_date": licence_valid,
        "identity_mismatches": identity_mismatches,
        "violation_check": violation_check,
    }

    if not policy_valid:
        result["verification_status"] = "REJECTED"
        result["reason"] = "Policy was not active on the incident date"
    elif identity_mismatches:
        result["verification_status"] = "ESCALATE"
        result["reason"] = "Identity/document mismatches found — needs human review"
    elif not licence_valid:
        result["verification_status"] = "ESCALATE"
        result["reason"] = "Driver licence invalid — route to pay-and-recover process"
        result["recovery_from_policyholder"] = True
    else:
        result["verification_status"] = "PASS"
        result["reason"] = "All checks passed"

    return result


def check_traffic_violations(violation_noted):
    """
    Check if the FIR records a traffic violation by the policyholder
    (e.g. drunk driving, wrong side driving). Per real insurance practice,
    a violation does NOT block the third party's payout - the insurer still
    pays the injured third party first, then may recover costs from the 
    policyholder or deny the policyholder's own coverage seperately.
    """
    if not violation_noted or violation_noted.strip().lower() in ("none", "no violation", "null"):
        return {"violation_found": False, "violation_type": None}

    return {
        "violation_found": True,
        "violation_type": violation_noted.strip(),
        "note": "Traffic violation recorded - third-party payout still proceeds, "
                "but flag for policyholder-side recovery/investigation"
    }
import json
import os


def generate_audit_report(claim_id):
    """
    Load a claim's full record and generate a clean, human-readable
    audit report — showing exactly what data was seen, which checks
    passed/failed, and why the final decision was made.
    """
    record_path = os.path.join("claims", claim_id, "claim_record.json")

    if not os.path.exists(record_path):
        return f"No claim record found for {claim_id}"

    with open(record_path, "r") as f:
        record = json.load(f)

    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"AUDIT TRAIL — {record['claim_id']}")
    lines.append(f"Processed at: {record['processed_at']}")
    lines.append(f"{'='*60}")

    # --- Section 1: What documents were seen ---
    lines.append("\n--- DOCUMENTS PROCESSED ---")
    for doc_type, data in record["intake_results"].items():
        confidence = data.get("raw_text_confidence", "unknown")
        lines.append(f"  [{doc_type}] extracted with confidence: {confidence}")
        if data.get("error"):
            lines.append(f"    ⚠ ERROR: {data['error']}")

    # --- Section 2: Verification checks ---
    v = record["verification_result"]
    lines.append("\n--- VERIFICATION CHECKS ---")
    lines.append(f"  Matched policy: {v.get('policy_id')} (vehicle match confidence: {v.get('vehicle_match_confidence')}%)")
    lines.append(f"  Policy valid on incident date: {v.get('policy_valid')}")
    lines.append(f"  Licence valid on incident date: {v.get('licence_valid_on_incident_date')}")
    lines.append(f"  Identity mismatches: {v.get('identity_mismatches') or 'None'}")
    violation = v.get("violation_check", {})
    lines.append(f"  Traffic violation: {violation.get('violation_type') or 'None'}")
    lines.append(f"  Verification status: {v.get('verification_status')} — {v.get('reason')}")

    # --- Section 3: Damage assessment ---
    a = record["assessment_result"]
    lines.append("\n--- DAMAGE ASSESSMENT ---")
    lines.append(f"  Overall confidence: {a.get('confidence')}")
    lines.append(f"  Damaged parts identified: {a.get('damaged_parts')}")
    lines.append(f"  Estimated cost range: ₹{a['cost_estimate']['total_min']:,} - ₹{a['cost_estimate']['total_max']:,}")
    lines.append(f"  Exceeds ₹{a.get('surveyor_threshold'):,} surveyor threshold: {a.get('exceeds_surveyor_threshold')}")

    # --- Section 4: Fraud check ---
    fr = record["fraud_result"]
    lines.append("\n--- FRAUD CHECK ---")
    poi = fr.get("point_of_impact_check", {})
    lines.append(f"  Point of impact consistent with FIR: {poi.get('consistent')} (match score: {poi.get('match_score')})")
    hist = fr.get("claim_history_check", {})
    lines.append(f"  Claim history flags: {hist.get('flags') or 'None'}")
    lines.append(f"  Overall fraud risk: {fr.get('overall_fraud_risk')}")

    # --- Section 5: Final decision ---
    d = record["decision_result"]
    lines.append("\n--- FINAL DECISION ---")
    lines.append(f"  DECISION: {d.get('decision')}")
    lines.append(f"  Requires surveyor: {d.get('requires_surveyor')}")
    lines.append(f"  Recovery from policyholder: {d.get('recovery_from_policyholder')}")
    lines.append("  Reasons:")
    for reason in d.get("reasons", []):
        lines.append(f"    - {reason}")

    lines.append(f"\n{'='*60}")

    report_text = "\n".join(lines)

    # Save the report alongside the claim record
    report_path = os.path.join("claims", claim_id, "audit_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    return report_text
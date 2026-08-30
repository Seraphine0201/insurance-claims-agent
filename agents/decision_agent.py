def make_decision(verification_result, assessment_result, fraud_result):
    """
    Final decision pipeline. Combines outputs from Verification, Assessment,
    and Fraud agents into one outcome: APPROVED, ESCALATED, or REJECTED.

    Every decision includes a list of reasons — this is the audit trail's
    raw material, so every outcome is explainable, not a black box.
    """
    reasons = []

    # --- 1. Verification-level hard stops ---
    if verification_result["verification_status"] == "REJECTED":
        return {
            "decision": "REJECTED",
            "reasons": [verification_result["reason"]],
            "requires_surveyor": False,
            "recovery_from_policyholder": False,
        }

    if verification_result["verification_status"] == "ESCALATE":
        reasons.append(f"Verification flagged for review: {verification_result['reason']}")

    # --- 2. Licence / recovery flag (does not block payout) ---
    recovery_from_policyholder = False
    violation_check = verification_result.get("violation_check", {})
    if violation_check.get("violation_found"):
        recovery_from_policyholder = True
        reasons.append(
            f"Traffic violation noted ({violation_check.get('violation_type')}) — "
            f"third-party payout proceeds, cost recovery flagged against policyholder"
        )

    # --- 3. Assessment-level checks ---
    requires_surveyor = assessment_result.get("exceeds_surveyor_threshold", False)
    if requires_surveyor:
        reasons.append(
            f"Estimated cost (up to ₹{assessment_result['cost_estimate']['total_max']:,}) "
            f"meets or exceeds ₹{assessment_result['surveyor_threshold']:,} — "
            f"licensed surveyor assignment legally required per IRDAI rules"
        )

    assessment_confidence = assessment_result.get("confidence", "low")
    if assessment_confidence == "low":
        reasons.append("Damage assessment confidence is low — photo quality insufficient for automated decisioning")

    # --- 4. Fraud-level checks ---
    fraud_risk = fraud_result.get("overall_fraud_risk", "low")
    if fraud_risk == "high":
        reasons.append("High fraud risk detected — claim history shows suspicious pattern")
    elif fraud_risk == "medium":
        reasons.append("Medium fraud risk — point of impact inconsistency detected, needs review")

    # --- 5. Final decision logic ---
    if requires_surveyor:
        decision = "ESCALATED"
    elif fraud_risk == "high":
        decision = "ESCALATED"
    elif assessment_confidence == "low":
        decision = "ESCALATED"
    elif verification_result["verification_status"] == "ESCALATE":
        decision = "ESCALATED"
    elif fraud_risk == "medium":
        decision = "ESCALATED"
    else:
        decision = "APPROVED"
        reasons.append("All checks passed — eligible for automatic settlement")

    return {
        "decision": decision,
        "reasons": reasons,
        "requires_surveyor": requires_surveyor,
        "recovery_from_policyholder": recovery_from_policyholder,
        "estimated_payout_range": assessment_result.get("cost_estimate", {}),
    }
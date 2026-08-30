from agents.decision_agent import make_decision

# Each test case: a synthetic scenario + what decision we EXPECT (our manual judgment)
TEST_SCENARIOS = [
    {
        "name": "Clean approval — everything passes, low cost",
        "verification_result": {
            "verification_status": "PASS",
            "reason": "All checks passed",
            "policy_id": "POL10005",
            "violation_check": {"violation_found": False, "violation_type": None},
        },
        "assessment_result": {
            "confidence": "high",
            "exceeds_surveyor_threshold": False,
            "surveyor_threshold": 50000,
            "cost_estimate": {"total_min": 5000, "total_max": 9000},
        },
        "fraud_result": {"overall_fraud_risk": "low"},
        "expected_decision": "APPROVED",
    },
    {
        "name": "High cost — must escalate to surveyor (IRDAI rule)",
        "verification_result": {
            "verification_status": "PASS",
            "reason": "All checks passed",
            "policy_id": "POL10005",
            "violation_check": {"violation_found": False, "violation_type": None},
        },
        "assessment_result": {
            "confidence": "high",
            "exceeds_surveyor_threshold": True,
            "surveyor_threshold": 50000,
            "cost_estimate": {"total_min": 60000, "total_max": 90000},
        },
        "fraud_result": {"overall_fraud_risk": "low"},
        "expected_decision": "ESCALATED",
    },
    {
        "name": "High fraud risk (collusion pattern) — must escalate",
        "verification_result": {
            "verification_status": "PASS",
            "reason": "All checks passed",
            "policy_id": "POL10006",
            "violation_check": {"violation_found": False, "violation_type": None},
        },
        "assessment_result": {
            "confidence": "high",
            "exceeds_surveyor_threshold": False,
            "surveyor_threshold": 50000,
            "cost_estimate": {"total_min": 8000, "total_max": 12000},
        },
        "fraud_result": {"overall_fraud_risk": "high"},
        "expected_decision": "ESCALATED",
    },
    {
        "name": "Medium fraud risk (point-of-impact mismatch) — escalate for review",
        "verification_result": {
            "verification_status": "PASS",
            "reason": "All checks passed",
            "policy_id": "POL10001",
            "violation_check": {"violation_found": False, "violation_type": None},
        },
        "assessment_result": {
            "confidence": "high",
            "exceeds_surveyor_threshold": False,
            "surveyor_threshold": 50000,
            "cost_estimate": {"total_min": 10000, "total_max": 15000},
        },
        "fraud_result": {"overall_fraud_risk": "medium"},
        "expected_decision": "ESCALATED",
    },
    {
        "name": "Low assessment confidence (blurry photo) — escalate, don't guess",
        "verification_result": {
            "verification_status": "PASS",
            "reason": "All checks passed",
            "policy_id": "POL10005",
            "violation_check": {"violation_found": False, "violation_type": None},
        },
        "assessment_result": {
            "confidence": "low",
            "exceeds_surveyor_threshold": False,
            "surveyor_threshold": 50000,
            "cost_estimate": {"total_min": 3000, "total_max": 6000},
        },
        "fraud_result": {"overall_fraud_risk": "low"},
        "expected_decision": "ESCALATED",
    },
    {
        "name": "Verification already rejected (expired policy) — hard stop",
        "verification_result": {
            "verification_status": "REJECTED",
            "reason": "Policy was not active on the incident date",
            "policy_id": "POL10008",
        },
        "assessment_result": {
            "confidence": "high",
            "exceeds_surveyor_threshold": False,
            "surveyor_threshold": 50000,
            "cost_estimate": {"total_min": 4000, "total_max": 7000},
        },
        "fraud_result": {"overall_fraud_risk": "low"},
        "expected_decision": "REJECTED",
    },
    {
        "name": "Drunk driving violation — still APPROVED for third party, recovery flagged",
        "verification_result": {
            "verification_status": "PASS",
            "reason": "All checks passed",
            "policy_id": "POL10005",
            "violation_check": {"violation_found": True, "violation_type": "drunk driving"},
        },
        "assessment_result": {
            "confidence": "high",
            "exceeds_surveyor_threshold": False,
            "surveyor_threshold": 50000,
            "cost_estimate": {"total_min": 7000, "total_max": 11000},
        },
        "fraud_result": {"overall_fraud_risk": "low"},
        "expected_decision": "APPROVED",
    },
    {
        "name": "Verification escalated (identity mismatch) — needs human review",
        "verification_result": {
            "verification_status": "ESCALATE",
            "reason": "Identity/document mismatches found — needs human review",
            "policy_id": "POL10002",
            "violation_check": {"violation_found": False, "violation_type": None},
        },
        "assessment_result": {
            "confidence": "high",
            "exceeds_surveyor_threshold": False,
            "surveyor_threshold": 50000,
            "cost_estimate": {"total_min": 5000, "total_max": 8000},
        },
        "fraud_result": {"overall_fraud_risk": "low"},
        "expected_decision": "ESCALATED",
    },
    {
        "name": "Cost exactly at threshold (₹50,000) — must still escalate",
        "verification_result": {
            "verification_status": "PASS",
            "reason": "All checks passed",
            "policy_id": "POL10005",
            "violation_check": {"violation_found": False, "violation_type": None},
        },
        "assessment_result": {
            "confidence": "high",
            "exceeds_surveyor_threshold": True,
            "surveyor_threshold": 50000,
            "cost_estimate": {"total_min": 45000, "total_max": 50000},
        },
        "fraud_result": {"overall_fraud_risk": "low"},
        "expected_decision": "ESCALATED",
    },
    {
        "name": "High fraud risk overrides even a low-cost, clean-looking claim",
        "verification_result": {
            "verification_status": "PASS",
            "reason": "All checks passed",
            "policy_id": "POL10006",
            "violation_check": {"violation_found": False, "violation_type": None},
        },
        "assessment_result": {
            "confidence": "high",
            "exceeds_surveyor_threshold": False,
            "surveyor_threshold": 50000,
            "cost_estimate": {"total_min": 2000, "total_max": 3000},
        },
        "fraud_result": {"overall_fraud_risk": "high"},
        "expected_decision": "ESCALATED",
    },
]


def run_evaluation():
    print(f"Running evaluation on {len(TEST_SCENARIOS)} mock claim scenarios...\n")
    print(f"{'='*70}")

    passed = 0
    failed = 0

    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        result = make_decision(
            scenario["verification_result"],
            scenario["assessment_result"],
            scenario["fraud_result"]
        )
        actual_decision = result["decision"]
        expected_decision = scenario["expected_decision"]
        match = actual_decision == expected_decision

        status = "✅ PASS" if match else "❌ FAIL"
        if match:
            passed += 1
        else:
            failed += 1

        print(f"[{i}] {status} — {scenario['name']}")
        print(f"    Expected: {expected_decision} | Actual: {actual_decision}")
        if not match:
            print(f"    Reasons given: {result['reasons']}")
        print()

    total = len(TEST_SCENARIOS)
    accuracy = (passed / total) * 100

    print(f"{'='*70}")
    print(f"RESULTS: {passed}/{total} scenarios matched expected outcome ({accuracy:.1f}% accuracy)")
    print(f"{'='*70}")


if __name__ == "__main__":
    run_evaluation()
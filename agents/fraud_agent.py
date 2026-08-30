import json
from rapidfuzz import fuzz


def load_claim_history(filepath="data/claim_history.json"):
    """Load past third-party claims for cross-checking."""
    with open(filepath, "r") as f:
        data = json.load(f)
    return data["claims"]


def check_point_of_impact_consistency(fir_point_of_impact, assessed_damaged_parts):
    """
    Check whether the damage location described in the FIR matches
    what the Assessment Agent actually found in the photos.
    """
    if not fir_point_of_impact:
        return {
            "consistent": None,
            "note": "FIR did not specify a point of impact — cannot verify consistency"
        }

    assessed_part_names = [p["part"] for p in assessed_damaged_parts]

    # Normalize FIR text (e.g. "front bumper" -> "front_bumper") for comparison
    normalized_fir_point = fir_point_of_impact.strip().lower().replace(" ", "_")

    best_score = 0
    for part in assessed_part_names:
        score = fuzz.ratio(normalized_fir_point, part)
        best_score = max(best_score, score)

    is_consistent = best_score >= 70

    return {
        "consistent": is_consistent,
        "fir_point_of_impact": fir_point_of_impact,
        "assessed_parts": assessed_part_names,
        "match_score": best_score,
        "note": "Point of impact matches assessed damage" if is_consistent
                else "Point of impact does NOT match assessed damage — possible pre-existing damage or FIR inconsistency"
    }


def check_claim_history(policy_number, third_party_vehicle_number, fir_number):
    """
    Cross-check this claim against past claims for:
    - duplicate FIR number (same FIR reused)
    - same third-party vehicle appearing repeatedly against the same policyholder
      (possible collusion)
    """
    past_claims = load_claim_history()
    flags = []

    # Check 1: duplicate FIR number
    for claim in past_claims:
        if claim["fir_number"] == fir_number:
            flags.append({
                "flag": "duplicate_fir_number",
                "detail": f"FIR number {fir_number} was already used in claim {claim['claim_id']}"
            })

    # Check 2: same policyholder + same third-party vehicle repeating (collusion signal)
    repeat_matches = [
        c for c in past_claims
        if c["policy_number"] == policy_number
        and c["third_party_vehicle_number"] == third_party_vehicle_number
    ]
    if repeat_matches:
        flags.append({
            "flag": "possible_collusion",
            "detail": f"Policyholder {policy_number} has {len(repeat_matches)} prior claim(s) "
                      f"involving the same third-party vehicle {third_party_vehicle_number}",
            "related_claims": [c["claim_id"] for c in repeat_matches]
        })

    # Check 3: general claim frequency for this policyholder (soft signal, not auto-flag)
    policyholder_claim_count = len([c for c in past_claims if c["policy_number"] == policy_number])

    return {
        "flags": flags,
        "is_flagged": len(flags) > 0,
        "policyholder_prior_claim_count": policyholder_claim_count
    }


def run_fraud_check(fir_data, assessment_result, policy_id):
    """
    Full fraud-check pipeline, combining point-of-impact consistency
    and claim-history cross-check.
    """
    poi_check = check_point_of_impact_consistency(
        fir_point_of_impact=fir_data.get("point_of_impact"),
        assessed_damaged_parts=assessment_result.get("damaged_parts", [])
    )

    history_check = check_claim_history(
        policy_number=policy_id,
        third_party_vehicle_number=fir_data.get("third_party_vehicle_number"),
        fir_number=fir_data.get("fir_number")
    )

    overall_risk = "low"
    if history_check["is_flagged"]:
        overall_risk = "high"
    elif poi_check["consistent"] is False:
        overall_risk = "medium"

    return {
        "point_of_impact_check": poi_check,
        "claim_history_check": history_check,
        "overall_fraud_risk": overall_risk
    }
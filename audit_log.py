import json
import os
import hashlib
from datetime import datetime

AUDIT_LOG_PATH = "audit/audit_log.jsonl"
os.makedirs("audit", exist_ok=True)


def _get_last_hash():
    """Read the last line of the log and return its hash, to chain the new entry to it."""
    if not os.path.exists(AUDIT_LOG_PATH):
        return "GENESIS"
    with open(AUDIT_LOG_PATH, "r") as f:
        lines = f.readlines()
    if not lines:
        return "GENESIS"
    last_entry = json.loads(lines[-1])
    return last_entry["entry_hash"]


def append_audit_entry(claim_record):
    """
    Append a summary of this claim to the audit log.
    This function ONLY ever opens the file in append ("a") mode —
    it never reads-then-rewrites, so existing entries can never be
    altered or deleted by this code path.
    """
    decision = claim_record.get("decision_result", {}) or {}
    verification = claim_record.get("verification_result", {}) or {}
    assessment = claim_record.get("assessment_result", {}) or {}
    fraud = claim_record.get("fraud_result", {}) or {}

    entry = {
        "claim_id": claim_record["claim_id"],
        "logged_at": datetime.now().isoformat(),
        "processed_at": claim_record.get("processed_at"),
        "documents_submitted": list(claim_record.get("intake_results", {}).keys()),
        "policy_id": verification.get("policy_id"),
        "verification_status": verification.get("verification_status"),
        "damaged_parts": assessment.get("damaged_parts"),
        "estimated_cost_range": assessment.get("cost_estimate"),
        "fraud_risk": fraud.get("overall_fraud_risk"),
        "decision": decision.get("decision"),
        "reasons": decision.get("reasons"),
    }

    prev_hash = _get_last_hash()
    entry["prev_hash"] = prev_hash

    # The entry's own hash is computed from its content + the previous hash,
    # forming a chain — if anyone edits an old entry, every hash after it
    # would no longer match, making tampering detectable.
    entry_string = json.dumps(entry, sort_keys=True)
    entry["entry_hash"] = hashlib.sha256(entry_string.encode()).hexdigest()

    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def load_all_audit_entries():
    """Read every entry from the log, oldest first."""
    if not os.path.exists(AUDIT_LOG_PATH):
        return []
    entries = []
    with open(AUDIT_LOG_PATH, "r") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries


def verify_chain_integrity():
    """
    Check every entry's hash against what it should be, given its content
    and the previous entry's hash. Returns True if the chain is intact,
    False if any entry appears to have been tampered with.
    """
    entries = load_all_audit_entries()
    expected_prev = "GENESIS"
    for entry in entries:
        if entry["prev_hash"] != expected_prev:
            return False
        check_entry = {k: v for k, v in entry.items() if k != "entry_hash"}
        recomputed = hashlib.sha256(json.dumps(check_entry, sort_keys=True).encode()).hexdigest()
        if recomputed != entry["entry_hash"]:
            return False
        expected_prev = entry["entry_hash"]
    return True
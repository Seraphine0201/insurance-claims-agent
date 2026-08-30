import os
from audit_trail import generate_audit_report

CLAIMS_FOLDER = "claims"

# Find all the claim folders that actually have a saved claim_record.json
claim_ids = [
    folder for folder in os.listdir(CLAIMS_FOLDER)
    if os.path.exists(os.path.join(CLAIMS_FOLDER, folder, "claim_record.json"))
]


for claim_id in claim_ids:
    report = generate_audit_report(claim_id)
    print(report)
    print("\n")
from orchestrator import process_claim

claim_record = process_claim(
    input_docs_folder="claims_input_test/input_docs",
    input_photos_folder="claims_input_test/input_photos"
)

print("\n\n=== FINAL CLAIM RECORD SUMMARY ===")
print("Claim ID:", claim_record["claim_id"])
print("Decision:", claim_record["decision_result"]["decision"])
print("Reasons:")
for reason in claim_record["decision_result"]["reasons"]:
    print(" -", reason)
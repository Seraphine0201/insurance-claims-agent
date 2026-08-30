from agents.intake_agent import process_document
from agents.verification_agent import verify_claim

# Step 1: Run Intake Agent on every uploaded document
documents_to_process = {
    "licence": ("sample_docs/licence_ramesh.png", "driving_licence"),
    "pan": ("sample_docs/pan_ramesh.png", "pan_card"),
    "aadhaar": ("sample_docs/aadhar_ramesh.png", "aadhaar_card"),
    "rc": ("sample_docs/rc_ramesh.png", "registration_certificate"),
    "fir": ("sample_docs/fir_ramesh.png", "fir"),
}

intake_results = {}

for doc_type, (filepath, doc_label) in documents_to_process.items():
    print(f"Processing {doc_type}...")
    result = process_document(filepath, doc_label)
    intake_results[doc_type] = result["structured_data"]
    print(f"  -> {result['structured_data']}\n")

# Step 2: The FIR needs special handling — it names the AT-FAULT vehicle,
# which is what Verification Agent uses to find the matching policy.
fir_data = intake_results["fir"]

# Step 3: Run Verification Agent using the FIR + all document data
verification_result = verify_claim(
    fir_data=fir_data,
    intake_results=intake_results,
    incident_date_str=fir_data.get("incident_date")
)

print("=== VERIFICATION RESULT ===")
print(verification_result)
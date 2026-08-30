import os
from agents.intake_agent import process_document
from agents.verification_agent import verify_claim

FIR_FOLDER = "sample_docs"

fir_files = [f for f in os.listdir(FIR_FOLDER) if "fir" in f.lower()]

for fir_filename in fir_files:
    fir_path = os.path.join(FIR_FOLDER, fir_filename)

    fir_result = process_document(fir_path, "fir")
    fir_data = fir_result["structured_data"]

    print(f"\n\n########## FIR: {fir_filename} ##########")
    print("=== FIR EXTRACTED DATA ===")
    print(fir_data)

    verification_result = verify_claim(
        fir_data=fir_data,
        intake_results={"fir": fir_data},
        incident_date_str=fir_data.get("incident_date")
    )

    print("\n=== VERIFICATION RESULT ===")
    print(verification_result)
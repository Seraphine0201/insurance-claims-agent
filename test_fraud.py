import os
from agents.intake_agent import process_document
from agents.assessment_agent import assess_damage
from agents.verification_agent import verify_claim
from agents.fraud_agent import run_fraud_check

FIR_FOLDER = "sample_docs"
DAMAGE_PHOTOS_FOLDER = "sample_docs/damage_photos"

fir_files = [f for f in os.listdir(FIR_FOLDER) if "fir" in f.lower()]

valid_extensions = (".jpg", ".jpeg", ".png")
damage_photo_files = [
    f for f in os.listdir(DAMAGE_PHOTOS_FOLDER)
    if f.lower().endswith(valid_extensions)
]

for fir_filename in fir_files:
    fir_path = os.path.join(FIR_FOLDER, fir_filename)
    fir_result = process_document(fir_path, "fir")
    fir_data = fir_result["structured_data"]

    print(f"\n\n########## FIR: {fir_filename} ##########")

    verification_result = verify_claim(
        fir_data=fir_data,
        intake_results={"fir": fir_data},
        incident_date_str=fir_data.get("incident_date")
    )
    print("=== VERIFICATION RESULT ===")
    print(verification_result)

    policy_id = verification_result.get("policy_id")

    # Use just the first damage photo for this test, to keep output focused
    if damage_photo_files:
        photo_path = os.path.join(DAMAGE_PHOTOS_FOLDER, damage_photo_files[0])
        assessment_result = assess_damage(photo_path)

        fraud_result = run_fraud_check(
            fir_data=fir_data,
            assessment_result=assessment_result,
            policy_id=policy_id
        )
        print("=== FRAUD CHECK RESULT ===")
        print(fraud_result)
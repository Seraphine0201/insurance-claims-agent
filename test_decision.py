import os
from agents.intake_agent import process_document
from agents.assessment_agent import assess_damage
from agents.verification_agent import verify_claim
from agents.fraud_agent import run_fraud_check
from agents.decision_agent import make_decision

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

    verification_result = verify_claim(
        fir_data=fir_data,
        intake_results={"fir": fir_data},
        incident_date_str=fir_data.get("incident_date")
    )
    policy_id = verification_result.get("policy_id")

    for photo_filename in damage_photo_files:
        photo_path = os.path.join(DAMAGE_PHOTOS_FOLDER, photo_filename)
        assessment_result = assess_damage(photo_path)

        fraud_result = run_fraud_check(
            fir_data=fir_data,
            assessment_result=assessment_result,
            policy_id=policy_id
        )

        decision_result = make_decision(verification_result, assessment_result, fraud_result)

        print(f"\n########## FIR: {fir_filename} | PHOTO: {photo_filename} ##########")
        print("DECISION:", decision_result["decision"])
        print("REASONS:")
        for r in decision_result["reasons"]:
            print(" -", r)
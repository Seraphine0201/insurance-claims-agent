import os
from agents.assessment_agent import assess_damage

DAMAGE_PHOTOS_FOLDER = "sample_docs/damage_photos"

valid_extensions = (".jpg", ".jpeg", ".png")

photo_files = [
    f for f in os.listdir(DAMAGE_PHOTOS_FOLDER)
    if f.lower().endswith(valid_extensions)
]

for filename in photo_files:
    photo_path = os.path.join(DAMAGE_PHOTOS_FOLDER, filename)
    print(f"\n=== ASSESSING: {photo_path} ===")
    result = assess_damage(photo_path)
    print(result)
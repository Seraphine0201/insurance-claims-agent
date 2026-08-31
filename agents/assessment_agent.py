import os
import json
import sys
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import hashlib

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(image_path):
    with open(image_path, "rb") as f:
        file_bytes = f.read()
    safe_name = hashlib.md5(file_bytes).hexdigest()
    return os.path.join(CACHE_DIR, f"assessment_{safe_name}.json")

load_dotenv()
try:
    import streamlit as st
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
except Exception:
    api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")


def load_cost_reference(filepath="data/cost_reference.json"):
    """Load the hand-built part+severity -> cost range table."""
    with open(filepath, "r") as f:
        return json.load(f)


def classify_damage(image_path):
    """
    Send a damage photo to Gemini vision and ask it to identify
    the damaged part(s) and severity for each. Cached to avoid
    repeated Gemini calls on the same image during testing.
    """
    cache_file = _cache_path(image_path)

    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cached_result = json.load(f)
        # Only trust the cache if it wasn't a stored failure
        if not cached_result.get("structured_data", {}).get("error"):
            print(f"  (using cached result for {image_path})", file=sys.stderr)
            return cached_result

    image = Image.open(image_path)

    prompt = """
You are a vehicle damage assessment agent for an insurance claims system.
Look at this photo of vehicle damage and identify EVERY visibly damaged part.

Only choose part names from this exact list:
front_bumper, rear_bumper, headlight, door, windshield, fender, bonnet,
side_mirror, tail_light, wheel_rim

For each damaged part, classify severity as exactly one of: minor, moderate, severe

Also provide an overall confidence level ("high", "medium", "low") based on how
clearly the photo shows the damage (blurry, poorly lit, or ambiguous photos = low).

Respond with ONLY a JSON object in this exact format, no other text:
{
  "damaged_parts": [
    {"part": "front_bumper", "severity": "moderate"}
  ],
  "confidence": "high"
}

If you cannot identify any damage at all, return an empty damaged_parts list.
"""

    try:
        response = model.generate_content([prompt, image])
    except Exception as e:
        return {
            "error": "Gemini API call failed (likely quota exceeded)",
            "error_detail": str(e),
            "damaged_parts": [],
            "confidence": "low"
        }

    cleaned = response.text.strip().replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        result = {
            "error": "Could not parse Gemini response as JSON",
            "raw_response": cleaned,
            "damaged_parts": [],
            "confidence": "low"
        }

    # Only write to cache if this was a real success — never cache a failure
    if not result.get("error"):
        with open(cache_file, "w") as f:
            json.dump(result, f, indent=2)

    return result


def estimate_cost(damaged_parts, cost_table):
    """
    Given a list of {part, severity} and the reference cost table,
    calculate a total estimated cost range.
    """
    total_min = 0
    total_max = 0
    breakdown = []

    for item in damaged_parts:
        part = item.get("part")
        severity = item.get("severity")

        if part in cost_table and severity in cost_table[part]:
            cost_range = cost_table[part][severity]
            total_min += cost_range[0]
            total_max += cost_range[1]
            breakdown.append({
                "part": part,
                "severity": severity,
                "cost_range": cost_range
            })
        else:
            breakdown.append({
                "part": part,
                "severity": severity,
                "cost_range": None,
                "note": "Part or severity not found in reference table — needs manual pricing"
            })

    return {
        "breakdown": breakdown,
        "total_min": total_min,
        "total_max": total_max
    }


def assess_damage(image_path):
    """Full assessment pipeline: photo -> damage classification -> cost estimate."""
    cost_table = load_cost_reference()
    classification = classify_damage(image_path)

    damaged_parts = classification.get("damaged_parts", [])
    confidence = classification.get("confidence", "low")

    cost_estimate = estimate_cost(damaged_parts, cost_table)

    threshold = 50000
    exceeds_surveyor_threshold = cost_estimate["total_max"] >= threshold

    return {
        "damaged_parts": damaged_parts,
        "confidence": confidence,
        "cost_estimate": cost_estimate,
        "exceeds_surveyor_threshold": exceeds_surveyor_threshold,
        "surveyor_threshold": threshold
    }
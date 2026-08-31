import os
import sys
import json
import platform
import pytesseract
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
import hashlib

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(image_path):
    """Generate a unique cache filename based on the image path."""
    with open(image_path, "rb") as f:
        file_bytes = f.read()
    safe_name = hashlib.md5(file_bytes).hexdigest()
    return os.path.join(CACHE_DIR, f"{safe_name}.json")


# ---Setup---
load_dotenv()
try:
    import streamlit as st
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
except Exception:
    api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# On Linux (like Streamlit Cloud), tesseract-ocr installs to system PATH automatically — no override needed


model = genai.GenerativeModel("gemini-2.5-flash")


def extract_text_from_image(image_path):
    """Run OCR on an image and return raw extracted text."""
    image = Image.open(image_path)
    raw_text = pytesseract.image_to_string(image)
    return raw_text


def extract_structured_data(raw_text, document_type):
    """
    Send raw OCR text to Gemini and ask it to return clean, structured JSON based on what kind of document this is.
    """
    prompt = f"""
You are an intake agent for an insurance claims system.
You are given raw OCR text extracted from a "{document_type}" document.
The text may be messy or have OCR errors - do your best to interpret it correctly.

Extract the following fields as a JSON object (use null for any field not found):
- name
- vehicle_number
- vehicle_model
- licence_number
- incident_date (only present in FIR documents, format DD-MM-YYYY, otherwise null)
- fir_number (only present in FIR documents, otherwise null)
- third_party_vehicle_number (only present in FIR documents, otherwise null)
- point_of_impact (only present in FIR documents, e.g. "front_bumper", otherwise null)
- document_type
- raw_text_confidence (your estimate: "high", "medium", or "low", based on how
  garbled the OCR text looks)
- violation_noted (only present in FIR documents — e.g. "drunk driving", 
  "wrong-side driving", "none", otherwise null)

 Raw OCR text:
 \"\"\"{raw_text}\"\"\"

Respond with ONLY the JSON object, no other text, no markdown formatting.
"""

    try:
        response = model.generate_content(prompt)
    except Exception as e:
        return {
            "error": "Gemini API call failed (likely quota exceeded)",
            "error_detail": str(e),
            "raw_text_confidence": "low"
        }

    # Clean up in case Gemini wraps the JSON in markdown code fences
    cleaned = response.text.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    try:
        structured_data = json.loads(cleaned)
    except json.JSONDecodeError:
        structured_data = {
            "error": "Could not parse Gemini response as JSON",
            "raw_response": cleaned
        }

    return structured_data

def process_document(image_path, document_type):
    """Full intake pipeline: OCR -> structured extraction, with caching."""
    cache_file = _cache_path(image_path)

    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cached_result = json.load(f)
        # Only trust the cache if it wasn't a stored failure
        if not cached_result.get("structured_data", {}).get("error"):
            print(f"  (using cached result for {image_path})", file=sys.stderr)
            return cached_result

    raw_text = extract_text_from_image(image_path)
    structured_data = extract_structured_data(raw_text, document_type)

    result = {
        "raw_ocr_text": raw_text,
        "structured_data": structured_data
    }

    # Only write to cache if this was a real success — never cache a failure
    if not structured_data.get("error"):
        with open(cache_file, "w") as f:
            json.dump(result, f, indent=2)

    return result
    
   

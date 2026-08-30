import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ No API key found. Check your .env file.")
else:
    print("✅ API key loaded successfully.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content("Say hello in one short sentence.")
    print("Gemini response:", response.text)
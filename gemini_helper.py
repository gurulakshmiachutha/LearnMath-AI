
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

client = genai.Client(api_key=API_KEY) if API_KEY else None


def generate_ai_response(prompt):

    if client is None:
        return "Gemini API key is missing. Check your .env file."

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        return response.text or "Gemini returned an empty response."

    except Exception as error:
        print("Gemini Error:", error)
        return "Gemini is temporarily unavailable. Please try again later."

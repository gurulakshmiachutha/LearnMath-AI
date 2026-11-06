
import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

client = None

if API_KEY:
    client = genai.Client(api_key=API_KEY)


def generate_ai_response(prompt):

    if not API_KEY:
        return "ERROR: Gemini API key is missing. Check your .env file."

    if client is None:
        return "ERROR: Gemini client could not be initialized."

    for attempt in range(3):

        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            if response.text:
                return response.text

            return "Gemini returned an empty response."

        except Exception as error:

            error_message = str(error)

            print("Gemini API Error:", error_message)

            if "503" in error_message or "UNAVAILABLE" in error_message:

                if attempt < 2:
                    time.sleep(2 ** (attempt + 1))
                    continue

                return "Gemini server is temporarily overloaded. Please try again later."

            elif "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:

                return (
                    "Gemini API limit reached. "
                    "Please check your API quota and retry after the limit resets."
                )

            elif "404" in error_message or "NOT_FOUND" in error_message:

                return (
                    "Gemini model not found or unavailable: "
                    + MODEL_NAME
                    + ". Check the model name and API access."
                )

            else:
                return "Gemini API Error: " + error_message

    return "Unable to generate an AI response."


import os
from dotenv import load_dotenv
from google import genai

# Load API key and model from .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.5-flash"

print("================================")
print("       GEMINI API TEST")
print("================================")

# Check API key
if not API_KEY:
    print("ERROR: GEMINI_API_KEY not found.")
    print("Please check your .env file.")

else:
    print("API key loaded successfully.")
    print("Model:", MODEL_NAME)

    try:
        # Create Gemini client
        client = genai.Client(api_key=API_KEY)

        # Send prompt to Gemini
        print("\nConnecting to Gemini...")

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents="Explain Python loops with three simple examples."
        )

        # Display response
        if response.text:
            print("\nSUCCESS! Gemini is working.")
            print("\n========== GEMINI RESPONSE ==========\n")
            print(response.text)
        else:
            print("Gemini returned an empty response.")

    except Exception as error:
        print("\nGEMINI CONNECTION FAILED")
        print("Error:", error)

print("\n================================")
print("          TEST FINISHED")
print("================================")

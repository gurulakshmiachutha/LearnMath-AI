
import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: Gemini API key not found in .env")
else:
    client = genai.Client(api_key=api_key)

    for attempt in range(1, 4):
        try:
            print("Connecting to Gemini 3.8 Flash...")

            response = client.interactions.create(
                model="gemini-3.8-flash",
                input="Explain Python variables in three simple sentences."
            )

            print("\nGEMINI RESPONSE:")
            print(response.output_text)
            print("\nGemini connection successful!")
            break

        except Exception as error:
            print("\nAttempt:", attempt)
            print("Error:", error)

            if attempt < 3:
                print("Retrying in 15 seconds...")
                time.sleep(15)
            else:
                print("Gemini is still unavailable. Try again later.")

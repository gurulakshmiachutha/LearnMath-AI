
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

print("Checking available models...")

for model in client.models.list():
    if "generateContent" in (model.supported_actions or []):
        print(model.name)

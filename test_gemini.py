
from gemini_helper import generate_ai_response

print("Testing Gemini connection...")

answer = generate_ai_response(
    "Explain Python loops with three simple examples."
)

print("\nGemini Response:")
print(answer)

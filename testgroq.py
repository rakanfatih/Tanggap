import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Inisialisasi client Google GenAI
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

print("Daftar Model yang Didukung oleh API Key Anda:\n")
for m in client.models.list():
    # Periksa action yang didukung melalui atribut supported_actions
    actions = getattr(m, "supported_actions", [])
    if "generateContent" in actions:
        print(f"- {m.name}")
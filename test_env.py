from dotenv import load_dotenv
import os

load_dotenv()

provider = os.getenv("AI_PROVIDER")
groq_key = os.getenv("GROQ_API_KEY", "")
openai_key = os.getenv("OPENAI_API_KEY", "")

print(f"Provider:       {provider}")
print(f"Groq key start: {groq_key[:15]}")
print(f"Groq key len:   {len(groq_key)}")
print(f"OpenAI key len: {len(openai_key)}")
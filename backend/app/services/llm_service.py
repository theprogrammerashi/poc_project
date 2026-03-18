import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY in .env file")

        self.client = Groq(api_key=api_key)
        self.model_name = "llama-3.3-70b-versatile"

    def generate(self, messages):
        """
        Accepts OpenAI-style messages list:
        [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        """
        # Groq naturally supports the OpenAI messages format!
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
        )

        return response.choices[0].message.content.strip()
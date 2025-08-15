import os
import requests

class GroqAI:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.api_url = "https://api.groqcloud.com/v1/chat/completions"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def chat(self, prompt: str):
        payload = {
            "model": "groq-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 150
        }
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            return f"AI Error: {e}"

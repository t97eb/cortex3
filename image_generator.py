import os
import requests

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/CompVis/stable-diffusion-v1-4"

def generate_image(prompt: str):
    headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}
    payload = {"inputs": prompt}
    try:
        response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        image_data = response.content
        return image_data
    except Exception as e:
        return None

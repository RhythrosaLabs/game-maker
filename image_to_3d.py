import requests
import json
import os

# Constants
REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
REPLICATE_API_KEY_FILE = "replicate_api_key.json"

def load_replicate_api_key():
    if os.path.exists(REPLICATE_API_KEY_FILE):
        with open(REPLICATE_API_KEY_FILE, 'r') as file:
            data = json.load(file)
            return data.get('api_key')
    return None

def get_replicate_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

def convert_to_3d(api_key, image_url):
    data = {
        "version": "your_model_version",  # Replace with your model version
        "input": {
            "image_url": image_url
        }
    }

    try:
        response = requests.post(REPLICATE_API_URL, headers=get_replicate_headers(api_key), json=data)
        response.raise_for_status()
        response_data = response.json()
        if "predictions" not in response_data:
            error_message = response_data.get("error", {}).get("message", "Unknown error")
            return f"Error: {error_message}"

        model_url = response_data["predictions"][0]["model_url"]
        return model_url

    except requests.RequestException as e:
        return f"Error: Unable to convert image to 3D: {str(e)}"

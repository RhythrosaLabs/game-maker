import requests
import streamlit as st

# Constants
CHAT_API_URL = "https://api.openai.com/v1/chat/completions"

def get_openai_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

def generate_random_game_concept(api_key):
    prompt = "Generate a random and creative concept for a 2D game. The game should have a unique theme, setting, and interesting mechanics. Make it fun and imaginative."
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant specializing in game design."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(CHAT_API_URL, headers=get_openai_headers(api_key), json=data)
        response.raise_for_status()
        response_data = response.json()
        if "choices" not in response_data:
            error_message = response_data.get("error", {}).get("message", "Unknown error")
            return f"Error: {error_message}"

        game_concept = response_data["choices"][0]["message"]["content"]
        return game_concept

    except requests.RequestException as e:
        return f"Error: Unable to communicate with the OpenAI API: {str(e)}"

import streamlit as st
import requests
import json
import os
import zipfile
from io import BytesIO
from PIL import Image

# Constants
CHAT_API_URL = "https://api.openai.com/v1/chat/completions"
DALLE_API_URL = "https://api.openai.com/v1/images/generations"
API_KEY_FILE = "api_key.json"

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = None

if 'replicate_key' not in st.session_state:
    st.session_state.replicate_key = None

if 'customization' not in st.session_state:
    st.session_state.customization = {
        'image_types': ['Character', 'Enemy', 'Background', 'Object'],
        'script_types': ['Player', 'Enemy', 'Game Object', 'Level Background'],
        'image_count': {'Character': 1, 'Enemy': 1, 'Background': 1, 'Object': 2},
        'script_count': {'Player': 1, 'Enemy': 1, 'Game Object': 3, 'Level Background': 1}
    }

def load_api_keys():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, 'r') as file:
            data = json.load(file)
            return data.get('api_key'), data.get('replicate_key')
    return None, None

def save_api_keys(api_key, replicate_key):
    with open(API_KEY_FILE, 'w') as file:
        json.dump({"api_key": api_key, "replicate_key": replicate_key}, file)

def get_headers(api_type='openai'):
    if api_type == 'openai':
        return {
            "Authorization": f"Bearer {st.session_state.api_key}",
            "Content-Type": "application/json"
        }
    elif api_type == 'replicate':
        return {
            "Authorization": f"Token {st.session_state.replicate_key}",
            "Content-Type": "application/json"
        }

def generate_content(prompt, role):
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": f"You are a helpful assistant specializing in {role}."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(CHAT_API_URL, headers=get_headers(), json=data)
        response.raise_for_status()
        response_data = response.json()
        if "choices" not in response_data:
            error_message = response_data.get("error", {}).get("message", "Unknown error")
            return f"Error: {error_message}"

        content_text = response_data["choices"][0]["message"]["content"]
        return content_text

    except requests.RequestException as e:
        return f"Error: Unable to communicate with the OpenAI API: {str(e)}"

def generate_image(prompt, size):
    data = {
        "model": "dall-e-3",
        "prompt": prompt,
        "size": size,
        "n": 1,
        "response_format": "url"
    }

    try:
        response = requests.post(DALLE_API_URL, headers=get_headers(), json=data)
        response.raise_for_status()
        response_data = response.json()
        if "data" not in response_data:
            error_message = response_data.get("error", {}).get("message", "Unknown error")
            return f"Error: {error_message}"

        if not response_data["data"]:
            return "Error: No data returned from API."

        image_url = response_data["data"][0]["url"]
        return image_url

    except requests.RequestException as e:
        return f"Error: Unable to generate image: {str(e)}"


def generate_images(customization):
    images = {}
    image_prompts = {
        'Character': f"Create a detailed, tall image of the main character with no background.",
        'Enemy': f"Create a detailed, tall image of the enemy character with no background.",
        'Background': f"Create a wide background image or skybox.",
        'Object': f"Create an image of a key object from the world with no background."
    }
    
    sizes = {
        'Character': '1024x1792',
        'Enemy': '1024x1792',
        'Background': '1792x1024',
        'Object': '1024x1024'
    }

    for img_type in st.session_state.customization['image_types']:
        for i in range(st.session_state.customization['image_count'].get(img_type, 1)):
            prompt = f"{image_prompts[img_type]} - Instance {i + 1}"
            size = sizes[img_type]
            image_url = generate_image(prompt, size)
            images[f"{img_type.lower()}_image_{i + 1}"] = image_url

    return images

def generate_unity_scripts(customization):
    script_descriptions = {
        'Player': "Unity script for the player character with WASD controls and space bar to jump or shoot.",
        'Enemy': "Unity script for an enemy character with basic AI behavior.",
        'Game Object': "Unity script for a game object with basic functionality.",
        'Level Background': "Unity script for the level background."
    }
    
    scripts = {}
    for script_type in st.session_state.customization['script_types']:
        for i in range(st.session_state.customization['script_count'].get(script_type, 1)):
            desc = f"{script_descriptions[script_type]} - Instance {i + 1}"
            script_code = generate_content(desc, "Unity scripting")
            scripts[f"{script_type.lower()}_script_{i + 1}.cs"] = script_code
    
    return scripts

def generate_game_plan(user_prompt):
    game_plan = {}

    with st.spinner('Generating game concept...'):
        game_plan['game_concept'] = generate_content(f"Invent a new 2D game concept with a detailed theme, setting, and unique features based on the following prompt: {user_prompt}. Ensure the game has WASD controls.", "game design")

    with st.spinner('Generating world concept...'):
        game_plan['world_concept'] = generate_content(f"Create a detailed world concept for the 2D game: {game_plan['game_concept']}", "world building")

    with st.spinner('Generating character concepts...'):
        game_plan['character_concepts'] = generate_content(f"Create detailed character concepts for the player and enemies in the 2D game: {game_plan['game_concept']}", "character design")

    with st.spinner('Generating plot...'):
        game_plan['plot'] = generate_content(f"Create a plot for the 2D game based on the world and characters of the game: {game_plan['game_concept']}", "storytelling")

    with st.spinner('Generating dialogue...'):
        game_plan['dialogue'] = generate_content(f"Write some dialogue for the 2D game based on the plot of the game: {game_plan['game_concept']}", "dialogue writing")

    with st.spinner('Generating images...'):
        game_plan['images'] = generate_images(st.session_state.customization)

    with st.spinner('Generating Unity scripts...'):
        game_plan['unity_scripts'] = generate_unity_scripts(st.session_state.customization)

    with st.spinner('Generating recap...'):
        game_plan['recap'] = generate_content(f"Recap the game plan for the 2D game: {game_plan['game_concept']}", "summarization")

    with st.spinner('Creating master document...'):
        game_plan['master_document'] = create_master_document(game_plan)

    return game_plan


def create_master_document(game_plan):
    master_doc = "Game Plan Master Document\n\n"
    for key, value in game_plan.items():
        if key == "unity_scripts":
            master_doc += f"{key.replace('_', ' ').capitalize()}:\n"
            for script_key in value:
                master_doc += f" - {script_key}: See attached script.\n"
        elif key == "images":
            master_doc += f"{key.replace('_', ' ').capitalize()}:\n"
            for image_key in value:
                master_doc += f" - {image_key}: See attached image.\n"
        else:
            master_doc += f"{key.replace('_', ' ').capitalize()}: See attached document.\n"
    return master_doc

def create_zip(content_dict):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for key, value in content_dict.items():
            if isinstance(value, str):
                zip_file.writestr(f"{key}.txt", value)
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str):
                        if "http" in sub_value:  # Assuming URL indicates an image
                            # Download the image
                            img_response = requests.get(sub_value)
                            img_data = img_response.content
                            zip_file.writestr(f"{key}/{sub_key}", img_data)
                        else:
                            zip_file.writestr(f"{key}/{sub_key}", sub_value)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()

# Streamlit UI
st.title("Quick Actions - Game Plan Generator")

# Load API keys from file if not set
if not st.session_state.api_key or not st.session_state.replicate_key:
    st.session_state.api_key, st.session_state.replicate_key = load_api_keys()

# API Key Input
if not st.session_state.api_key:
    openai_key = st.text_input("Enter your OpenAI API key:", type="password")
    replicate_key = st.text_input("Enter your Replicate API key:", type="password")
    
    if st.button("Set API Keys"):
        st.session_state.api_key = openai_key
        st.session_state.replicate_key = replicate_key
        save_api_keys(st.session_state.api_key, st.session_state.replicate_key)
        st.success("API keys set successfully!")

# Game Plan Generation
if st.session_state.api_key:
    prompt = st.text_input("Enter topic/keywords for your game:")
    if st.button("Generate Game Plan"):
        if prompt:
            game_plan = generate_game_plan(prompt)
            st.write(game_plan['master_document'])
            
            # Download option
            zip_content = create_zip(game_plan)
            st.download_button(label="Download Game Plan", data=zip_content, file_name="game_plan.zip", mime="application/zip")
        else:
            st.warning("Please enter a prompt.")

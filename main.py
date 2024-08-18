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

if 'customization' not in st.session_state:
    st.session_state.customization = {
        'image_types': ['Character', 'Enemy', 'Background', 'Object'],
        'script_types': ['Player', 'Enemy', 'Game Object', 'Level Background'],
        'image_count': {'Character': 1, 'Enemy': 1, 'Background': 1, 'Object': 2},
        'script_count': {'Player': 1, 'Enemy': 1, 'Game Object': 3, 'Level Background': 1}
    }

def load_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, 'r') as file:
            data = json.load(file)
            return data.get('api_key')
    return None

def save_api_key(api_key):
    with open(API_KEY_FILE, 'w') as file:
        json.dump({"api_key": api_key}, file)

def get_headers():
    return {
        "Authorization": f"Bearer {st.session_state.api_key}",
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
        "prompt": prompt,
        "size": size,
        "n": 1
    }

    try:
        response = requests.post(DALLE_API_URL, headers=get_headers(), json=data)
        response.raise_for_status()
        response_data = response.json()
        if "data" not in response_data:
            error_message = response_data.get("error", {}).get("message", "Unknown error")
            return f"Error: {error_message}"

        image_url = response_data["data"][0]["url"]
        return image_url

    except requests.RequestException as e:
        return f"Error: Unable to generate image: {str(e)}"

def generate_images(customization):
    images = {}
    image_prompts = {
        'Character': f"Create a detailed, tall image of the main character with no background, easily convertible to 3D.",
        'Enemy': f"Create a detailed, tall image of the enemy character with no background, easily convertible to 3D.",
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

# API Key Input
if not st.session_state.api_key:
    st.session_state.api_key = load_api_key()

if not st.session_state.api_key:
    api_key = st.text_input("Enter your OpenAI API key:", type="password")
    if st.button("Set API Key"):
        st.session_state.api_key = api_key
        save_api_key(api_key)
        st.success("API key set successfully!")

# Customization Inputs
st.sidebar.header("Customization Options")

# Image Customization
image_types = st.sidebar.multiselect(
    "Select image types to generate:",
    options=['Character', 'Enemy', 'Background', 'Object'],
    default=['Character', 'Enemy', 'Background', 'Object']
)

image_counts = {img_type: st.sidebar.slider(f"Number of {img_type} images:", min_value=1, max_value=10, value=st.session_state.customization['image_count'].get(img_type, 1)) for img_type in image_types}

# Script Customization
script_types = st.sidebar.multiselect(
    "Select script types to generate:",
    options=['Player', 'Enemy', 'Game Object', 'Level Background'],
    default=['Player', 'Enemy', 'Game Object', 'Level Background']
)

script_counts = {script_type: st.sidebar.slider(f"Number of {script_type} scripts:", min_value=1, max_value=10, value=st.session_state.customization['script_count'].get(script_type, 1)) for script_type in script_types}

# Save customization state
st.session_state.customization['image_types'] = image_types
st.session_state.customization['image_count'] = image_counts
st.session_state.customization['script_types'] = script_types
st.session_state.customization['script_count'] = script_counts

# Main Content
if st.session_state.api_key:
    prompt = st.text_input("Enter topic/keywords for your game:")
    if st.button("Generate Game Plan"):
        if prompt:
            st.session_state.game_plan = generate_game_plan(prompt)
            
            # Display generated content
            game_plan = st.session_state.game_plan
            for key, value in game_plan.items():
                if key not in ["unity_scripts", "master_document", "images"]:
                    st.subheader(key.replace('_', ' ').capitalize())
                    st.write(value)
                elif key == "images":
                    for image_key, image_url in value.items():
                        st.subheader(image_key.replace('_', ' ').capitalize())
                        st.image(image_url)
                elif key == "unity_scripts":
                    st.subheader('Unity Scripts')
                    for script_key, script_code in value.items():
                        st.download_button(
                            label=script_key,
                            data=script_code,
                            file_name=script_key,
                            mime="text/plain"
                        )

            # Create download button for ZIP file
            zip_file = create_zip(game_plan)
            st.download_button(
                label="Download Game Plan ZIP",
                data=zip_file,
                file_name="game_plan.zip",
                mime="application/zip"
            )
        else:
            st.warning("Please enter a prompt.")

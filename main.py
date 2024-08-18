import streamlit as st
import requests
import json
import os
import zipfile
from io import BytesIO

# Constants
CHAT_API_URL = "https://api.openai.com/v1/chat/completions"
DALLE_API_URL = "https://api.openai.com/v1/images/generations"
API_KEY_FILE = "api_key.json"

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if 'images' not in st.session_state:
    st.session_state.images = {}
if 'unity_scripts' not in st.session_state:
    st.session_state.unity_scripts = {}

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

    # Generate and display images
    with st.spinner('Generating images...'):
        st.session_state.images['character_image'] = generate_image(
            f"Create a detailed, tall image of the main character from this game concept: {game_plan['character_concepts']}. The image should have no background and be easily converted to 3D.",
            "1024x1792"
        )
        st.session_state.images['enemy_image'] = generate_image(
            f"Create a detailed, tall image of the enemy character from this game concept: {game_plan['character_concepts']}. The image should have no background and be easily converted to 3D.",
            "1024x1792"
        )
        st.session_state.images['background_image'] = generate_image(
            f"Create a wide background image or skybox based on the world concept of this game: {game_plan['world_concept']}.",
            "1792x1024"
        )
        st.session_state.images['object_image_1'] = generate_image(
            f"Create an image of a key object from the world of this game: {game_plan['world_concept']}. The object should have no background.",
            "1024x1024"
        )
        st.session_state.images['object_image_2'] = generate_image(
            f"Create another image of a key object from the world of this game: {game_plan['world_concept']}. The object should have no background.",
            "1024x1024"
        )

    with st.spinner('Generating Unity scripts...'):
        st.session_state.unity_scripts = generate_unity_scripts(game_plan)

    with st.spinner('Generating recap...'):
        game_plan['recap'] = generate_content(f"Recap the game plan for the 2D game: {game_plan['game_concept']}", "summarization")

    with st.spinner('Creating master document...'):
        game_plan['master_document'] = create_master_document(game_plan)

    return game_plan

def generate_unity_scripts(game_plan):
    descriptions = [
        f"Unity script for the player character in a 2D game with WASD controls and space bar to jump or shoot, based on the character descriptions: {game_plan['character_concepts']}",
        f"Unity script for an enemy character in a 2D game with basic AI behavior, based on the character descriptions: {game_plan['character_concepts']}",
        f"Unity script for a game object in a 2D game, based on the world concept: {game_plan['world_concept']}",
        f"Unity script for a second game object in a 2D game, based on the world concept: {game_plan['world_concept']}",
        f"Unity script for a third game object in a 2D game, based on the world concept: {game_plan['world_concept']}",
        f"Unity script for the level background in a 2D game, based on the world concept: {game_plan['world_concept']}"
    ]
    scripts = {f"script_{i + 1}.cs": generate_content(desc, "Unity scripting") for i, desc in enumerate(descriptions)}
    return scripts

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

# Main Content
if st.session_state.api_key:
    prompt = st.text_input("Enter topic/keywords for your game:")
    if st.button("Generate Game Plan"):
        if prompt:
            game_plan = generate_game_plan(prompt)

            # Display generated content
            for key, value in game_plan.items():
                if key not in ["unity_scripts", "master_document", "images"]:
                    st.subheader(key.replace('_', ' ').capitalize())
                    st.write(value)
                elif key == "images":
                    for image_key, image_url in st.session_state.images.items():
                        st.subheader(image_key.replace('_', ' ').capitalize())
                        st.image(image_url)
                elif key == "unity_scripts":
                    st.subheader('Unity Scripts')
                    for script_key, script_code in value.items():
                        st.code(script_code, language='csharp')

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
else:
    st.warning("Please set your OpenAI API key to use the application.")

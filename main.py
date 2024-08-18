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
        "model": "gpt-4",
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
        return f"Error: Unable to communicate with the OpenAI API."

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
    
    with st.spinner('Generating Unity scripts...'):
        game_plan['unity_scripts'] = generate_unity_scripts(game_plan['game_concept'], game_plan['character_concepts'], game_plan['world_concept'])
    
    with st.spinner('Generating recap...'):
        game_plan['recap'] = generate_content(f"Recap the game plan for the 2D game: {game_plan['game_concept']}", "summarization")
    
    with st.spinner('Creating master document...'):
        game_plan['master_document'] = create_master_document(game_plan)

    return game_plan

def generate_unity_scripts(game_concept, character_concepts, world_concept):
    scripts = {}
    descriptions = [
        f"Unity script for the player character in a 2D game with WASD controls and space bar to jump or shoot, based on the character descriptions: {character_concepts}",
        f"Unity script for an enemy character in a 2D game with basic AI behavior, based on the character descriptions: {character_concepts}",
        f"Unity script for a game object in a 2D game, based on the world concept: {world_concept}",
        f"Unity script for a second game object in a 2D game, based on the world concept: {world_concept}",
        f"Unity script for a third game object in a 2D game, based on the world concept: {world_concept}",
        f"Unity script for the level background in a 2D game, based on the world concept: {world_concept}"
    ]
    for i, desc in enumerate(descriptions, start=1):
        scripts[f"script_{i}.cs"] = generate_content(desc, "Unity scripting")
    return scripts

def create_master_document(game_plan):
    master_doc = "Game Plan Master Document\n\n"
    for key, value in game_plan.items():
        if key == "unity_scripts":
            master_doc += f"{key.replace('_', ' ').capitalize()}:\n"
            for script_key in value:
                master_doc += f" - {script_key}: See attached script.\n"
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
                if key != "unity_scripts" and key != "master_document":
                    st.subheader(key.replace('_', ' ').capitalize())
                    st.write(value)
            
            # Create download button for ZIP file
            zip_file = create_zip(game_plan)
            st.download_button(
                label="Download Game Plan ZIP",
                data=zip_file,
                file_name="game_plan.zip",
                mime="application/zip"
            )
        else:
            st.warning("Please enter a prompt before generating the game plan.")
else:
    st.warning("Please set your OpenAI API key to use the application.")

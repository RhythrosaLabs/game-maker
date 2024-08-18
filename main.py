# main_app.py

import streamlit as st
import requests
import json
import os
import zipfile
from io import BytesIO

# Constants
CHAT_API_URL = "https://api.openai.com/v1/chat/completions"
DALLE_API_URL = "https://api.openai.com/v1/images/generations"
REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
API_KEY_FILE = "api_key.json"

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = None

if 'customization' not in st.session_state:
    st.session_state.customization = {
        'image_types': ['Character', 'Enemy', 'Background', 'Object'],
        'script_types': ['Player', 'Enemy', 'Game Object', 'Level Background'],
        'image_count': {'Character': 1, 'Enemy': 1, 'Background': 1, 'Object': 2},
        'script_count': {'Player': 1, 'Enemy': 1, 'Game Object': 3, 'Level Background': 1},
        'convert_to_3d': False
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

def convert_to_3d(api_key, image_url):
    data = {
        "version": "your_model_version",  # Replace with your model version
        "input": {
            "image_url": image_url
        }
    }

    try:
        response = requests.post(REPLICATE_API_URL, headers=get_headers(), json=data)
        response.raise_for_status()
        response_data = response.json()
        if "predictions" not in response_data:
            error_message = response_data.get("error", {}).get("message", "Unknown error")
            return f"Error: {error_message}"

        model_url = response_data["predictions"][0]["model_url"]
        return model_url

    except requests.RequestException as e:
        return f"Error: Unable to convert image to 3D: {str(e)}"

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

        # Convert images to 3D if the checkbox is checked
        if st.session_state.customization.get('convert_to_3d', False):
            for key, image_url in game_plan['images'].items():
                if image_url and image_url.startswith("http"):
                    model_url = convert_to_3d(st.session_state.api_key, image_url)
                    game_plan['images'][key] = model_url

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

def create_zip(content_dict, zip_filename):
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for filename, content in content_dict.items():
            if filename.endswith('.cs'):
                zipf.writestr(filename, content)
            elif filename.endswith('.png') or filename.endswith('.jpg'):
                img_data = requests.get(content).content
                zipf.writestr(filename, img_data)
            else:
                zipf.writestr(filename, content)

def main():
    st.title("Game Content Generator")
    
    # Load API key
    st.session_state.api_key = load_api_key()
    
    # API Key Input
    api_key = st.text_input("Enter your OpenAI and Replicate API Key", type="password")
    if st.button("Save API Key"):
        if api_key:
            st.session_state.api_key = api_key
            save_api_key(api_key)
            st.success("API Key saved successfully!")
        else:
            st.error("Please enter a valid API Key.")
    
    if not st.session_state.api_key:
        st.info("Please enter your API Key to use the app.")
        return

    # Customization Options
    st.sidebar.header("Customization Options")
    st.session_state.customization['image_types'] = st.sidebar.multiselect("Select Image Types", ['Character', 'Enemy', 'Background', 'Object'], default=['Character'])
    st.session_state.customization['script_types'] = st.sidebar.multiselect("Select Script Types", ['Player', 'Enemy', 'Game Object', 'Level Background'], default=['Player'])
    st.session_state.customization['image_count'] = {img_type: st.sidebar.number_input(f"Number of {img_type} images", min_value=1, value=st.session_state.customization['image_count'].get(img_type, 1)) for img_type in st.session_state.customization['image_types']}
    st.session_state.customization['script_count'] = {script_type: st.sidebar.number_input(f"Number of {script_type} scripts", min_value=1, value=st.session_state.customization['script_count'].get(script_type, 1)) for script_type in st.session_state.customization['script_types']}
    st.session_state.customization['convert_to_3d'] = st.sidebar.checkbox("Convert images to 3D")

    # User Input
    user_prompt = st.text_area("Describe your game idea", "Describe your game concept here...")

    if st.button("Generate Game Content"):
        with st.spinner("Generating content..."):
            game_plan = generate_game_plan(user_prompt)
        
        # Display Results
        st.subheader("Game Concept")
        st.write(game_plan['game_concept'])
        
        st.subheader("World Concept")
        st.write(game_plan['world_concept'])
        
        st.subheader("Character Concepts")
        st.write(game_plan['character_concepts'])
        
        st.subheader("Plot")
        st.write(game_plan['plot'])
        
        st.subheader("Dialogue")
        st.write(game_plan['dialogue'])
        
        st.subheader("Images")
        for key, url in game_plan['images'].items():
            st.image(url, caption=key)
        
        st.subheader("Unity Scripts")
        for key, script in game_plan['unity_scripts'].items():
            st.download_button(label=f"Download {key}", data=script, file_name=key)
        
        st.subheader("Master Document")
        st.download_button(label="Download Master Document", data=game_plan['master_document'], file_name="master_document.txt")
        
        zip_filename = "game_content.zip"
        create_zip({
            **game_plan['unity_scripts'],
            **game_plan['images']
        }, zip_filename)
        
        st.download_button(label="Download Zip File", data=open(zip_filename, 'rb').read(), file_name=zip_filename)

if __name__ == "__main__":
    main()

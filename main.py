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
API_KEY_FILE = "api_keys.json"

# Initialize session state
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {
        'openai': None,
        'replicate': None
    }

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
            return data.get('openai'), data.get('replicate')
    return None, None

def save_api_keys(openai_key, replicate_key):
    with open(API_KEY_FILE, 'w') as file:
        json.dump({"openai": openai_key, "replicate": replicate_key}, file)

def get_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

def generate_content(api_key, prompt, role):
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": f"You are a helpful assistant specializing in {role}."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(CHAT_API_URL, headers=get_headers(api_key), json=data)
        response.raise_for_status()
        response_data = response.json()
        if "choices" not in response_data:
            error_message = response_data.get("error", {}).get("message", "Unknown error")
            return f"Error: {error_message}"

        content_text = response_data["choices"][0]["message"]["content"]
        return content_text

    except requests.RequestException as e:
        return f"Error: Unable to communicate with the OpenAI API: {str(e)}"

def generate_image(api_key, prompt, size):
    data = {
        "model": "dall-e-3",
        "prompt": prompt,
        "size": size,
        "n": 1,
        "response_format": "url"
    }

    try:
        response = requests.post(DALLE_API_URL, headers=get_headers(api_key), json=data)
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

def generate_images(api_key, theme, customization):
    images = {}
    image_prompts = {
        'Character': f"Create a detailed image of a main character for a game with a theme of '{theme}'. The character should be designed for ease of use in game development.",
        'Enemy': f"Create a detailed image of an enemy character for a game with a theme of '{theme}'. The enemy should fit the overall design of the game and be ready for game development.",
        'Background': f"Create a wide background or skybox image for a game with a theme of '{theme}'. The background should complement the game environment and be suitable for level design.",
        'Object': f"Create an image of a key object for a game with a theme of '{theme}'. The object should be designed to fit seamlessly into the game world."
    }
    
    sizes = {
        'Character': '1024x1792',
        'Enemy': '1024x1792',
        'Background': '1792x1024',
        'Object': '1024x1024'
    }

    for img_type in customization['image_types']:
        for i in range(customization['image_count'].get(img_type, 1)):
            prompt = f"{image_prompts[img_type]} - Instance {i + 1}"
            size = sizes[img_type]
            image_url = generate_image(api_key, prompt, size)
            images[f"{img_type.lower()}_image_{i + 1}"] = image_url

    return images

def generate_unity_scripts(api_key, theme, customization):
    script_descriptions = {
        'Player': f"Unity script for the player character in a game with the theme '{theme}'. The script should include basic controls suitable for the game's design.",
        'Enemy': f"Unity script for an enemy character in a game with the theme '{theme}'. The script should include basic AI behavior fitting the game's style.",
        'Game Object': f"Unity script for a game object in a game with the theme '{theme}'. The script should provide basic functionality and be adaptable to the game's needs.",
        'Level Background': f"Unity script for managing the level background in a game with the theme '{theme}'. The script should handle background changes and fitting seamlessly into the game environment."
    }
    
    scripts = {}
    for script_type in customization['script_types']:
        for i in range(customization['script_count'].get(script_type, 1)):
            desc = f"{script_descriptions[script_type]} - Instance {i + 1}"
            script_code = generate_content(api_key, desc, "Unity scripting")
            scripts[f"{script_type.lower()}_script_{i + 1}.cs"] = script_code
    
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
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, content in content_dict.items():
            if isinstance(content, str):
                if name.endswith('.cs'):
                    zf.writestr(name, content)
                else:
                    zf.writestr(name, content)
            elif isinstance(content, dict):
                for sub_name, sub_content in content.items():
                    if isinstance(sub_content, str):
                        if "http" in sub_content:  # Assuming URL indicates an image
                            # Download the image
                            img_response = requests.get(sub_content)
                            img_data = img_response.content
                            zf.writestr(f"{name}/{sub_name}", img_data)
                        else:
                            zf.writestr(f"{name}/{sub_name}", sub_content)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()

# Streamlit UI
st.title('Game Design and Development Toolkit')

# API keys input
st.sidebar.header("API Keys")
openai_key = st.sidebar.text_input("OpenAI API Key", type="password", value=st.session_state.api_keys['openai'])
replicate_key = st.sidebar.text_input("Replicate API Key", type="password", value=st.session_state.api_keys['replicate'])

if st.sidebar.button("Save API Keys"):
    st.session_state.api_keys['openai'] = openai_key
    st.session_state.api_keys['replicate'] = replicate_key
    save_api_keys(openai_key, replicate_key)
    st.success("API keys saved successfully!")

# Customization input
st.sidebar.header("Customization Options")
image_types = st.sidebar.multiselect("Select Image Types", st.session_state.customization['image_types'], default=st.session_state.customization['image_types'])
script_types = st.sidebar.multiselect("Select Script Types", st.session_state.customization['script_types'], default=st.session_state.customization['script_types'])
image_count = {img_type: st.sidebar.slider(f"Number of {img_type} Images", 1, 10, st.session_state.customization['image_count'].get(img_type, 1)) for img_type in image_types}
script_count = {script_type: st.sidebar.slider(f"Number of {script_type} Scripts", 1, 10, st.session_state.customization['script_count'].get(script_type, 1)) for script_type in script_types}
st.session_state.customization.update({'image_types': image_types, 'script_types': script_types, 'image_count': image_count, 'script_count': script_count})

# Main content
st.header("Generate Game Assets")
user_prompt = st.text_area("Enter Game Theme and Description", value="")

if st.button("Generate Assets"):
    if not st.session_state.api_keys['openai']:
        st.error("OpenAI API key is required.")
    elif not st.session_state.api_keys['replicate']:
        st.error("Replicate API key is required.")
    elif not user_prompt:
        st.error("Please enter a game theme.")
    else:
        with st.spinner("Generating images and scripts..."):
            images = generate_images(st.session_state.api_keys['openai'], user_prompt, st.session_state.customization)
            scripts = generate_unity_scripts(st.session_state.api_keys['openai'], user_prompt, st.session_state.customization)
            master_doc = create_master_document({"images": images, "unity_scripts": scripts})
            zip_content = create_zip({**images, **scripts, "game_plan_master.txt": master_doc})

            st.success("Generation complete!")
            st.download_button("Download All Assets", zip_content, "game_assets.zip")

import streamlit as st
import requests
import json
import os
import zipfile
from io import BytesIO
from PIL import Image
import replicate

# Constants
CHAT_API_URL = "https://api.openai.com/v1/chat/completions"
DALLE_API_URL = "https://api.openai.com/v1/images/generations"
REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"  # Optional
API_KEY_FILE = "api_key.json"

# Initialize session state
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {'openai': None, 'replicate': None}

if 'customization' not in st.session_state:
    st.session_state.customization = {
        'image_types': ['Character', 'Enemy', 'Background', 'Object'],
        'script_types': ['Player', 'Enemy', 'Game Object', 'Level Background'],
        'image_count': {'Character': 1, 'Enemy': 1, 'Background': 1, 'Object': 2},
        'script_count': {'Player': 1, 'Enemy': 1, 'Game Object': 3, 'Level Background': 1},
        'use_replicate': {'convert_to_3d': False, 'generate_music': False}
    }

# Load API keys from a file
def load_api_keys():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, 'r') as file:
            data = json.load(file)
            return data.get('openai'), data.get('replicate')
    return None, None

# Save API keys to a file
def save_api_keys(openai_key, replicate_key):
    with open(API_KEY_FILE, 'w') as file:
        json.dump({"openai": openai_key, "replicate": replicate_key}, file)

# Get headers for OpenAI API
def get_openai_headers():
    return {
        "Authorization": f"Bearer {st.session_state.api_keys['openai']}",
        "Content-Type": "application/json"
    }

# Generate content using OpenAI API
def generate_content(prompt, role):
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": f"You are a helpful assistant specializing in {role}."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(CHAT_API_URL, headers=get_openai_headers(), json=data)
        response.raise_for_status()
        response_data = response.json()
        if "choices" not in response_data:
            error_message = response_data.get("error", {}).get("message", "Unknown error")
            return f"Error: {error_message}"

        content_text = response_data["choices"][0]["message"]["content"]
        return content_text

    except requests.RequestException as e:
        return f"Error: Unable to communicate with the OpenAI API: {str(e)}"

# Generate images using OpenAI's DALL-E API
def generate_image(prompt, size):
    data = {
        "model": "dall-e-3",
        "prompt": prompt,
        "size": size,
        "n": 1,
        "response_format": "url"
    }

    try:
        response = requests.post(DALLE_API_URL, headers=get_openai_headers(), json=data)
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

# Convert image to 3D model using Replicate API
def convert_image_to_3d(image_url):
    headers = {
        "Authorization": f"Token {st.session_state.api_keys['replicate']}",
        "Content-Type": "application/json"
    }
    data = {
        "input": {"image": image_url},
        "model": "adirik/wonder3d"
    }

    try:
        response = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get('output', {}).get('url')
    except requests.RequestException as e:
        return f"Error: Unable to convert image to 3D model: {str(e)}"

# Generate music using Replicate's MusicGen
def generate_music(prompt):
    replicate_client = replicate.Client(api_token=st.session_state.api_keys['replicate'])
    
    try:
        input_data = {
            "prompt": prompt,
            "model_version": "stereo-large",
            "output_format": "mp3",
            "normalization_strategy": "peak"
        }
        
        output = replicate_client.run(
            "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
            input=input_data
        )
        
        return output
    
    except Exception as e:
        return f"Error: Unable to generate music: {str(e)}"
        
# Generate multiple images based on customization settings
def generate_images(customization):
    images = {}
    
    image_prompts = {
        'Character': "Create a highly detailed, front-facing character concept art for a 2D game. The character should be in a neutral pose, with clearly defined features and high contrast. The design should be suitable for 3d rigging and for animation, with clear lines and distinct colors.",
        'Enemy': "Design a menacing, front-facing enemy character concept art for a 2D game. The enemy should have a threatening appearance with distinctive features, and be suitable for 3d rigging and animation. The design should be highly detailed with a clear silhouette, in a neutral pose",
        'Background': "Create a wide, highly detailed background image for a level of the game. The scene should include a clear distinction between foreground, midground, and background elements. The style should be consistent with the theme, with room for character movement in the foreground.",
        'Object': "Create a detailed object image for a 2D game. The object should be a key item with a transparent background, easily recognizable, and fitting the theme. The design should be clear, with minimal unnecessary details, to ensure it integrates well into the game environment."
    }
    
    sizes = {
        'Character': '1024x1792',
        'Enemy': '1024x1792',
        'Background': '1792x1024',
        'Object': '1024x1024'
    }

    for img_type in st.session_state.customization['image_types']:
        for i in range(st.session_state.customization['image_count'].get(img_type, 1)):
            prompt = f"{image_prompts[img_type]} - Variation {i + 1}"
            size = sizes[img_type]
            image_url = generate_image(prompt, size)
            if st.session_state.customization['use_replicate']['convert_to_3d'] and img_type != 'Background':
                image_url = convert_image_to_3d(image_url)
            images[f"{img_type.lower()}_image_{i + 1}"] = image_url

    return images

# Generate Unity scripts based on customization settings
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
    
def create_zip(content_dict):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for key, value in content_dict.items():
            if key == "unity_scripts":
                for script_key, script_value in value.items():
                    zip_file.writestr(script_key, script_value)
            elif key == "images":
                for image_key, image_url in value.items():
                    response = requests.get(image_url)
                    image = Image.open(BytesIO(response.content))
                    image_filename = f"{image_key}.png"
                    image.save(image_filename)
                    zip_file.write(image_filename)
                    os.remove(image_filename)
            elif key == "music":
                for music_key, music_url in value.items():
                    response = requests.get(music_url)
                    music_data = BytesIO(response.content)
                    zip_file.writestr(music_key, music_data.read())
    
    zip_buffer.seek(0)
    return zip_buffer

# Streamlit app layout
st.sidebar.header("API Keys")
openai_key = st.sidebar.text_input("OpenAI API Key", type="password", value=st.session_state.api_keys['openai'] or '')
replicate_key = st.sidebar.text_input("Replicate API Key", type="password", value=st.session_state.api_keys['replicate'] or '')
if st.sidebar.button("Save API Keys"):
    save_api_keys(openai_key, replicate_key)
    st.session_state.api_keys['openai'] = openai_key
    st.session_state.api_keys['replicate'] = replicate_key
    st.sidebar.success("API keys saved successfully!")

st.title("Game Asset Generator")

tab1, tab2, tab3, tab4 = st.tabs(["Images", "Documents", "Scripts/Codes", "Advanced Options"])

with tab1:
    st.header("Generate Images")
    image_types = st.multiselect("Select image types", options=st.session_state.customization['image_types'])
    if st.button("Generate Images"):
        images = generate_images(st.session_state.customization)
        st.session_state.generated_images = images
        for key, url in images.items():
            st.image(url, caption=key)
            st.download_button(label=f"Download {key}", data=requests.get(url).content, file_name=f"{key}.png")

with tab2:
    st.header("Generate Documents")
    st.write("Functionality to generate documents will be added here.")

with tab3:
    st.header("Generate Scripts/Codes")
    if st.button("Generate Scripts"):
        scripts = generate_unity_scripts(st.session_state.customization)
        st.session_state.generated_scripts = scripts
        for file_name, script_code in scripts.items():
            st.code(script_code, language='csharp')
            st.download_button(label=f"Download {file_name}", data=script_code, file_name=file_name)

with tab4:
    st.header("Advanced Options")
    st.session_state.customization['use_replicate']['convert_to_3d'] = st.checkbox("Convert images to 3D models", value=st.session_state.customization['use_replicate']['convert_to_3d'])
    st.session_state.customization['use_replicate']['generate_music'] = st.checkbox("Generate background music", value=st.session_state.customization['use_replicate']['generate_music'])
    if st.session_state.customization['use_replicate']['generate_music']:
        music_prompt = st.text_input("Music generation prompt", "Create background music for a 2D game level.")
        if st.button("Generate Music"):
            music_url = generate_music(music_prompt)
            st.session_state.generated_music = {'background_music': music_url}
            st.audio(music_url)
            st.download_button(label="Download Music", data=requests.get(music_url).content, file_name="background_music.mp3")
    st.write("Additional advanced options and settings can be added here.")

# Generate and download ZIP of all assets
if st.button("Generate and Download All"):
    content_dict = {
        "images": st.session_state.get('generated_images', {}),
        "unity_scripts": st.session_state.get('generated_scripts', {}),
        "music": st.session_state.get('generated_music', {})
    }
    
    zip_buffer = create_zip(content_dict)
    st.download_button(label="Download All Assets", data=zip_buffer, file_name="game_assets.zip")

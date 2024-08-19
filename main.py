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
REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
API_KEY_FILE = "api_key.json"

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
        response = requests.post(REPLICATE_API_URL, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get('output', {}).get('url')
    except requests.RequestException as e:
        return f"Error: Unable to convert image to 3D model: {str(e)}"

# Generate music using Replicate's MusicGen
def generate_music(prompt):
    headers = {
        "Authorization": f"Token {st.session_state.api_keys['replicate']}",
        "Content-Type": "application/json"
    }
    data = {
        "input": {"text": prompt},
        "model": "meta/musicgen"
    }

    try:
        response = requests.post(REPLICATE_API_URL, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get('output', {}).get('url')
    except requests.RequestException as e:
        return f"Error: Unable to generate music: {str(e)}"

# Generate multiple images based on customization settings
def generate_images(customization):
    images = {}
    
    # Refined prompts for better game design output
    image_prompts = {
        'Character': "Create a highly detailed, front-facing character concept art for a 2D game. The character should be in a neutral pose, with clearly defined features and high contrast. The design should be suitable for 3D rigging and for animation, with clear lines and distinct colors.",
        'Enemy': "Design a menacing, front-facing enemy character concept art for a 2D game. The enemy should have a threatening appearance with distinctive features, and be suitable for 3D rigging and animation. The design should be highly detailed with a clear silhouette, in a neutral pose.",
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
            if img_type != 'Background' and st.session_state.customization['use_replicate']['convert_to_3d']:
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

# Generate a complete game plan
def generate_game_plan(user_prompt):
    game_plan = {}

    with st.spinner('Generating game concept...'):
        game_plan['game_concept'] = generate_content(f"Invent a new 2D game concept with a detailed theme, setting, and unique features based on the following prompt: {user_prompt}. Ensure the game has WASD controls.", "game design")

    with st.spinner('Generating world concept...'):
        game_plan['world_concept'] = generate_content(f"Create a detailed world concept for the 2D game: {game_plan['game_concept']}", "world building")

    with st.spinner('Generating character concepts...'):
        game_plan['character_concepts'] = generate_content(f"Create detailed character concepts for the player and enemies in the 2D game: {game_plan['game_concept']}", "character design")

    with st.spinner('Generating plot...'):
        game_plan['plot'] = generate_content(f"Create a plot for the 2D game based on the world and characters described: {game_plan['world_concept']} and {game_plan['character_concepts']}", "plot creation")

    with st.spinner('Generating level design...'):
        game_plan['level_design'] = generate_content(f"Design levels for the 2D game: {game_plan['game_concept']}. Include layout and key elements.", "level design")

    return game_plan

# App layout
st.title('Game Asset Generator')

st.sidebar.header('API Keys')
openai_key = st.sidebar.text_input('OpenAI API Key', type='password')
replicate_key = st.sidebar.text_input('Replicate API Key', type='password')

if st.sidebar.button('Save API Keys'):
    st.session_state.api_keys['openai'] = openai_key
    st.session_state.api_keys['replicate'] = replicate_key
    save_api_keys(openai_key, replicate_key)
    st.success('API keys saved successfully!')

st.sidebar.header('Customization Settings')

with st.sidebar.expander('Image Customization'):
    for img_type in st.session_state.customization['image_types']:
        st.session_state.customization['image_count'][img_type] = st.sidebar.slider(f'Number of {img_type.lower()} images', 1, 10, st.session_state.customization['image_count'][img_type])

with st.sidebar.expander('Script Customization'):
    for script_type in st.session_state.customization['script_types']:
        st.session_state.customization['script_count'][script_type] = st.sidebar.slider(f'Number of {script_type.lower()} scripts', 1, 10, st.session_state.customization['script_count'][script_type])

with st.sidebar.expander('Use Replicate'):
    st.session_state.customization['use_replicate']['convert_to_3d'] = st.sidebar.checkbox('Convert images to 3D', st.session_state.customization['use_replicate']['convert_to_3d'])
    st.session_state.customization['use_replicate']['generate_music'] = st.sidebar.checkbox('Generate music', st.session_state.customization['use_replicate']['generate_music'])

tab1, tab2, tab3, tab4 = st.tabs(['Images', 'Documents', 'Scripts/Codes', 'Request Files'])

# Image generation tab
with tab1:
    st.header('Generate Images')

    if st.button('Generate Images'):
        with st.spinner('Generating images...'):
            images = generate_images(st.session_state.customization)
            for key, url in images.items():
                if url.startswith("Error:"):
                    st.error(url)
                else:
                    st.image(url, caption=key)

# Document generation tab
with tab2:
    st.header('Documents')
    if st.button('Generate Documents'):
        with st.spinner('Generating documents...'):
            game_plan = generate_game_plan("Create a game concept with a unique twist.")
            for key, content in game_plan.items():
                st.subheader(key)
                st.write(content)

# Scripts tab
with tab3:
    st.header('Unity Scripts')

    if st.button('Generate Scripts'):
        with st.spinner('Generating scripts...'):
            scripts = generate_unity_scripts(st.session_state.customization)
            for file_name, script_code in scripts.items():
                st.subheader(file_name)
                st.code(script_code, language='csharp')

# Request files tab
with tab4:
    st.header('Request Files')

    request_type = st.selectbox('Select the type of file to request', ['Image', 'Document', 'Script'])

    if st.button('Request File'):
        with st.spinner(f'Requesting {request_type.lower()}...'):
            # Here you can handle the request logic based on file type
            st.success(f'{request_type} requested successfully!')

# Download all assets as a ZIP
if st.button('Download All Assets'):
    with st.spinner('Creating ZIP file...'):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for key, url in images.items():
                if not url.startswith("Error:"):
                    response = requests.get(url)
                    img = Image.open(BytesIO(response.content))
                    img_path = f"{key}.png"
                    zip_file.writestr(img_path, response.content)
            for file_name, script_code in scripts.items():
                zip_file.writestr(file_name, script_code)

        zip_buffer.seek(0)
        st.download_button(
            label="Download All Assets",
            data=zip_buffer,
            file_name="game_assets.zip",
            mime="application/zip"
        )

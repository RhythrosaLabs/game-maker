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
    # Initialize Replicate client
    replicate_client = replicate.Client(api_token=st.session_state.api_keys['replicate'])
    
    try:
        # Define the input for the model
        input_data = {
            "prompt": prompt,
            "model_version": "stereo-large",
            "output_format": "mp3",
            "normalization_strategy": "peak"
        }
        
        # Run the model
        output = replicate_client.run(
            "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
            input=input_data
        )
        
        # Return the URL of the generated music
        return output
    
    except Exception as e:
        return f"Error: Unable to generate music: {str(e)}"
        
# Generate multiple images based on customization settings
def generate_images(customization):
    images = {}
    
    # Refined prompts for better game design output
    image_prompts = {
        'Character': "Create a highly detailed, front-facing character concept art for a 2D game. The character should be in a neutral pose, with clearly defined features and high contrast. The design should be suitable for 3d rigging and for animation, with clear lines and distinct colors.",
        'Enemy': "Design a menacing, front-facing enemy character concept art for a 2D game. The enemy should have a threatening appearance with distinctive features, and be suitable for 3d rigging and animation. The design should be highly detailed with a clear silhouette, in a neutral pose",
        'Background': "Create a wide, highly detailed background image for a level of the gamey. The scene should include a clear distinction between foreground, midground, and background elements. The style should be consistent with the theme, with room for character movement in the foreground.",
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
                    music_filename = f"{music_key}.mp3"
                    with open(music_filename, "wb") as music_file:
                        music_file.write(response.content)
                    zip_file.write(music_filename)
                    os.remove(music_filename)
            else:
                zip_file.writestr(f"{key}.txt", value)
    zip_buffer.seek(0)
    return zip_buffer


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
        game_plan['plot'] = generate_content(f"Create a plot for the 2D game based on the world and characters of the game: {game_plan['world_concept']} and {game_plan['character_concepts']}.", "plot development")

    with st.spinner('Generating assets...'):
        game_plan['images'] = generate_images(st.session_state.customization)
        game_plan['scripts'] = generate_unity_scripts(st.session_state.customization)

    return game_plan

# Streamlit app layout
st.title("Automate Your Game Dev")

# API Key Inputs
st.sidebar.header("API Keys")
openai_key = st.sidebar.text_input("OpenAI API Key", value=st.session_state.api_keys['openai'])
replicate_key = st.sidebar.text_input("Replicate API Key", value=st.session_state.api_keys['replicate'])
if st.sidebar.button("Save API Keys"):
    save_api_keys(openai_key, replicate_key)
    st.session_state.api_keys['openai'] = openai_key
    st.session_state.api_keys['replicate'] = replicate_key
    st.sidebar.success("API Keys saved successfully!")

# Customization Options
st.sidebar.header("Customization")
with st.sidebar.expander("Image Customization"):
    for img_type in st.session_state.customization['image_types']:
        st.session_state.customization['image_count'][img_type] = st.sidebar.number_input(f"Number of {img_type} Images", min_value=1, value=st.session_state.customization['image_count'][img_type])

with st.sidebar.expander("Script Customization"):
    for script_type in st.session_state.customization['script_types']:
        st.session_state.customization['script_count'][script_type] = st.sidebar.number_input(f"Number of {script_type} Scripts", min_value=1, value=st.session_state.customization['script_count'][script_type])

with st.sidebar.expander("Replicate Options"):
    st.session_state.customization['use_replicate']['convert_to_3d'] = st.checkbox("Convert Images to 3D")
    st.session_state.customization['use_replicate']['generate_music'] = st.checkbox("Generate Music")

# Generate Game Plan
user_prompt = st.text_area("Describe your game concept", "Enter a detailed description of your game here...")
if st.button("Generate Game Plan"):
    if not st.session_state.api_keys['openai'] or not st.session_state.api_keys['replicate']:
        st.error("Please enter and save both OpenAI and Replicate API keys.")
    else:
        game_plan = generate_game_plan(user_prompt)

        # Display game plan results
        st.subheader("Game Concept")
        st.write(game_plan['game_concept'])

        st.subheader("World Concept")
        st.write(game_plan['world_concept'])

        st.subheader("Character Concepts")
        st.write(game_plan['character_concepts'])

        st.subheader("Plot")
        st.write(game_plan['plot'])

        st.subheader("Assets")
        st.write("### Images")
        for img_name, img_url in game_plan['images'].items():
            st.write(f"{img_name}: [View Image]({img_url})")
            if st.session_state.customization['use_replicate']['convert_to_3d']:
                st.write(f"3D Model: [View 3D Model]({convert_image_to_3d(img_url)})")
        
        st.write("### Scripts")
        for script_name, script_code in game_plan['scripts'].items():
            st.write(f"{script_name}:\n```csharp\n{script_code}\n```")

        # Save results
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for img_name, img_url in game_plan['images'].items():
                if img_url.startswith('http'):
                    img_response = requests.get(img_url)
                    img = Image.open(BytesIO(img_response.content))
                    img_file_name = f"{img_name}.png"
                    with BytesIO() as img_buffer:
                        img.save(img_buffer, format='PNG')
                        zip_file.writestr(img_file_name, img_buffer.getvalue())
            for script_name, script_code in game_plan['scripts'].items():
                zip_file.writestr(script_name, script_code)

        st.download_button("Download ZIP of Assets and Scripts", zip_buffer.getvalue(), file_name="game_plan.zip")

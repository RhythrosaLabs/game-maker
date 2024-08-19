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

def get_openai_headers():
    return {
        "Authorization": f"Bearer {st.session_state.api_keys['openai']}",
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
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for name, content in content_dict.items():
            if name.endswith('.cs'):
                zip_file.writestr(name, content)
            elif name.endswith('.png'):
                image = Image.open(requests.get(content, stream=True).raw)
                image_buffer = BytesIO()
                image.save(image_buffer, format='PNG')
                zip_file.writestr(name, image_buffer.getvalue())
            else:
                zip_file.writestr(name, content)
    zip_buffer.seek(0)
    return zip_buffer

def main():
    st.title("Game Plan Generator")

    st.sidebar.header("API Key Configuration")
    openai_key = st.sidebar.text_input("OpenAI API Key", value=st.session_state.api_keys['openai'], type="password")
    replicate_key = st.sidebar.text_input("Replicate API Key", value=st.session_state.api_keys['replicate'], type="password")
    if st.sidebar.button("Save API Keys"):
        st.session_state.api_keys['openai'] = openai_key
        st.session_state.api_keys['replicate'] = replicate_key
        save_api_keys(openai_key, replicate_key)
        st.success("API keys saved!")

    tabs = st.tabs(["Images", "Documents", "Scripts/Codes", "Generate Specific Types"])
    
    with tabs[0]:
        st.header("Image Generation")
        image_type = st.selectbox("Select Image Type", st.session_state.customization['image_types'])
        image_count = st.number_input("Number of Images", min_value=1, max_value=5, value=1)
        if st.button("Generate Images"):
            images = generate_images(st.session_state.customization)
            for name, url in images.items():
                st.image(url, caption=name)
    
    with tabs[1]:
        st.header("Document Generation")
        document_type = st.selectbox("Select Document Type", ["Game Plan", "Character Sheet", "Level Design", "Plot Outline"])
        if st.button("Generate Document"):
            document_content = generate_content(f"Create a {document_type} based on the following prompt: {document_type}", "document creation")
            st.text_area("Generated Document", document_content, height=400)

    with tabs[2]:
        st.header("Script/Code Generation")
        script_type = st.selectbox("Select Script Type", st.session_state.customization['script_types'])
        script_count = st.number_input("Number of Scripts", min_value=1, max_value=5, value=1)
        if st.button("Generate Scripts"):
            scripts = generate_unity_scripts(st.session_state.customization)
            for name, code in scripts.items():
                st.code(code, language='csharp', caption=name)
    
    with tabs[3]:
        st.header("Generate Specific Types")
        generate_option = st.selectbox("Choose Asset Type to Generate", ["Character", "Enemy", "Background", "Object"])
        if st.button("Generate"):
            if generate_option in st.session_state.customization['image_types']:
                images = generate_images(st.session_state.customization)
                for name, url in images.items():
                    if generate_option.lower() in name:
                        st.image(url, caption=name)
            elif generate_option in st.session_state.customization['script_types']:
                scripts = generate_unity_scripts(st.session_state.customization)
                for name, code in scripts.items():
                    if generate_option.lower() in name:
                        st.code(code, language='csharp', caption=name)
    
    if st.button("Generate Full Game Plan"):
        user_prompt = st.text_input("Enter Game Concept Prompt")
        if user_prompt:
            game_plan = generate_game_plan(user_prompt)
            zip_buffer = create_zip(game_plan)
            st.download_button("Download Full Game Plan", zip_buffer, "game_plan.zip")

if __name__ == "__main__":
    main()

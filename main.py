import streamlit as st
import requests
import json
import os
import zipfile
from io import BytesIO
from PIL import Image
from random_game_concept import generate_random_game_concept  # Import the function

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

def generate_random_game_concept(api_key):
    prompt = "Generate a random and creative concept for a 2D game. The game should have a unique theme, setting, and interesting mechanics. Make it fun and imaginative."
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant specializing in game design."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(CHAT_API_URL, headers=get_openai_headers(api_key), json=data)
        response.raise_for_status()
        response_data = response.json()
        if "choices" not in response_data:
            error_message = response_data.get("error", {}).get("message", "Unknown error")
            return f"Error: {error_message}"

        game_concept = response_data["choices"][0]["message"]["content"]
        return game_concept

    except requests.RequestException as e:
        return f"Error: Unable to communicate with the OpenAI API: {str(e)}"


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
        for file_name, file_content in content_dict.items():
            if isinstance(file_content, str) and file_content.startswith("http"):
                try:
                    img_response = requests.get(file_content)
                    img_response.raise_for_status()
                    img = Image.open(BytesIO(img_response.content))
                    img.save(file_name)
                    zip_file.write(file_name)
                    os.remove(file_name)
                except requests.RequestException as e:
                    st.error(f"Error downloading image: {str(e)}")
            else:
                zip_file.writestr(file_name, file_content)
    zip_buffer.seek(0)
    return zip_buffer

def main():
    st.title("Quick Actions - Game Plan Generator")

    if not st.session_state.api_keys['openai'] or not st.session_state.api_keys['replicate']:
        openai_key, replicate_key = load_api_keys()
        st.session_state.api_keys['openai'] = openai_key
        st.session_state.api_keys['replicate'] = replicate_key

    if not st.session_state.api_keys['openai'] or not st.session_state.api_keys['replicate']:
        openai_key = st.text_input("Enter your OpenAI API key:", type="password")
        replicate_key = st.text_input("Enter your Replicate API key:", type="password")
        
        if st.button("Set API Keys"):
            st.session_state.api_keys['openai'] = openai_key
            st.session_state.api_keys['replicate'] = replicate_key
            save_api_keys(openai_key, replicate_key)
            st.success("API keys set successfully!")

    st.subheader("Customization")
    st.session_state.customization['image_types'] = st.multiselect(
        "Select Image Types to Generate",
        options=['Character', 'Enemy', 'Background', 'Object'],
        default=['Character', 'Enemy', 'Background', 'Object']
    )

    st.session_state.customization['script_types'] = st.multiselect(
        "Select Script Types to Generate",
        options=['Player', 'Enemy', 'Game Object', 'Level Background'],
        default=['Player', 'Enemy', 'Game Object', 'Level Background']
    )

    for img_type in st.session_state.customization['image_types']:
        st.session_state.customization['image_count'][img_type] = st.number_input(f"Number of {img_type} Images:", min_value=1, value=1)

    for script_type in st.session_state.customization['script_types']:
        st.session_state.customization['script_count'][script_type] = st.number_input(f"Number of {script_type} Scripts:", min_value=1, value=1)

    user_prompt = st.text_area("Enter a topic or keywords for your game:", "A 2D platformer where a cat with magical powers fights robots in a cyberpunk city.")

    if st.button("Generate Game Plan"):
        if not st.session_state.api_keys['openai']:
            st.error("Please set the OpenAI API key.")
        else:
            game_plan = generate_game_plan(user_prompt)

            st.subheader("Generated Game Plan")
            st.write(game_plan['game_concept'])
            st.write(game_plan['world_concept'])
            st.write(game_plan['character_concepts'])
            st.write(game_plan['plot'])
            st.write(game_plan['dialogue'])

            for img_key, img_url in game_plan['images'].items():
                st.image(img_url, caption=img_key, use_column_width=True)

            st.write(game_plan['recap'])

            zip_content = create_zip(game_plan)
            st.download_button(label="Download Game Plan (ZIP)", data=zip_content, file_name="game_plan.zip", mime="application/zip")

    st.header("Random Game Concept Generator")
    if st.button("Ask GPT for a Random Game Concept"):
        concept = generate_random_game_concept()
        st.write(concept)

if __name__ == "__main__":
    main()

import streamlit as st
import requests
import json
import os
import zipfile
from io import BytesIO
from PIL import Image
import replicate

# ... [Keep all the existing imports and constants] ...

# ... [Keep all the existing functions] ...

# Streamlit app layout
st.title("Automate Your Game Dev")

# API Key Inputs (in the sidebar)
st.sidebar.header("API Keys")
openai_key = st.sidebar.text_input("OpenAI API Key", value=st.session_state.api_keys['openai'])
replicate_key = st.sidebar.text_input("Replicate API Key", value=st.session_state.api_keys['replicate'])
if st.sidebar.button("Save API Keys"):
    save_api_keys(openai_key, replicate_key)
    st.session_state.api_keys['openai'] = openai_key
    st.session_state.api_keys['replicate'] = replicate_key
    st.sidebar.success("API Keys saved successfully!")

# Main content area
st.header("Customization")

# Image Customization
st.subheader("Image Customization")
for img_type in st.session_state.customization['image_types']:
    st.session_state.customization['image_count'][img_type] = st.number_input(
        f"Number of {img_type} Images", 
        min_value=1, 
        value=st.session_state.customization['image_count'][img_type]
    )

# Script Customization
st.subheader("Script Customization")
for script_type in st.session_state.customization['script_types']:
    st.session_state.customization['script_count'][script_type] = st.number_input(
        f"Number of {script_type} Scripts", 
        min_value=1, 
        value=st.session_state.customization['script_count'][script_type]
    )

# Replicate Options
st.subheader("Replicate Options")
st.session_state.customization['use_replicate']['convert_to_3d'] = st.checkbox("Convert Images to 3D")
st.session_state.customization['use_replicate']['generate_music'] = st.checkbox("Generate Music")

# Generate Game Plan
st.header("Generate Game Plan")
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

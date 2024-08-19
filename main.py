import streamlit as st
import requests
import json
import os
import zipfile
from io import BytesIO

# Constants
CHAT_API_URL = "https://api.openai.com/v1/chat/completions"
DALLE_API_URL = "https://api.openai.com/v1/images/generations"
API_KEY_FILE = "api_keys.json"

# Initialize session state
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {'openai': None, 'clipdrop': None, 'stability': None, 'replicate': None}

if 'customization' not in st.session_state:
    st.session_state.customization = {
        'social_media': {'Facebook': False, 'Twitter': False, 'Instagram': False, 'LinkedIn': False},
        'image_tools': {'bypass_generation': False},
        'other_settings': {'add_audio_logo': False, 'add_video_logo': False}
    }

# Load API keys from a file
def load_api_keys():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, 'r') as file:
            return json.load(file)
    return {}

# Save API keys to a file
def save_api_keys(keys):
    with open(API_KEY_FILE, 'w') as file:
        json.dump(keys, file)

# Get headers for OpenAI API
def get_openai_headers():
    return {
        "Authorization": f"Bearer {st.session_state.api_keys['openai']}",
        "Content-Type": "application/json"
    }

# Generate content using OpenAI API
def generate_content(prompt, role):
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": f"You are a helpful assistant specializing in {role}."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(CHAT_API_URL, headers=get_openai_headers(), json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        return f"Error: Unable to communicate with the OpenAI API: {str(e)}"

# Generate marketing campaign
def generate_marketing_campaign(prompt, budget, customization):
    campaign = {}

    campaign['concept'] = generate_content(f"Create a marketing campaign concept for the following product/campaign: {prompt}. The budget is ${budget}.", "marketing")

    platforms = [platform for platform, selected in customization['social_media'].items() if selected]
    if platforms:
        campaign['social_media_strategy'] = generate_content(f"Create a social media strategy for {', '.join(platforms)} for the following campaign: {campaign['concept']}", "social media marketing")

    if not customization['image_tools']['bypass_generation']:
        # Here you would typically generate images, but we'll skip that for now
        campaign['image_concepts'] = generate_content(f"Describe image concepts for the marketing campaign: {campaign['concept']}", "visual design")

    if customization['other_settings']['add_audio_logo']:
        campaign['audio_logo_concept'] = generate_content(f"Describe an audio logo concept for the campaign: {campaign['concept']}", "audio branding")

    if customization['other_settings']['add_video_logo']:
        campaign['video_logo_concept'] = generate_content(f"Describe a video logo concept for the campaign: {campaign['concept']}", "video branding")

    return campaign

# Streamlit app layout
st.set_page_config(page_title="Generate Marketing Campaign", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .stTextInput > div > div > input {background-color: #2b2b2b; color: white;}
    .stTextArea > div > div > textarea {background-color: #2b2b2b; color: white;}
    .stNumberInput > div > div > input {background-color: #2b2b2b; color: white;}
    .stSelectbox > div > div > select {background-color: #2b2b2b; color: white;}
    .stMultiSelect > div > div > select {background-color: #2b2b2b; color: white;}
    .stSlider > div > div > div > div {background-color: #2b2b2b;}
    .stCheckbox > label > div {color: white;}
    </style>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Sidebar Menu")
    
    tab1, tab2, tab3 = st.tabs(["API Key Setup", "About", "Chat"])
    
    with tab1:
        st.session_state.api_keys['openai'] = st.text_input("Enter your OpenAI API key:", type="password", value=st.session_state.api_keys['openai'])
        st.session_state.api_keys['clipdrop'] = st.text_input("Enter your Clipdrop API key:", type="password", value=st.session_state.api_keys['clipdrop'])
        st.session_state.api_keys['stability'] = st.text_input("Enter your Stability API key:", type="password", value=st.session_state.api_keys['stability'])
        st.session_state.api_keys['replicate'] = st.text_input("Enter your Replicate API key:", type="password", value=st.session_state.api_keys['replicate'])

        if st.button("Save API Keys"):
            save_api_keys(st.session_state.api_keys)
            st.success("API Keys saved successfully!")

# Main content
st.title("Generate Marketing Campaign")

prompt = st.text_area("Prompt", "Describe your product or campaign...")
budget = st.number_input("Budget", min_value=0, value=1000)

with st.expander("Advanced Options"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Social Media Platforms")
        for platform in st.session_state.customization['social_media']:
            st.session_state.customization['social_media'][platform] = st.checkbox(platform, value=st.session_state.customization['social_media'][platform])
    
    with col2:
        st.subheader("Image Tools")
        st.session_state.customization['image_tools']['bypass_generation'] = st.checkbox("Bypass image generation", value=st.session_state.customization['image_tools']['bypass_generation'])
        
        st.subheader("Other Settings")
        st.session_state.customization['other_settings']['add_audio_logo'] = st.checkbox("Add audio logo", value=st.session_state.customization['other_settings']['add_audio_logo'])
        st.session_state.customization['other_settings']['add_video_logo'] = st.checkbox("Add video logo", value=st.session_state.customization['other_settings']['add_video_logo'])

if st.button("Generate Marketing Campaign"):
    if not st.session_state.api_keys['openai']:
        st.error("Please enter and save your OpenAI API key.")
    else:
        with st.spinner("Generating marketing campaign..."):
            campaign = generate_marketing_campaign(prompt, budget, st.session_state.customization)

        st.subheader("Campaign Concept")
        st.write(campaign['concept'])

        if 'social_media_strategy' in campaign:
            st.subheader("Social Media Strategy")
            st.write(campaign['social_media_strategy'])

        if 'image_concepts' in campaign:
            st.subheader("Image Concepts")
            st.write(campaign['image_concepts'])

        if 'audio_logo_concept' in campaign:
            st.subheader("Audio Logo Concept")
            st.write(campaign['audio_logo_concept'])

        if 'video_logo_concept' in campaign:
            st.subheader("Video Logo Concept")
            st.write(campaign['video_logo_concept'])

        # Save results
        campaign_json = json.dumps(campaign, indent=2)
        st.download_button("Download Campaign as JSON", campaign_json, file_name="marketing_campaign.json")

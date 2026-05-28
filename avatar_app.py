import streamlit as st
import replicate
import os
from dotenv import load_dotenv
from PIL import Image
import requests
import time
from elevenlabs.client import ElevenLabs

load_dotenv()

st.title("AI Avatar Video Generator")
st.write("Create AI videos of yourself speaking!")

# Get API tokens
replicate_token = os.getenv("REPLICATE_API_TOKEN")
if not replicate_token:
    replicate_token = st.secrets.get("REPLICATE_API_TOKEN")
if not replicate_token:
    st.error("❌ Error: REPLICATE_API_TOKEN not found")
    st.stop()

elevenlabs_token = os.getenv("ELEVENLABS_API_TOKEN")
if not elevenlabs_token:
    elevenlabs_token = st.secrets.get("ELEVENLABS_API_TOKEN")
if not elevenlabs_token:
    st.error("❌ Error: ELEVENLABS_API_TOKEN not found")
    st.stop()

os.environ["REPLICATE_API_TOKEN"] = replicate_token

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=elevenlabs_token)

st.header("Step 1: Upload Your Photo")
uploaded_file = st.file_uploader("Choose a photo:", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Your photo", width=300)
    
    with open("temp_photo.jpg", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success("Photo uploaded!")
    
    st.header("Step 2: Select Language")
    language = st.selectbox(
        "Choose language:",
        ["English (US)", "English (UK)", "Spanish", "French", "German", "Chinese", "Japanese"]
    )
    st.info(f"🌍 Selected: {language}")
    
    st.header("Step 3: Select Voice")
    # ElevenLabs default voices
    voices_dict = {
        "George": "JBFqnCBsd6RMkjVDRZzb",
        "Callum": "N2lVS1Bf4yfhs3UNxFjO",
        "Alice": "Xb7hH8MSUJpSbvXZwix3",
        "Liam": "TX3LPaxmHKbtyChAf97l",
        "Matilda": "T9gMpSsS5vicPHZMVLua",
        "Will": "bIHbv24MWmeRgasZH58o",
        "Emily": "LcfcDJNUP1ajNAe3NEN5",
    }
    
    voice_name = st.selectbox("Choose voice:", list(voices_dict.keys()))
    st.info(f"🎤 Selected: {voice_name}")
    
    st.header("Step 4: What should the avatar say?")
    script = st.text_area(
        "Enter your script:", 
        height=100, 
        placeholder="Example: Hello! My name is John. I'm excited to meet you today."
    )
    
    if script:
        char_count = len(script)
        st.info(f"📝 {char_count} characters - ⏳ Processing takes 3-7 minutes")
    
    if script:
        if st.button("Create Video", type="primary"):
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            try:
                # Step 1: Generate audio with ElevenLabs SDK
                progress_placeholder.progress(20)
                status_placeholder.text("🎤 Generating voice with ElevenLabs... (20%)")
                
                audio_generator = elevenlabs_client.text_to_speech.convert(
                    text=script,
                    voice_id=voices_dict[voice_name],
                    model_id="eleven_multilingual_v2"
                )
                
                # Convert generator to bytes
                audio_bytes = b"".join(audio_generator)
                
                # Save audio temporarily
                with open("temp_audio.mp3", "wb") as f:
                    f.write(audio_bytes)
                
                progress_placeholder.progress(40)
                status_placeholder.text("✨ Audio generated, creating video... (40%)")
                
                # Step 2: Create video from image + audio
                input_data = {
                    "image": open("temp_photo.jpg", "rb"),
                    "audio": open("temp_audio.mp3", "rb"),
                    "resolution": "720p",
                    "fps": 24
                }
                
                output = replicate.run(
                    "prunaai/p-video:68b33d8ba1189a1a997abf2c09edc5bbb90d6cfa239befbf9c903bcfee7f9a59",
                    input=input_data
                )
                
                progress_placeholder.progress(100)
                status_placeholder.text("✅ Video created! (100%)")
                
                st.success("✅ Your avatar video is ready!")
                st.video(str(output))
                
                st.download_button(
                    label="📥 Download Video",
                    data=requests.get(str(output)).content,
                    file_name="avatar_video.mp4",
                    mime="video/mp4"
                )
                
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Tip: Make sure your ElevenLabs API token is valid and you have credits remaining")
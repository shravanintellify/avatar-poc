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
client = ElevenLabs(api_key=elevenlabs_token)

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
    
    st.header("Step 3: Select Gender and Voice")
    
    # Your actual ElevenLabs voices
    male_voices = {
        "Male Voice 1": "8Ln42OXYupYsag45MAUy",
        "Male Voice 2": "s3TPKV1kjDlVtZbl4Ksh",
        "Male Voice 3": "6FiCmD8eY5VyjOdG5Zjk",
        "Male Voice 4": "ppLqTilh7rH7fbUVlXsf",
        "Male Voice 5": "pVnrL6sighQX7hVz89cp",
    }

    female_voices = {
        "Female Voice 1": "uIZsnBL0YK1S5j69bAih",
        "Female Voice 2": "yj30vwTGJxSHezdAGsv9",
        "Female Voice 3": "K7W7zLWeGoxU9YqWoB7A",
        "Female Voice 4": "6u6JbqKdaQy89ENzLSju",
        "Female Voice 5": "NDTYOmYEjbDIVCKB35i3",
    }

    # Gender selection
    gender = st.radio("Choose Gender:", ["Male", "Female"], horizontal=True)
    st.info(f"👤 Selected: {gender}")

    # Select voice based on gender
    if gender == "Male":
        voice_options = male_voices
    else:
        voice_options = female_voices

    voice_name = st.selectbox("Choose voice:", list(voice_options.keys()))
    selected_voice_id = voice_options[voice_name]
    st.info(f"🎤 Selected: {voice_name}")
    
    st.header("Step 4: What should the avatar say?")
    script = st.text_area(
        "Enter your script:", 
        height=100, 
        placeholder="Example: Hello! My name is John. I'm excited to meet you today."
    )
    
    if script:
        char_count = len(script)
        # Estimate: ~150 words per minute = ~2.5 characters per second
        estimated_duration = max(5, int(char_count / 2.5))
        st.info(f"📝 {char_count} characters - ⏱️ Estimated: {estimated_duration}s video")
    
    if script:
        if st.button("Create Video", type="primary"):
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            try:
                # Step 1: Generate audio with ElevenLabs
                progress_placeholder.progress(20)
                status_placeholder.text("🎤 Generating voice with ElevenLabs... (20%)")
                
                audio_data = client.text_to_speech.convert(
                    text=script,
                    voice_id=selected_voice_id,
                    model_id="eleven_monolingual_v1",
                    output_format="mp3_44100_128"
                )
                
                # Save audio temporarily
                with open("temp_audio.mp3", "wb") as f:
                    f.write(audio_data)
                
                progress_placeholder.progress(40)
                status_placeholder.text("✨ Creating video... (40%)")
                
                # Calculate video duration based on character count
                char_count = len(script)
                video_duration = max(5, int(char_count / 2.5))
                
                # Step 2: Create video from image + audio
                input_data = {
                    "image": open("temp_photo.jpg", "rb"),
                    "audio": open("temp_audio.mp3", "rb"),
                    "prompt": script,
                    "duration": video_duration,
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
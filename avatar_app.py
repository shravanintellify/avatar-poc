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

def process_image(image):
    """Convert image to RGB and pad to square without stretching"""
    # Convert RGBA to RGB if needed
    if image.mode == "RGBA":
        rgb_image = Image.new("RGB", image.size, (255, 255, 255))
        rgb_image.paste(image, mask=image.split()[3])
        image = rgb_image
    elif image.mode != "RGB":
        image = image.convert("RGB")
    
    # Get original dimensions
    orig_width, orig_height = image.size
    
    # Create square canvas (720x720 for better quality)
    size = 720
    square = Image.new("RGB", (size, size), (255, 255, 255))
    
    # Calculate scaling to fit image in square while maintaining aspect ratio
    scale = min(size / orig_width, size / orig_height)
    new_width = int(orig_width * scale)
    new_height = int(orig_height * scale)
    
    # Resize image
    image_resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Paste centered on white background
    offset_x = (size - new_width) // 2
    offset_y = (size - new_height) // 2
    square.paste(image_resized, (offset_x, offset_y))
    
    return square

st.header("Step 1: Upload Your Photo")
uploaded_file = st.file_uploader("Choose a photo:", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    st.write(f"📊 **Original Image:** {image.size[0]}x{image.size[1]} ({image.mode})")
    st.image(image, caption="Your photo", width=300)
    
    # Process image
    processed_image = process_image(image)
    
    with open("temp_photo.jpg", "wb") as f:
        processed_image.save(f, format="JPEG", quality=95)
    
    st.success("✅ Photo processed (720x720, no stretching)")
    
    st.header("Step 2: Select Gender and Voice")
    
    # Gender selection
    gender = st.radio("Choose Gender:", ["Male", "Female"], horizontal=True)
    st.info(f"👤 Selected: {gender}")
    
    # Select voice based on gender
    if gender == "Male":
        voice_options = male_voices
    else:
        voice_options = female_voices
    
    selected_voice_name = st.selectbox(
        "Choose voice:",
        list(voice_options.keys())
    )
    selected_voice_id = voice_options[selected_voice_name]
    st.info(f"🎤 Selected: {selected_voice_name}")
    
    st.header("Step 3: What should the avatar say?")
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
                    voice_id=selected_voice_id,
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
                # Use only image and audio - let the model handle the rest
                input_data = {
                    "image": open("temp_photo.jpg", "rb"),
                    "audio": open("temp_audio.mp3", "rb"),
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
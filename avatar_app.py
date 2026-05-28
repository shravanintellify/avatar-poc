import streamlit as st
import replicate
import os
from dotenv import load_dotenv
from PIL import Image
import requests
import time

load_dotenv()

st.title("AI Avatar Video Generator")
st.write("Create AI videos of yourself speaking!")

api_token = os.getenv("REPLICATE_API_TOKEN")
if not api_token:
    api_token = st.secrets.get("REPLICATE_API_TOKEN")
if not api_token:
    st.error("❌ Error: REPLICATE_API_TOKEN not found")
    st.stop()

os.environ["REPLICATE_API_TOKEN"] = api_token

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
    
    st.header("Step 3: Select Voice Gender & Type")
    col1, col2 = st.columns(2)
    
    with col1:
        gender = st.selectbox(
            "Choose gender:",
            ["Male", "Female"]
        )
    
    with col2:
        if gender == "Male":
            voice_option = st.selectbox(
                "Choose voice:",
                ["Natural", "Professional", "Friendly", "Energetic", "Deep"]
            )
        else:
            voice_option = st.selectbox(
                "Choose voice:",
                ["Natural", "Professional", "Friendly", "Energetic", "Soft"]
            )
    
    st.info(f"🎤 Selected: {gender} - {voice_option}")
    
    st.header("Step 4: What should the avatar say?")
    script = st.text_area(
        "Enter your script:", 
        height=100, 
        placeholder="Example: Hello! My name is John. I'm excited to meet you today."
    )
    
    if script:
        char_count = len(script)
        st.info(f"📝 {char_count} characters - ⏳ Processing takes 2-5 minutes")
    
    st.header("Step 5: Adjust Speaking Speed")
    speed = st.slider(
        "Speaking Speed:",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1,
        help="0.5 = Slow, 1.0 = Normal, 2.0 = Fast"
    )
    
    speed_label = "🐢 Slow" if speed < 1.0 else "⚡ Fast" if speed > 1.0 else "⏱️ Normal"
    st.info(f"{speed_label} - Speed: {speed}x")
    
    if script:
        if st.button("Create Video", type="primary"):
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            try:
                progress_values = [10, 25, 40, 55, 70, 85, 95]
                status_messages = [
                    "🎬 Uploading image...", 
                    "🎤 Processing dialogue...", 
                    "✨ Generating avatar...", 
                    "🎨 Creating frames...", 
                    "⚙️ Finalizing video...", 
                    "🔄 Almost there...", 
                    "✅ Rendering..."
                ]
                
                for progress, message in zip(progress_values, status_messages):
                    progress_placeholder.progress(progress)
                    status_placeholder.text(f"{message} ({progress}%)")
                    time.sleep(0.5)
                
                progress_placeholder.progress(95)
                status_placeholder.text("✨ Final touches... (95%)")
                time.sleep(2)
                
                # Use built-in dialogue generation with image and speed control
                input_data = {
                    "image": open("temp_photo.jpg", "rb"),
                    "prompt": script,
                    "duration": 5,
                    "resolution": "720p",
                    "fps": 24,
                    "speech_rate": speed
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
                st.info("💡 Tip: Try a shorter script (under 100 words) for better results")
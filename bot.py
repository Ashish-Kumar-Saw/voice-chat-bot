import streamlit as st
import numpy as np
import os
from dotenv import load_dotenv
import speech_recognition as sr
from gtts import gTTS
import tempfile
import time
import pygame

# Try importing google.generativeai with better error handling
try:
    import google.generativeai as genai
    USING_GEMINI = True
except ImportError:
    USING_GEMINI = False
    st.error("Could not import Google Generative AI. Please install with: pip install google-generativeai")

# Load environment variables securely
load_dotenv()

# Configure the page with minimal theme
st.set_page_config(
    page_title="Voice AI(BOT)",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Initialize pygame mixer for reliable audio playback
pygame.mixer.init()

# Your CSS here (unchanged)
st.markdown("""
<style>
    .main {
        background-color: #ffffff;
        padding: 0;
        max-width: 100%;
    }
    
    /* Hide default header */
    header {
        visibility: hidden;
    }
    
    /* Animated pulsing circle */
    .ai-circle {
        width: 200px;
        height: 200px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(147,51,234,0.8) 0%, rgba(192,132,252,0.4) 70%, rgba(216,180,254,0) 100%);
        margin: 50px auto;
        display: flex;
        justify-content: center;
        align-items: center;
        animation: pulse 2s infinite ease-in-out;
        position: relative;
    }
    
    .ai-circle-inner {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(236,72,153,1) 0%, rgba(244,114,182,0.6) 70%, rgba(251,207,232,0) 100%);
        position: absolute;
    }
    
    @keyframes pulse {
        0% { transform: scale(0.95); }
        50% { transform: scale(1.05); }
        100% { transform: scale(0.95); }
    }
    
    .ai-circle.listening {
        animation: listen 1s infinite ease-in-out;
        background: radial-gradient(circle, rgba(59,130,246,0.8) 0%, rgba(96,165,250,0.4) 70%, rgba(191,219,254,0) 100%);
    }
    
    @keyframes listen {
        0% { transform: scale(0.95); opacity: 0.8; }
        50% { transform: scale(1.1); opacity: 1; }
        100% { transform: scale(0.95); opacity: 0.8; }
    }
    
    .ai-circle.thinking {
        animation: think 1.5s infinite ease-in-out;
        background: radial-gradient(circle, rgba(234,179,8,0.8) 0%, rgba(250,204,21,0.4) 70%, rgba(254,240,138,0) 100%);
    }
    
    @keyframes think {
        0% { transform: scale(0.95) rotate(0deg); }
        50% { transform: scale(1.05) rotate(10deg); }
        100% { transform: scale(0.95) rotate(0deg); }
    }
    
    .ai-circle.speaking {
        animation: speak 0.8s infinite ease-in-out;
        background: radial-gradient(circle, rgba(16,185,129,0.8) 0%, rgba(52,211,153,0.4) 70%, rgba(167,243,208,0) 100%);
    }
    
    @keyframes speak {
        0% { transform: scale(0.98); }
        25% { transform: scale(1.02); }
        50% { transform: scale(0.98); }
        75% { transform: scale(1.02); }
        100% { transform: scale(0.98); }
    }
    
    /* Chat bubble for response */
    .response-bubble {
        background: #f3e8ff;
        border-radius: 20px;
        padding: 15px;
        margin: 20px auto;
        max-width: 80%;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* IMPROVED BUTTON STYLING */
    .stButton > button {
        width: 70px !important;
        height: 70px !important;
        border-radius: 50% !important;
        border: 2px solid #a855f7 !important;
        background: #a855f7 !important;
        color: white !important;
        font-size: 30px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        padding: 0 !important;
        margin: 0 auto !important; /* Center button in column */
        line-height: 1 !important;
        border: 3px solid #7e22ce !important;
    }
    
    .stButton > button:hover {
        background: #9333ea !important;
        transform: scale(1.05) !important;
    }
    
    /* Hide default footer */
    footer {
        visibility: hidden !important;
    }
    
    /* Custom button container */
    .button-container {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 20px auto !important;
        max-width: 300px !important;
    }
    
    /* Better column alignment for buttons */
    .button-row {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    
    /* Status text */
    .status-text {
        text-align: center;
        color: #a855f7;
        font-style: italic;
        margin-top: 10px;
        font-size: 18px;
    }
    
    /* Bilingual status text */
    .hindi-text {
        display: block;
        margin-top: 5px;
        font-size: 16px;
    }
    
    /* Hide all streamlit branding and extra elements */
    #MainMenu, .stDeployButton, footer, header {
        visibility: hidden !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Make sure the entire app fits well on mobile */
    .stApp {
        max-width: 100vw !important;
    }
    
    /* Adjust column width to ensure proper button alignment */
    [data-testid="column"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
</style>
""", unsafe_allow_html=True)

# Configure Gemini API if available
if USING_GEMINI:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
    else:
        genai.configure(api_key=api_key)

# Initialize speech recognizer
recognizer = sr.Recognizer()

# Hindi translations for status messages
hindi_translations = {
    "listening": "सुन रहा हूँ...",
    "thinking": "सोच रहा हूँ...",
    "speaking": "बोल रहा हूँ...",
    "welcome": "नमस्ते! मुझसे बात करने के लिए माइक्रोफोन बटन पर टैप करें।",
    "error": "मुझे समझ नहीं आया। कृपया फिर से बोलें।"
}

# Initialize session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'processing_stage' not in st.session_state:
    st.session_state.processing_stage = "idle"  # idle, listening, thinking, speaking
if 'user_input' not in st.session_state:
    st.session_state.user_input = None
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = None
if 'error_message' not in st.session_state:
    st.session_state.error_message = None
if 'welcomed' not in st.session_state:
    st.session_state.welcomed = False

# Create placeholders for UI elements
animation_placeholder = st.empty()
response_placeholder = st.empty()
status_placeholder = st.empty()

# Function to convert speech to text
def speech_to_text():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        
        text = recognizer.recognize_google(audio)
        return text, None
    except sr.RequestError:
        return None, "Network error. Check your internet connection."
    except sr.UnknownValueError:
        return None, "I didn't catch that. Please try again."
    except Exception as e:
        return None, f"Error: {str(e)}"

# Function to get response from Gemini AI
def get_ai_response(prompt):
    if not USING_GEMINI:
        return "I'm having trouble thinking right now. The Gemini API is not properly configured."
    
    try:
        if not os.getenv("GEMINI_API_KEY"):
            return "Sorry, I can't think without my API key. Please ask the administrator to set up the GEMINI_API_KEY."
            
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        
        # System prompt for simple, friendly responses
        system_prompt = """
        You are a friendly voice assistant. Keep your responses concise, simple, and helpful.
        Use simple language that anyone can understand.
        """
        
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"I'm having trouble right now. Error: {str(e)}"

# Function to convert text to speech and play it
def text_to_speech_and_play(text, lang='en'):
    temp_filename = None
    try:
        # Convert text to speech
        tts = gTTS(text=text, lang=lang, slow=False)
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_filename = fp.name
            tts.save(temp_filename)
        
        # Play using pygame
        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()
        
        # Wait for audio to finish playing
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    
    except Exception as e:
        st.error(f"Error playing audio: {str(e)}")
    
    finally:
        # Clean up the temporary file
        if temp_filename and os.path.exists(temp_filename):
            try:
                os.unlink(temp_filename)
            except:
                pass

# Show animation based on current processing stage
def update_animation():
    if st.session_state.processing_stage == "listening":
        animation_placeholder.markdown("""
        <div class="ai-circle listening">
            <div class="ai-circle-inner"></div>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state.processing_stage == "thinking":
        animation_placeholder.markdown("""
        <div class="ai-circle thinking">
            <div class="ai-circle-inner"></div>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state.processing_stage == "speaking":
        animation_placeholder.markdown("""
        <div class="ai-circle speaking">
            <div class="ai-circle-inner"></div>
        </div>
        """, unsafe_allow_html=True)
    else:  # idle
        animation_placeholder.markdown("""
        <div class="ai-circle">
            <div class="ai-circle-inner"></div>
        </div>
        """, unsafe_allow_html=True)

# Update status text
def update_status():
    if st.session_state.error_message:
        status_placeholder.markdown(f"""
        <p class="status-text" style="color: #ef4444;">
            {st.session_state.error_message}
        </p>
        """, unsafe_allow_html=True)
    elif st.session_state.processing_stage == "listening":
        status_placeholder.markdown(f"""
        <p class="status-text">
            Listening...
            <span class="hindi-text">{hindi_translations['listening']}</span>
        </p>
        """, unsafe_allow_html=True)
    elif st.session_state.processing_stage == "thinking":
        status_placeholder.markdown(f"""
        <p class="status-text">
            Thinking...
            <span class="hindi-text">{hindi_translations['thinking']}</span>
        </p>
        """, unsafe_allow_html=True)
    elif st.session_state.processing_stage == "speaking":
        status_placeholder.markdown(f"""
        <p class="status-text">
            Speaking...
            <span class="hindi-text">{hindi_translations['speaking']}</span>
        </p>
        """, unsafe_allow_html=True)
    else:
        status_placeholder.markdown("", unsafe_allow_html=True)

# Display the latest response
def update_response_bubble():
    if st.session_state.conversation:
        latest_response = st.session_state.conversation[-1][1]
        response_placeholder.markdown(f"""
        <div class="response-bubble">
            {latest_response}
        </div>
        """, unsafe_allow_html=True)

# Process stages based on current state
if st.session_state.processing_stage == "listening":
    # Execute speech to text
    update_animation()
    update_status()
    user_input, error = speech_to_text()
    
    if error:
        st.session_state.error_message = error
        st.session_state.processing_stage = "idle"
        st.experimental_rerun()
    
    if user_input:
        st.session_state.user_input = user_input
        st.session_state.conversation.append(("user", user_input))
        st.session_state.processing_stage = "thinking"
        st.experimental_rerun()

elif st.session_state.processing_stage == "thinking":
    # Execute AI response generation
    update_animation()
    update_status()
    response = get_ai_response(st.session_state.user_input)
    st.session_state.ai_response = response
    st.session_state.conversation.append(("assistant", response))
    st.session_state.processing_stage = "speaking"
    update_response_bubble()
    st.experimental_rerun()

elif st.session_state.processing_stage == "speaking":
    # Execute text to speech
    update_animation()
    update_status()
    update_response_bubble()
    text_to_speech_and_play(st.session_state.ai_response)
    st.session_state.processing_stage = "idle"
    st.session_state.user_input = None
    st.session_state.ai_response = None
    st.experimental_rerun()

else:
    # Idle state - update UI and handle welcome message
    update_animation()
    update_status()
    update_response_bubble()
    
    # Play welcome message on first load
    if not st.session_state.welcomed:
        st.session_state.welcomed = True
        welcome_text_en = "Hello! Tap the microphone button and speak to ask me a question."
        st.session_state.conversation.append(("assistant", welcome_text_en))
        update_response_bubble()
        text_to_speech_and_play(welcome_text_en)
        text_to_speech_and_play(hindi_translations['welcome'], lang='hi')

# Microphone button
st.markdown('<div class="button-row">', unsafe_allow_html=True)
mic_button = st.button("🎤", key="mic_button", disabled=(st.session_state.processing_stage != "idle"))
if mic_button:
    st.session_state.error_message = None
    st.session_state.processing_stage = "listening"
    st.experimental_rerun()
st.markdown('</div>', unsafe_allow_html=True)
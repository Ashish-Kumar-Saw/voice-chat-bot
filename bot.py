import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS
import tempfile
import base64
import json

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Voice AI Bot",
    page_icon="🎤",
    layout="centered"
)

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("GEMINI_API_KEY not found in environment variables")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'awaiting_transcript' not in st.session_state:
    st.session_state.awaiting_transcript = False
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""

# Function to get AI response
def get_ai_response(prompt):
    try:
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        system_prompt = "You are a friendly voice assistant. Keep your responses concise, simple, and helpful."
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"I'm having trouble right now. Error: {str(e)}"

# Function to convert text to speech
def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_filename = fp.name
            tts.save(temp_filename)
            with open(temp_filename, "rb") as audio_file:
                audio_bytes = audio_file.read()
            import os
            os.unlink(temp_filename)
        return audio_bytes
    except Exception as e:
        st.error(f"Error generating audio: {str(e)}")
        return None

# Display header
st.title("Voice AI Bot")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "audio" in message and message["audio"]:
            st.audio(message["audio"])

# Create JavaScript component for microphone access
microphone_js = """
<style>
    .mic-button {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: #a855f7;
        color: white;
        font-size: 30px;
        display: flex;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        margin: 20px auto;
        border: 3px solid #7e22ce;
    }
    
    .mic-button:hover {
        background: #9333ea;
        transform: scale(1.05);
    }
    
    .mic-button.listening {
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(0.95); opacity: 0.8; }
        50% { transform: scale(1.05); opacity: 1; }
        100% { transform: scale(0.95); opacity: 0.8; }
    }
    
    .status-text {
        text-align: center;
        color: #a855f7;
        font-style: italic;
        margin-top: 10px;
    }
</style>

<div id="mic-button" class="mic-button">🎤</div>
<div id="status" class="status-text"></div>

<script>
    // Speech recognition setup
    const micButton = document.getElementById('mic-button');
    const statusDiv = document.getElementById('status');
    
    let recognition;
    
    // Check if browser supports speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        // Set up event listeners
        micButton.addEventListener('click', toggleListening);
        
        // Speech recognition events
        recognition.onstart = function() {
            micButton.classList.add('listening');
            statusDiv.innerText = 'Listening...';
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            statusDiv.innerText = 'Processing...';
            
            // Send to Python using window.parent.postMessage
            window.parent.postMessage({
                type: 'transcript',
                text: transcript
            }, '*');
        };
        
        recognition.onerror = function(event) {
            micButton.classList.remove('listening');
            statusDiv.innerText = 'Error: ' + event.error;
        };
        
        recognition.onend = function() {
            micButton.classList.remove('listening');
        };
        
    } else {
        statusDiv.innerText = 'Speech recognition not supported in this browser';
        micButton.disabled = true;
    }
    
    function toggleListening() {
        if (micButton.classList.contains('listening')) {
            recognition.stop();
        } else {
            recognition.start();
        }
    }
</script>
"""

# JavaScript message handler
js_message_handler = """
<script>
window.addEventListener('message', function(e) {
    if (e.data.type === 'transcript') {
        // Submit the transcript to Streamlit
        const transcript = e.data.text;
        
        // Using Streamlit's setComponentValue mechanism
        if (window.parent.streamlitInstance && typeof window.parent.streamlitInstance.setComponentValue === 'function') {
            window.parent.streamlitInstance.setComponentValue(transcript);
        } else {
            // Fallback: using form submission
            const form = parent.document.querySelector('form');
            const textInput = parent.document.querySelector('.stTextInput input');
            
            if (textInput && form) {
                textInput.value = transcript;
                const event = new Event('input', { bubbles: true });
                textInput.dispatchEvent(event);
                
                setTimeout(() => {
                    form.dispatchEvent(new Event('submit', { bubbles: true }));
                }, 100);
            }
        }
    }
});

// Expose Streamlit instance
window.streamlitInstance = {
    setComponentValue: function(value) {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: value
        }, '*');
    }
};
</script>
"""

# Display the microphone button
st.components.v1.html(microphone_js + js_message_handler, height=150)

# Text input as fallback
user_input = st.text_input("Or type your message here:", key="text_input")

# Handle user input (from text input or speech)
if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Generate AI response
    with st.spinner("Thinking..."):
        ai_response = get_ai_response(user_input)
    
    # Generate audio
    audio_data = text_to_speech(ai_response)
    
    # Add AI response
    st.session_state.messages.append({
        "role": "assistant", 
        "content": ai_response,
        "audio": audio_data
    })
    
    # Clear input and rerun
    st.session_state.transcript = ""
    st.experimental_rerun()

# Display welcome message on first load
if not st.session_state.messages:
    welcome_text = "Hello! I'm your AI assistant. Click the microphone button or type to ask me a question."
    audio_data = text_to_speech(welcome_text)
    
    st.session_state.messages.append({
        "role": "assistant", 
        "content": welcome_text,
        "audio": audio_data
    })
    st.experimental_rerun()
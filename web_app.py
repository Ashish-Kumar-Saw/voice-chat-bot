import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Voice AI Bot (Web Version)",
    page_icon="🎤",
    layout="centered"
)

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("GEMINI_API_KEY not found in environment variables")

# Web-based version with JavaScript for speech recognition
st.markdown("""
<style>
    .main {
        background-color: #ffffff;
        padding: 0;
        max-width: 100%;
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
    
    /* Status text */
    .status-text {
        text-align: center;
        color: #a855f7;
        font-style: italic;
        margin-top: 10px;
        font-size: 18px;
    }
    
    /* Microphone button */
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
        transition: all 0.3s ease;
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
</style>

<div id="response" class="response-bubble" style="display: none;"></div>
<div id="status" class="status-text"></div>
<div id="mic-button" class="mic-button">🎤</div>

<script>
    // Speech recognition setup
    const micButton = document.getElementById('mic-button');
    const statusDiv = document.getElementById('status');
    const responseDiv = document.getElementById('response');
    
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
            
            // Send to Streamlit
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: transcript
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
    
    // Listen for messages from Streamlit
    window.addEventListener('message', function(event) {
        if (event.data.type === 'streamlit:render') {
            // This runs when component is rendered
            console.log('Component rendered');
        }
        
        if (event.data.response) {
            responseDiv.style.display = 'block';
            responseDiv.innerText = event.data.response;
            statusDiv.innerText = '';
            
            // Text-to-speech
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(event.data.response);
                speechSynthesis.speak(utterance);
            }
        }
    });
</script>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Create Streamlit components for handling speech input
speech_input = st.empty()
user_input = speech_input.text_input("Speech Input (Hidden)", key="speech_input", label_visibility="hidden")

# Process user input when received
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    try:
        # Get response from Gemini
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        system_prompt = "You are a friendly voice assistant. Keep your responses concise, simple, and helpful."
        full_prompt = f"{system_prompt}\n\nUser: {user_input}\n\nAssistant:"
        response = model.generate_content(full_prompt)
        ai_response = response.text
        
        # Add response to chat history
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        
        # Pass response back to JavaScript
        st.markdown(f"""
        <script>
            window.parent.postMessage({{
                response: {ai_response!r}
            }}, '*');
        </script>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
    
    # Clear input field
    speech_input.text_input("Speech Input (Hidden)", key="speech_input_clear", label_visibility="hidden")

# Display conversation history
for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    
    if role == "user":
        st.markdown(f"**You**: {content}")
    else:
        st.markdown(f"**Assistant**: {content}")
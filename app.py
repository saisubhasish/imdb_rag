import os
import requests
import streamlit as st
from datetime import datetime

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8080")
MAX_HISTORY = 5  # Number of messages to display in chat history

# Initialize session state
def init_session_state():
    if "user_id" not in st.session_state:
        st.session_state.user_id = ""
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "input_buffer" not in st.session_state:
        st.session_state.input_buffer = ""

init_session_state()

# Layout setup
st.set_page_config(page_title="🎬 IMDB Movie Bot", layout="wide")
st.title("🎬 Chat with IMDB Movie Bot")

# Sidebar for user management
with st.sidebar:
    st.header("User Settings")
    
    # Create a form for the user ID input
    with st.form("user_id_form"):
        user_id = st.text_input("Enter your User ID:", key="user_id_input")
        
        # This button will be triggered by both clicking and pressing Enter
        submitted = st.form_submit_button("Start Session")
        
        if submitted:
            if user_id.strip():
                try:
                    response = requests.post(
                        f"{API_URL}/start_session",
                        json={"user_id": int(user_id)},
                        timeout=5
                    )
                    if response.status_code == 200:
                        st.session_state.session_id = response.json()["session_id"]
                        st.session_state.user_id = user_id
                        st.session_state.chat_history = []
                        st.success(f"Session started: {st.session_state.session_id}")
                    else:
                        st.error(f"Failed to start session: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error starting session: {str(e)}")
            else:
                st.error("Please enter a valid User ID")

    if st.session_state.session_id:
        if st.button("End Session"):
            st.session_state.session_id = None
            st.session_state.chat_history = []
            st.success("Session ended")

# Main chat interface
def display_chat():
    st.markdown("---")
    
    # Display chat history
    for msg in st.session_state.chat_history[-MAX_HISTORY:]:
        if msg["role"] == "user":
            st.markdown(f"**You ({msg['time']}):** {msg['content']}")
        else:
            st.markdown(f"**Bot ({msg['time']}):** {msg['content']}")
        st.markdown("---")

    # Input area at bottom
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input(
            "Type your question:",
            key="input_buffer",
            label_visibility="collapsed",
            placeholder="Ask about movies...",
            on_change=submit_query
        )
    with col2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("Send"):
            submit_query()

def submit_query():
    if not st.session_state.session_id:
        st.error("Please start a session first")
        return

    user_query = st.session_state.input_buffer.strip()
    if not user_query:
        return

    # Add user message to history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_query,
        "time": datetime.now().strftime("%H:%M")
    })

    try:
        payload = {
            "user_id": int(st.session_state.user_id),
            "session_id": st.session_state.session_id,
            "user_query": user_query
        }

        response = requests.post(
            f"{API_URL}/query",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            bot_response = response.json().get("answer", "No response received")
            st.session_state.chat_history.append({
                "role": "bot",
                "content": bot_response,
                "time": datetime.now().strftime("%H:%M")
            })
        else:
            error_msg = f"Error {response.status_code}: {response.json().get('detail', 'Unknown error')}"
            st.session_state.chat_history.append({
                "role": "bot",
                "content": error_msg,
                "time": datetime.now().strftime("%H:%M")
            })

    except Exception as e:
        st.session_state.chat_history.append({
            "role": "bot",
            "content": f"Connection error: {str(e)}",
            "time": datetime.now().strftime("%H:%M")
        })

    # Clear input buffer
    st.session_state.input_buffer = ""

# Display appropriate interface based on session state
if st.session_state.session_id:
    st.success(f"Active Session: {st.session_state.session_id}")
    display_chat()
else:
    st.info("Please enter your User ID and start a session in the sidebar")

# Add some styling
st.markdown("""
<style>
    .stTextInput input {
        border-radius: 20px;
        padding: 10px 15px;
    }
    .stButton button {
        width: 100%;
        border-radius: 20px;
        padding: 10px;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

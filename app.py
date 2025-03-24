import os, json
import requests
import streamlit as st
from datetime import datetime
from typing import Optional

from src.logger import logging

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8080")
MAX_HISTORY = 5  # Number of messages to display in chat history

# --------------------------
# Session State Management
# --------------------------
def init_session_state():
    """Initialize all session state variables"""
    session_vars = {
        "username": "",
        "password": "",
        "access_token": None,
        "user_id": None,
        "session_id": None,
        "chat_history": [],
        "input_buffer": "",
        "active_tab": "Chat"  # Track current tab
    }
    
    for key, value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --------------------------
# API Client Functions
# --------------------------
def make_api_request(
    method: str,
    endpoint: str,
    data: Optional[dict] = None,
    needs_auth: bool = True,
    is_form_data: bool = False
) -> Optional[dict]:
    """Generic function to make API requests"""
    headers = {}
    if needs_auth and st.session_state.access_token:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    
    try:
        url = f"{API_URL}/{endpoint}"
        
        # Debug output
        logging.info(f"Making {method} request to {url}")  # Debug
        
        if is_form_data:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            response_data = data
        else:
            headers["Content-Type"] = "application/json"
            response_data = json.dumps(data) if data else None
        
        response = None
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(
                url, 
                data=response_data if is_form_data else None,
                json=None if is_form_data else data,
                headers=headers, 
                timeout=10
            )
        
        # Debug output
        logging.info(f"Response status: {response.status_code}")  # Debug
        logging.info(f"Response content: {response.text}")  # Debug
        
        if not response.content:
            st.error(f"Empty response from server for {endpoint}")
            return None
            
        try:
            response_json = response.json()
        except ValueError as e:
            st.error(f"Invalid JSON response from {endpoint}. Response: {response.text}")
            return None
            
        if response.status_code == 200:
            return response_json
        else:
            error_detail = response_json.get("detail", response.text)
            st.error(f"API Error ({response.status_code}): {error_detail}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
    return None

# --------------------------
# Authentication Functions
# --------------------------
def handle_login():
    """Handle user login"""
    if not st.session_state.username or not st.session_state.password:
        st.error("Please enter both username and password")
        return
    
    response = make_api_request(
        "POST",
        "generate_access_token",
        data={
            "username": st.session_state.username,
            "password": st.session_state.password
        },
        needs_auth=False,
        is_form_data=True
    )
    
    if response and "access_token" in response:
        st.session_state.access_token = response["access_token"]
        st.success("Login successful!")
        fetch_user_info()
    else:
        st.error("Login failed - please check credentials")

def fetch_user_info():
    """Fetch user info after login"""
    user_info = make_api_request("GET", "user_info")
    if user_info:
        try:
            st.session_state.user_id = str(user_info.get("user_id"))  # Ensure string
        except Exception as e:
            st.error(f"Failed to process user info: {str(e)}")

def handle_logout():
    """Clear session on logout"""
    st.session_state.access_token = None
    st.session_state.session_id = None
    st.session_state.chat_history = []
    st.success("Logged out successfully")

# --------------------------
# Session Management
# --------------------------
def handle_start_session():
    """Start a new chat session"""
    if not st.session_state.user_id:
        st.error("Please enter a User ID")
        return
    
    response = make_api_request(
        "POST",
        "start_session",
        data={"user_id": st.session_state.user_id}  # Now sends string
    )
    
    if response:
        st.session_state.session_id = response["session_id"]
        st.session_state.chat_history = []
        st.success(f"Session started: {st.session_state.session_id}")

def handle_end_session():
    """End current session"""
    st.session_state.session_id = None
    st.session_state.chat_history = []
    st.success("Session ended")

# --------------------------
# Chat Functions
# --------------------------
def submit_query():
    """Submit user query to the API"""
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

    response = make_api_request(
        "POST",
        "query",
        data={
            "user_id": st.session_state.user_id,
            "session_id": st.session_state.session_id,
            "user_query": user_query
        }
    )

    if response:
        bot_response = response.get("answer", "No response received")
        st.session_state.chat_history.append({
            "role": "bot",
            "content": bot_response,
            "time": datetime.now().strftime("%H:%M")
        })

    # Clear input buffer
    st.session_state.input_buffer = ""

# --------------------------
# User Registration
# --------------------------
def handle_registration(username: str, password: str, email: str, full_name: str):
    """Handle new user registration"""
    response = make_api_request(
        "POST",
        "register",
        data={
            "username": username,
            "password": password,
            "email": email,
            "full_name": full_name
        },
        needs_auth=False
    )
    
    if response:
        st.success("Registration successful! Please login.")

# --------------------------
# UI Components
# --------------------------
def render_auth_section():
    """Render authentication UI"""
    with st.sidebar:
        st.header("Authentication")
        
        # Login Form
        with st.expander("Login", expanded=True):
            with st.form("login_form"):
                st.session_state.username = st.text_input("Username")
                st.session_state.password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    handle_login()
        
        # Registration Form
        with st.expander("Register", expanded=False):
            with st.form("register_form"):
                reg_username = st.text_input("Username (Register)")
                reg_password = st.text_input("Password (Register)", type="password")
                reg_email = st.text_input("Email (Optional)")
                reg_full_name = st.text_input("Full Name (Optional)")
                if st.form_submit_button("Register"):
                    handle_registration(reg_username, reg_password, reg_email, reg_full_name)
        
        # Session Management
        if st.session_state.access_token:
            st.success(f"Logged in as {st.session_state.username}")
            
            with st.form("session_form"):
                # Changed from number_input to text_input
                st.session_state.user_id = st.text_input(
                    "User ID", 
                    value=str(st.session_state.user_id) if st.session_state.user_id else ""
                )
                if st.form_submit_button("Start Session"):
                    handle_start_session()
            
            if st.session_state.session_id:
                if st.button("End Session"):
                    handle_end_session()
            
            if st.button("Logout"):
                handle_logout()

def render_chat_interface():
    """Render the main chat interface"""
    st.markdown("---")
    
    # Display chat history
    for msg in st.session_state.chat_history[-MAX_HISTORY:]:
        if msg["role"] == "user":
            st.markdown(f"**You ({msg['time']}):** {msg['content']}")
        else:
            st.markdown(f"**Bot ({msg['time']}):** {msg['content']}")
        st.markdown("---")

    # Input area
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

def render_api_tester():
    """Interface for testing API endpoints"""
    st.header("API Tester")
    
    endpoint = st.selectbox(
        "Select Endpoint",
        ["/register", "/generate_access_token", "/start_session", "/query", "/user_info"]
    )
    
    with st.form("api_tester_form"):
        if endpoint == "/register":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            email = st.text_input("Email (Optional)")
            full_name = st.text_input("Full Name (Optional)")
        elif endpoint == "/generate_access_token":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
        elif endpoint == "/start_session":
            user_id = st.number_input("User ID", value=1)
        elif endpoint == "/query":
            user_id = st.number_input("User ID", value=1)
            session_id = st.text_input("Session ID")
            user_query = st.text_input("Query")
        elif endpoint == "/user_info":
            pass  # No parameters needed
            
        submitted = st.form_submit_button("Test Endpoint")
        
        if submitted:
            data = {}
            if endpoint == "/register":
                data = {
                    "username": username,
                    "password": password,
                    "email": email,
                    "full_name": full_name
                }
            elif endpoint == "/generate_access_token":
                data = {
                    "username": username,
                    "password": password
                }
            elif endpoint == "/start_session":
                data = {"user_id": user_id}
            elif endpoint == "/query":
                data = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "user_query": user_query
                }
                
            method = "POST" if endpoint != "/user_info" else "GET"
            response = make_api_request(
                method,
                endpoint.lstrip("/"),
                data=data if data else None,
                needs_auth=endpoint not in ["/register", "/generate_access_token"]
            )
            
            if response:
                st.json(response)

# --------------------------
# Main App Layout
# --------------------------
def main():
    """Main application layout"""
    st.set_page_config(page_title="🎬 IMDB Movie Bot", layout="wide")
    st.title("🎬 IMDB Movie Bot & API Tester")
    
    # Tab navigation
    tabs = ["Chat", "API Tester"]
    st.session_state.active_tab = st.radio(
        "Navigation",
        tabs,
        horizontal=True,
        label_visibility="hidden"
    )
    
    # Render auth section in sidebar
    render_auth_section()
    
    # Main content area
    if st.session_state.active_tab == "Chat":
        if st.session_state.session_id:
            st.success(f"Active Session: {st.session_state.session_id}")
            render_chat_interface()
        elif st.session_state.access_token:
            st.info("Please start a session in the sidebar")
        else:
            st.info("Please login in the sidebar")
    else:
        render_api_tester()
    
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
        .stRadio > div {
            display: flex;
            gap: 10px;
        }
        .stRadio > div > label {
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
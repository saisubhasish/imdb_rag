import os
import requests
import streamlit as st

# Use the environment variable for API_URL
API_URL = os.getenv("API_URL", "http://localhost:8080")  # Fallback to localhost if not set

# Layout setup
col1, col2 = st.columns([1, 3])  # Left for User ID, Right for Chat interface

with col1:
    st.markdown("### 🆔 User ID")
    user_id_input = st.text_input("Enter your User ID:", key="user_id", on_change=lambda: start_session())

with col2:
    st.title("🎬 Chat with IMDB Movie Bot")
    st.markdown("---")  # Separator

# Ensure session states exist
if "session_id" not in st.session_state:
    st.session_state["session_id"] = None
if "bot_response" not in st.session_state:
    st.session_state["bot_response"] = ""
if "latest_query" not in st.session_state:
    st.session_state["latest_query"] = ""
if "input_buffer" not in st.session_state:
    st.session_state["input_buffer"] = ""  # Separate input variable

# Function to start a session
def start_session():
    user_id = st.session_state["user_id"].strip()
    if user_id:
        try:
            response = requests.post(f"{API_URL}/start_session", json={"user_id": int(user_id)})
            if response.status_code == 200:
                st.session_state["session_id"] = response.json()["session_id"]
                st.success(f"Session started: {st.session_state['session_id']}")
            else:
                st.error(f"Failed to start session: {response.json()}")
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
    else:
        st.error("Please enter a valid User ID.")

# Function to handle query submission
def submit_query():
    user_query = st.session_state.get("input_buffer", "").strip()
    
    if user_query and st.session_state["session_id"]:
        payload = {
            "user_id": int(st.session_state["user_id"]),
            "session_id": st.session_state["session_id"],
            "user_query": user_query
        }

        try:
            response = requests.post(f"{API_URL}/query", json=payload, timeout=10)
            if response.status_code == 200:
                st.session_state["bot_response"] = response.json().get("answer", "No response received.")
            else:
                st.session_state["bot_response"] = f"Error {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            st.session_state["bot_response"] = f"Request failed: {e}"
        
        st.session_state["latest_query"] = user_query  # Store latest query
        st.session_state["input_buffer"] = ""  # **Clear input field**
    else:
        st.error("Please start a session before submitting a query.")

# Chat Section
with col2:
    user_query_input = st.text_input("Ask your question:", key="input_buffer", on_change=submit_query)

    if st.button("Submit"):
        submit_query()

    # Display conversation below "Submit" button
    st.write("**You:**", st.session_state.get("latest_query", ""))
    st.write("**Bot:**", st.session_state.get("bot_response", ""))


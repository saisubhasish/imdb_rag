import os
import uuid
import certifi
import uvicorn
import warnings
from typing import List, Dict
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient
from fastapi import FastAPI, HTTPException

from src.logger import logging
from src.utils import get_vector_store, get_retriever, get_response
from src.config import QDRANT_COLLECTION_NAME, QDRANT_HOST, QDRANT_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, MODEL_NAME_LLAMA

warnings.filterwarnings("ignore")

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())  # SSL handshake failed
db = client["chat_db"]  # Database Name
sessions_collection = db["sessions"]  # Collection Name

# Define a maximum context window (for last 5 messages)
CONTEXT_WINDOW = 5

app = FastAPI()

# Connect vector store
vector_store = get_vector_store(QDRANT_HOST=QDRANT_HOST, API_KEY=QDRANT_API_KEY, QDRANT_COLLECTION_NAME=QDRANT_COLLECTION_NAME, OPENAI_API_KEY=OPENAI_API_KEY)
# Build retriever
retriever = get_retriever(GROQ_API_KEY=GROQ_API_KEY, MODEL_NAME_LLAMA=MODEL_NAME_LLAMA, vector_store=vector_store)

# Define request model
class QueryRequest(BaseModel):
    user_id: int  # Add user_id to the request model
    session_id: str  # Unique session ID for maintaining context
    user_query: str

# Define request model for session start
class StartSessionRequest(BaseModel):
    user_id: int

@app.get("/")
def home():
    return {"message": "Server is up and running."}

@app.post("/start_session")
def start_session(request: StartSessionRequest):
    """Start a new session for a user"""
    session_id = str(uuid.uuid4())  # Generate unique session ID
    sessions_collection.insert_one({"user_id": request.user_id, "session_id": session_id, "history": []})
    return {"message": "Session started", "session_id": session_id}

@app.post("/query")
async def query_qdrant(request: QueryRequest):
    try:
        # logging.info(f"Received request: {request}")  # Debugging

        # Fetch session document
        session_document = sessions_collection.find_one({"user_id": request.user_id, "session_id": request.session_id})

        if not session_document:
            logging.warning(f"No session found for user {request.user_id}, creating a new one.")
            session_id = str(uuid.uuid4())
            sessions_collection.insert_one({"user_id": request.user_id, "session_id": session_id, "history": []})
            request.session_id = session_id

        chat_history: List[Dict] = session_document.get("history", []) if session_document else []
        # logging.info(f"Chat history: {chat_history}")  # Debugging

        # Pass chat history as context to retriever annd get response
        response = get_response(query=request.user_query, retriever=retriever, chat_history=chat_history)
        # logging.info(f"Generated response: {response}")  # Debugging

        # Update chat history with new query and response
        new_history_entry = {"query": request.user_query, "response": response}
        chat_history.append(new_history_entry)

        # Limit the history to the context window
        if len(chat_history) > CONTEXT_WINDOW:
            chat_history = chat_history[-CONTEXT_WINDOW:]

        # Update the session document in MongoDB
        sessions_collection.update_one(
            {"user_id": request.user_id, "session_id": request.session_id},
            {"$set": {"history": chat_history}},
            upsert=True
        )

        return {"answer": response}
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

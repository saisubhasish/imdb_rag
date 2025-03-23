import os
import certifi
import uvicorn
import warnings
from typing import List, Dict
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient
from fastapi import FastAPI, HTTPException

from src.utils import get_vector_store, get_retriever, get_response
from src.config import QDRANT_COLLECTION_NAME, QDRANT_HOST, QDRANT_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, MODEL_NAME_LLAMA

warnings.filterwarnings("ignore")

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())  # SSL handshake failed
db = client["chat_db"]  # Database Name
users_collection = db["users"]  # Collection Name

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
    user_query: str

@app.get("/")
def home():
    return {"message": "Server is up and running."}

@app.post("/query")
async def query_qdrant(request: QueryRequest):
    try:
        # Fetch or create user document
        user_document = users_collection.find_one({"user_id": request.user_id})
        if not user_document:
            user_document = {"user_id": request.user_id, "history": []}
            users_collection.insert_one(user_document)

        # Get the user's chat history
        chat_history: List[Dict] = user_document.get("history", [])

        # Pass the chat history as context to the retriever
        response = get_response(query=request.user_query, retriever=retriever, chat_history=chat_history)

        # Update chat history with the new query and response
        new_history_entry = {"query": request.user_query, "response": response}
        chat_history.append(new_history_entry)

        # Limit the history to the context window
        if len(chat_history) > CONTEXT_WINDOW:
            chat_history = chat_history[-CONTEXT_WINDOW:]

        # Update the user document in MongoDB
        users_collection.update_one(
            {"user_id": request.user_id},
            {"$set": {"history": chat_history}}
        )

        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

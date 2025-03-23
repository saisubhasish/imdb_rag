import os
import certifi
import uvicorn
import warnings
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
        # Get response from the retriever
        response = get_response(query=request.user_query, retriever=retriever)

        # Find or create user document
        user_document = users_collection.find_one({"user_id": request.user_id})
        if not user_document:
            # Create a new user document if it doesn't exist
            user_document = {"user_id": request.user_id, "history": []}
            users_collection.insert_one(user_document)

        # Update chat history
        new_history_entry = {"query": request.user_query, "response": response}
        users_collection.update_one(
            {"user_id": request.user_id},
            {"$push": {"history": new_history_entry}}
        )

        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

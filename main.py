import uuid
import certifi
import uvicorn
import warnings
from typing import Annotated
from typing import List, Dict
from datetime import timedelta
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials

from src.logger import logging
from src.config import QDRANT_COLLECTION_NAME, QDRANT_HOST, QDRANT_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, MODEL_NAME_LLAMA, MONGODB_URI, ACCESS_TOKEN_EXPIRE_MINUTES, CONTEXT_WINDOW, users_collection, sessions_collection
from src.utils import get_vector_store, get_retriever, get_response, Token, create_access_token, authenticate_user, get_password_hash, get_user, verify_token, UserInDB


warnings.filterwarnings("ignore")

# Security
security = HTTPBearer()

# Create FastAPI app
app = FastAPI()

# Configures CORS to allow cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Defines query request structure with user_id, session_id, and user_query.
class QueryRequest(BaseModel):
    user_id: str  # Add user_id to the request model
    session_id: str  # Unique session ID for maintaining context
    user_query: str

# Defines the session start request.
class StartSessionRequest(BaseModel):
    user_id: str  

# Defines user registration details.
class UserCreate(BaseModel):
    username: str
    password: str
    email: str | None = None
    full_name: str | None = None

# Validates authentication token and retrieves user info.
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = await verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_user(username=payload.get("sub"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/")
async def home():
    return {"message": "Server is up and running."}

# Checks if username exists, hashes the password, and saves user to MongoDB.
@app.post("/register")
async def register_user(user_data: UserCreate):
    existing_user = await get_user(username=user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = await get_password_hash(user_data.password)
    
    user_dict = {
        "username": user_data.username,
        "hashed_password": hashed_password,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "disabled": False
        # Let MongoDB generate the _id automatically
    }
    
    result = users_collection.insert_one(user_dict)
    return {
        "message": "User created successfully",
        "user_id": str(result.inserted_id)  # Return string ID
    }

# Returns user details after authentication.
@app.get("/user_info")
async def get_user_info(current_user: UserInDB = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "user_id": current_user.id,  # Now returns string ID
        "email": current_user.email,
        "full_name": current_user.full_name
    }

# Authenticates user and generates a JWT access token.
@app.post("/generate_access_token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

# Creates a new session and stores it in MongoDB.
@app.post("/start_session")
async def start_session(request: StartSessionRequest, current_user: UserInDB = Depends(get_current_user)):
    session_id = str(uuid.uuid4())
    sessions_collection.insert_one({
        "user_id": request.user_id,  # Now accepts string
        "session_id": session_id,
        "history": [],
        "username": current_user.username
    })
    return {"message": "Session started", "session_id": session_id}

# Fetches session history, queries Qdrant for relevant data, generates a response, and stores conversation history.
@app.post("/query")
async def query_qdrant(
    request: QueryRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    try:
        # Verify session belongs to authenticated user
        session_document = sessions_collection.find_one({
            "user_id": request.user_id,
            "session_id": request.session_id,
            "username": current_user.username
        })

        if not session_document:
            raise HTTPException(status_code=404, detail="Session not found or unauthorized")

        chat_history: List[Dict] = session_document.get("history", [])

        # Get vector store and retriever
        vector_store = await get_vector_store(
            QDRANT_HOST=QDRANT_HOST,
            API_KEY=QDRANT_API_KEY,
            QDRANT_COLLECTION_NAME=QDRANT_COLLECTION_NAME,
            OPENAI_API_KEY=OPENAI_API_KEY
        )
        retriever = await get_retriever(
            GROQ_API_KEY=GROQ_API_KEY,
            MODEL_NAME_LLAMA=MODEL_NAME_LLAMA,
            vector_store=vector_store
        )

        # Get and store response
        response = await get_response(
            query=request.user_query,
            retriever=retriever,
            chat_history=chat_history
        )

        # Update history
        new_history_entry = {"query": request.user_query, "response": response}
        chat_history.append(new_history_entry)
        if len(chat_history) > CONTEXT_WINDOW:
            chat_history = chat_history[-CONTEXT_WINDOW:]

        sessions_collection.update_one(
            {"_id": session_document["_id"]},
            {"$set": {"history": chat_history}}
        )

        return {"answer": response}
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

import pandas as pd
import qdrant_client
import re, os, jwt, sys
from typing import List, Dict
from pydantic import BaseModel
from pymongo import MongoClient
from langchain_groq import ChatGroq
from langchain_qdrant import Qdrant
from langchain.schema import Document
from passlib.context import CryptContext
from langchain.chains import RetrievalQA
from fastapi import HTTPException, status
from langchain_openai import OpenAIEmbeddings
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from qdrant_client.http.models import VectorParams, Distance
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.logger import logging
from src.exception import ImdbException
from src.config import MONGODB_URI


async def format_data_n_get_documents(DATA_DUMP_FILE_PATH):
    """
    Read the IMDb data dump CSV file and convert each row into a LangChain Document format.

    Args:
        DATA_DUMP_FILE_PATH (str): The path to the IMDb data dump CSV file.

    Returns:
        List[Document]: A list of LangChain Document objects, each containing metadata and page content.
    """
    df = pd.read_csv(DATA_DUMP_FILE_PATH)

    try:
        # Convert rows into LangChain Document format containing metadata and structured content.
        documents = [
            Document(           # Maintain metadata
                metadata={"title": row["Series_Title"], "year": row["Released_Year"], "genre": row["Genre"], "rating": row["IMDB_Rating"]},
                page_content=(
                    f"Movie: {row['Series_Title']}, Released: {row['Released_Year']}, Genre: {row['Genre']}, "
                    f"Rating: {row['IMDB_Rating']}, Director: {row['Director']},  Overview: {row['Overview']}"
                    f"Starring: {row['Star1']}, {row['Star2']}, {row['Star3']}, {row['Star4']}."
                )
            )
            for _, row in df.iterrows()
        ]
    except Exception as e:
        raise ImdbException(e, sys)

    return documents

def get_vector_store(QDRANT_HOST, API_KEY, QDRANT_COLLECTION_NAME, OPENAI_API_KEY):
    """
    Initialize Qdrant client and vector store with OpenAI embeddings, to set Up Qdrant Vector Store.

    Args:
        QDRANT_HOST (str): The URL of the Qdrant server.
        API_KEY (str): The API key for the Qdrant server.
        QDRANT_COLLECTION_NAME (str): The name of the Qdrant collection.
        OPENAI_API_KEY (str): The API key for the OpenAI embeddings.

    Returns:
        Qdrant: The initialized vector store with OpenAI embeddings.
    """

    try:
        # Initialize Qdrant Client
        client = qdrant_client.QdrantClient(url=QDRANT_HOST, api_key=API_KEY, timeout=120)

        # Check if collection exists, then create it
        if not client.collection_exists(QDRANT_COLLECTION_NAME):
            client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)    # 1536 used by OpenAI embeddings
            )

    except Exception as e:
        raise ImdbException(e, sys)

    # Initialize embeddings
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

    # Connects Qdrant with LangChain for storing and retrieving vectorized documents.
    vector_store = Qdrant(
        client=client,
        collection_name=QDRANT_COLLECTION_NAME,
        embeddings=embeddings
    )
    
    return vector_store

async def get_chunked_data(documents, CHUNK_SIZE, CHUNK_OVERLAP):
    """
    Asynchronous function to split documents into smaller text chunks.

    Args:
        documents (list[Document]): List of documents to split.
        CHUNK_SIZE (int): Size of each chunk in characters.
        CHUNK_OVERLAP (int): Overlap of each chunk in characters.

    Returns:
        list[str]: List of chunked documents as strings.
    """
    try:
        # Define text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n"]
        )

        # Process documents and split text correctly
        chunked_documents = []
        for doc in documents:
            chunks = text_splitter.split_text(doc.page_content)  # Use page_content instead of passing Document object
            chunked_documents.extend(chunks)

        # Display some chunked samples
        logging.info(chunked_documents[:5])

        return chunked_documents
    
    except Exception as e:
        raise ImdbException(e, sys)

async def store_data_to_vdb(vector_store, chunked_documents):
    """
    Asynchronous function to store chunked documents to Vector DB (Qdrant).
    
    Args:
        vector_store (Qdrant): Qdrant vector store.
        chunked_documents (list[str]): List of chunked documents as strings.
    
    Returns:
        None
    """
    try:
        # Store data to Qdrant
        vector_store.add_texts(chunked_documents)
        logging.info("Data stored to Vector DB successfully")

    except Exception as e:
        raise ImdbException(e, sys)

def get_retriever(GROQ_API_KEY, MODEL_NAME_LLAMA, vector_store):
    """
    Asynchronous function to get a retriever instance from ChatGroq and Qdrant vector store.

    Args:
        GROQ_API_KEY (str): API key for ChatGroq.
        MODEL_NAME_LLAMA (str): Model name for the LLaMA model.
        vector_store (Qdrant): Qdrant vector store.

    Returns:
        retriever (RetrievalQA): Retriever instance.

    Raises:
        ImdbException: If there is an error in initializing the retriever.
    """
    try:
        # Initialize retriever
        retriever= RetrievalQA.from_chain_type(
            llm=ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME_LLAMA, temperature=0.5, streaming=True),
            chain_type='stuff',
            retriever=vector_store.as_retriever()
            )
        return retriever
    
    except Exception as e:
        raise ImdbException(e, sys)
    
def get_response(query: str, retriever, chat_history: List[Dict] = None) -> str:
    """
    Gets a response to a query from the model.

    Args:
        query (str): The query to get a response to.
        retriever (RetrievalQA): The retriever to get the response from.
        chat_history (Optional[List[Dict]]): The chat history to use as context. Defaults to None.

    Returns:
        str: The response to the query.
    """
    if chat_history is None:        # Corner case
        chat_history = []

    # Format the chat history into a context string
    context = "\n".join([f"User: {entry['query']}\nBot: {entry['response']}" for entry in chat_history])

    logging.info(f"Context: {context}")
    logging.info(f"User's query: {query}")

    # Combine the context with the current query
    full_query = f"{context}\nUser: {query}"
    logging.info(f"Full query: {full_query}")

    # Get the response from the retriever
    response = retriever.invoke(full_query)
    logging.info(f"Response from model: {response}\n")

    # Clean up the response if necessary
    if 'query' in response:
        response = remove_query(response)
    if "<think>" in response:
        response = remove_think_tags(response)

    return response

def remove_think_tags(text):
    """
    Remove any "<think> </think>" tags from the text to prevent the model from
    thinking out loud. This is useful for removing the model's internal
    thought process from the response.

    Args:
        text (str): The text to remove the tags from.

    Returns:
        str: The text with any "<think>" tags removed.
    """
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def remove_query(text):
    """
    Remove the query from the text.

    Args:
        text (Dict[str, str]): The text to remove the query from. The text should have a key "result" with the result as the value.

    Returns:
        str: The text with the query removed.
    """
    return text['result']

# JWT Authentication Constants
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OAuth2 scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str
    id: str | None = None

class RequestState(BaseModel):
    user_id: str
    session_id: str
    message: str

# JWT Authentication Functions
async def verify_password(plain_password, hashed_password):
    """
    Verifies that a plain text password matches its hashed counterpart.

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password to verify against.

    Returns:
        bool: True if the plain text password matches the hashed password, False otherwise.
    """

    return pwd_context.verify(plain_password, hashed_password)

async def get_password_hash(password):
    """
    Generates a hashed version of the given password.

    Args:
        password (str): The plain text password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)

async def get_user(username: str):
    """
    Retrieves a user from the database based on their username.

    Args:
        username (str): The username to retrieve the user by.

    Returns:
        UserInDB: The user associated with the given username, or None if no user is found.
    """
    client = MongoClient(MONGODB_URI)
    db = client["chat_db"]
    users_collection = db["users"]
    user_data = users_collection.find_one({"username": username})
    if user_data:
        # Convert MongoDB document to Pydantic model
        user_data["id"] = str(user_data["_id"])  # Ensure string type
        return UserInDB(**user_data)
    return None

async def authenticate_user(username: str, password: str):
    """
    Authenticates a user based on their username and password.

    Args:
        username (str): The username to authenticate.
        password (str): The password to authenticate with.

    Returns:
        UserInDB | False: The authenticated user if successful, False otherwise.
    """
    user = await get_user(username)
    if not user:
        return False
    if not await verify_password(password, user.hashed_password):
        return False
    return user

async def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Creates a JWT access token based on the given data and optional expiration delta.

    Args:
        data (dict): The data to encode in the JWT token.
        expires_delta (timedelta | None, optional): The expiration delta for the token. Defaults to None.

    Raises:
        HTTPException: If an error occurs while creating the access token.

    Returns:
        str: The encoded JWT access token.
    """
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logging.error(f"Error creating access token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token"
        )

async def verify_token(token: str):
    """
    Verifies and decodes a JWT token.

    Args:
        token (str): The JWT token to verify.

    Returns:
        dict | None: The decoded payload if the token is valid, None otherwise.
    """

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
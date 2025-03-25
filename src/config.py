import os
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

# Qdrant Configs
QDRANT_COLLECTION_NAME = "imdb"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_HOST=os.getenv("QDRANT_HOST")

# DB Connection
MONGODB_URI = os.getenv("MONGODB_URI")
# MongoDB Connection
client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())  # SSL handshake failed
db = client["chat_db"]  # Database Name
sessions_collection = db["sessions"]  # Collection Name
users_collection = db["users"]

# LLM API Keys & COnfigs
GROQ_API_KEY=os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME_LLAMA='deepseek-r1-distill-llama-70b'

#  Data configs
DATA_DUMP_FILE_PATH="C:/Users/saisu/Documents/Learning/RAG_project_imdb/data/imdb_top_1000.csv"
CHUNK_SIZE=1000
CHUNK_OVERLAP=50

ACCESS_TOKEN_EXPIRE_MINUTES = 5184000  # 10 years

# Define a maximum context window (for last 5 messages)
CONTEXT_WINDOW = 5
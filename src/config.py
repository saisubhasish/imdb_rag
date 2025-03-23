import os
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

# Qdrant Configs
QDRANT_COLLECTION_NAME = "imdb"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_HOST="https://2e65de7d-6361-40e7-8035-b288c90181a1.us-west-1-0.aws.cloud.qdrant.io:6333"
# DB Connection
MONGODB_URI = os.getenv("MONGODB_URI")
# LLM API Keys & COnfigs
GROQ_API_KEY=os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME_LLAMA='llama-3.2-11b-vision-preview'
#  Data configs
DATA_DUMP_FILE_PATH="C:/Users/saisu/Documents/Learning/RAG_project_imdb/data/imdb_top_1000.csv"
CHUNK_SIZE=1000
CHUNK_OVERLAP=50
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST")
API_KEY = os.getenv("API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_COLLECTION_NAME = "imdb"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME_LLAMA='deepseek-r1-distill-llama-70b'
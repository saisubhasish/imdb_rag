import os
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("API_KEY")
GROQ_API_KEY=os.getenv("GROQ_API_KEY")
MODEL_NAME_LLAMA='llama-3.2-11b-vision-preview'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_COLLECTION_NAME = "imdb"
QDRANT_HOST = os.getenv("QDRANT_HOST")

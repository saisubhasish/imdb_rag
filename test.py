import warnings

from src.utils import get_vector_store, get_retriever, get_response
from src.config import QDRANT_COLLECTION_NAME, QDRANT_HOST, QDRANT_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, MODEL_NAME_LLAMA


warnings.filterwarnings("ignore")

# Connect vector store
vector_store = get_vector_store(QDRANT_HOST=QDRANT_HOST, API_KEY=QDRANT_API_KEY, QDRANT_COLLECTION_NAME=QDRANT_COLLECTION_NAME, OPENAI_API_KEY=OPENAI_API_KEY)


retriever=get_retriever(GROQ_API_KEY=GROQ_API_KEY, MODEL_NAME_LLAMA=MODEL_NAME_LLAMA, vector_store=vector_store)


query="Inception, who are actors in it?"
print(get_response(query=query, retriever=retriever))


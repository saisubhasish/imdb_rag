from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import qdrant_client
from dotenv import load_dotenv
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
import re

# Load environment variables
load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST")
API_KEY = os.getenv("API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
QDRANT_COLLECTION_NAME = "imdb"
MODEL_NAME_LLAMA = "deepseek-r1-distill-llama-70b"

# Initialize FastAPI
app = FastAPI()

# Initialize Qdrant client
client = qdrant_client.QdrantClient(url=QDRANT_HOST, api_key=API_KEY, timeout=120)

# Initialize embeddings
embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

# Connect to vector store
vector_store = Qdrant(client=client, collection_name=QDRANT_COLLECTION_NAME, embeddings=embeddings)

# Initialize QA chain
qa = RetrievalQA.from_chain_type(
    llm=ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME_LLAMA, temperature=0.5),
    chain_type="stuff",
    retriever=vector_store.as_retriever()
)

# Function to clean response
def remove_think_tags(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

# Request model
class QueryRequest(BaseModel):
    question: str

# API endpoint for answering questions
@app.post("/ask")
async def ask_question(request: QueryRequest):
    try:
        response = qa.invoke(request.question)
        if "<think>" in response:
            response = remove_think_tags(response)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the app (if needed for local execution)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# TODO: FIx issues reffering the notebook
import uvicorn
import warnings
import qdrant_client
from pydantic import BaseModel
from langchain_qdrant import Qdrant
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from fastapi import FastAPI, HTTPException
from langchain_openai import OpenAIEmbeddings

from src.utils import remove_think_tags, remove_query
from src.config import QDRANT_COLLECTION_NAME, QDRANT_HOST, API_KEY, OPENAI_API_KEY, GROQ_API_KEY, MODEL_NAME_LLAMA


warnings.filterwarnings("ignore")

# Initialize Qdrant Client
client = qdrant_client.QdrantClient(url=QDRANT_HOST, api_key=API_KEY, timeout=120)

# Initialize embeddings
embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

# Connect vector store
vector_store = Qdrant(
    client=client,
    collection_name=QDRANT_COLLECTION_NAME,
    embeddings=embeddings
)

qa=RetrievalQA.from_chain_type(
    llm=ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME_LLAMA, temperature=0.5, streaming=True),
    chain_type='stuff',
    retriever=vector_store.as_retriever())

def get_response(query):
    response=qa.invoke(query)
    if 'query' in response:
        response=remove_query(response)
    if "<think>" in response:
        response=remove_think_tags(response)
    return response


# query="Inception, who are actors in it?"
# print(get_response(query=query))

app=FastAPI()

# Define request model
class QueryRequest(BaseModel):
    question: str

@app.post("/query")
async def query_qdrant(request: QueryRequest):
    try:
        response=get_response(request.question)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
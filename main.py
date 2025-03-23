import uvicorn
import warnings
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

from src.utils import get_vector_store, get_retriever, get_response
from src.config import QDRANT_COLLECTION_NAME, QDRANT_HOST, QDRANT_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, MODEL_NAME_LLAMA


warnings.filterwarnings("ignore")

app=FastAPI()

# Connect vector store
vector_store = get_vector_store(QDRANT_HOST=QDRANT_HOST, API_KEY=QDRANT_API_KEY, QDRANT_COLLECTION_NAME=QDRANT_COLLECTION_NAME, OPENAI_API_KEY=OPENAI_API_KEY)

retriever=get_retriever(GROQ_API_KEY=GROQ_API_KEY, MODEL_NAME_LLAMA=MODEL_NAME_LLAMA, vector_store=vector_store)

# Define request model
class QueryRequest(BaseModel):
    user_query: str

@app.post("/query")
async def query_qdrant(request: QueryRequest):
    try:
        response=get_response(query=request.user_query, retriever=retriever)
        return {"answer": response}
    except Exception as e:  
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
import re
import pandas as pd
import qdrant_client
from typing import List, Dict
from langchain_groq import ChatGroq
from langchain_qdrant import Qdrant
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain_openai import OpenAIEmbeddings
from qdrant_client.http.models import VectorParams, Distance
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.logger import logging
from src.exception import ImdbException


def format_data_n_get_documents(DATA_DUMP_FILE_PATH):
    # Load IMDb dataset
    df = pd.read_csv(DATA_DUMP_FILE_PATH)

    try:
        # Convert rows into LangChain Document format
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
        raise ImdbException(e)

    return documents

def get_vector_store(QDRANT_HOST, API_KEY, QDRANT_COLLECTION_NAME, OPENAI_API_KEY):
    try:
        # Initialize Qdrant Client
        client = qdrant_client.QdrantClient(url=QDRANT_HOST, api_key=API_KEY, timeout=120)

        # Check if collection exists, then create it
        if not client.collection_exists(QDRANT_COLLECTION_NAME):
            client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )

    except Exception as e:
        raise ImdbException(e)

    # Initialize embeddings
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

    # Connect vector store
    vector_store = Qdrant(
        client=client,
        collection_name=QDRANT_COLLECTION_NAME,
        embeddings=embeddings
    )
    
    return vector_store

def get_chunked_data(documents, CHUNK_SIZE, CHUNK_OVERLAP):
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
        raise ImdbException(e)


def store_data_to_vdb(vector_store, chunked_documents):
    try:
        # Store data to Qdrant
        vector_store.add_texts(chunked_documents)
        logging.info("Data stored to Vector DB successfully")

    except Exception as e:
        raise ImdbException(e)

def get_retriever(GROQ_API_KEY, MODEL_NAME_LLAMA, vector_store):
    try:
        # Initialize retriever
        retriever=RetrievalQA.from_chain_type(
            llm=ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME_LLAMA, temperature=0.5, streaming=True),
            chain_type='stuff',
            retriever=vector_store.as_retriever()
            )
        return retriever
    
    except Exception as e:
        raise ImdbException(e)
    

def get_response(query: str, retriever, chat_history: List[Dict] = None) -> str:
    # Check if chat history is provided
    if chat_history is None:        # Corner case
        chat_history = []

    # Format the chat history into a context string
    context = "\n".join([f"User: {entry['query']}\nBot: {entry['response']}" for entry in chat_history])

    # Combine the context with the current query
    full_query = f"{context}\nUser: {query}"

    # Get the response from the retriever
    response = retriever.invoke(full_query)

    # Clean up the response if necessary
    if 'query' in response:
        response = remove_query(response)
    if "<think>" in response:
        response = remove_think_tags(response)

    return response

def remove_think_tags(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def remove_query(text):
    return text['result']
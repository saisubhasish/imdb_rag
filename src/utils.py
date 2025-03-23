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
    """
    Function to format the IMDb data dump into LangChain Document format
    and return a list of Documents.

    Args:
        DATA_DUMP_FILE_PATH (str): Path to the IMDb data dump CSV file

    Returns:
        List[Document]: List of Documents with metadata and page_content
    """
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
    """
    Function to initialize a Qdrant vector store with an OpenAI embeddings model.

    Args:
        QDRANT_HOST (str): Qdrant server URL
        API_KEY (str): Qdrant API key
        QDRANT_COLLECTION_NAME (str): Qdrant collection name
        OPENAI_API_KEY (str): OpenAI API key

    Returns:
        Qdrant: Qdrant vector store
    """
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
    """
    Function to split documents into smaller text chunks using LangChain's RecursiveCharacterTextSplitter.

    Args:
        documents (List[Document]): List of Documents with metadata and page_content
        CHUNK_SIZE (int): Size of each chunk
        CHUNK_OVERLAP (int): Overlap size between chunks

    Returns:
        List[str]: List of chunked text strings
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
        raise ImdbException(e)


def store_data_to_vdb(vector_store, chunked_documents):
    """
    Function to store the chunked data into a Qdrant vector store.

    Args:
        vector_store (Qdrant): Qdrant vector store
        chunked_documents (List[str]): List of chunked text strings

    Returns:
        None

    Raises:
        ImdbException: If an error occurs during storing the data to vector store
    """
    try:
        # Store data to Qdrant
        vector_store.add_texts(chunked_documents)
        logging.info("Data stored to Vector DB successfully")

    except Exception as e:
        raise ImdbException(e)

def get_retriever(GROQ_API_KEY, MODEL_NAME_LLAMA, vector_store):
    """
    Function to initialize a RetrievalQA retriever using the specified Groq API key, model name, and Qdrant vector store.

    Args:
        GROQ_API_KEY (str): API key for accessing the Groq model
        MODEL_NAME_LLAMA (str): Name of the LLaMA model to use
        vector_store (Qdrant): Qdrant vector store to be used as the retriever

    Returns:
        RetrievalQA: Initialized retriever object for performing retrieval-based QA

    Raises:
        ImdbException: If an error occurs during retriever initialization
    """

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
    """
    Function to get a response from the retriever given the user's query and an optional chat history.

    Args:
        query (str): The user's query
        retriever: The retriever object to use for generating the response
        chat_history (List[Dict], optional): The chat history to use as context for the response. Defaults to None.

    Returns:
        str: The response from the retriever
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
    """Remove think tags from the text. Think tags are strings that start with "<think>" and end with "</think>" (inclusive).

    Args:
        text (str): The text to remove think tags from

    Returns:
        str: The text with think tags removed
    """
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def remove_query(text):
    """
    Extract and return the 'result' field from a given text dictionary.

    Args:
        text (dict): A dictionary containing various fields, including 'result'.

    Returns:
        str: The value associated with the 'result' key in the text dictionary.
    """

    return text['result']
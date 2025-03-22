import re
import pandas as pd
import qdrant_client
from langchain_groq import ChatGroq
from langchain_qdrant import Qdrant
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain_openai import OpenAIEmbeddings
from qdrant_client.http.models import VectorParams, Distance
from langchain.text_splitter import RecursiveCharacterTextSplitter


def format_data_n_get_documents(DATA_DUMP_FILE_PATH):
    # Load IMDb dataset
    df = pd.read_csv(DATA_DUMP_FILE_PATH)

    # Convert rows into LangChain Document format
    documents = [
        Document(
            metadata={"title": row["Series_Title"], "year": row["Released_Year"], "genre": row["Genre"], "rating": row["IMDB_Rating"]},
            page_content=(
                f"Movie: {row['Series_Title']}, Released: {row['Released_Year']}, Genre: {row['Genre']}, "
                f"Rating: {row['IMDB_Rating']}, Director: {row['Director']},  Overview: {row['Overview']}"
                f"Starring: {row['Star1']}, {row['Star2']}, {row['Star3']}, {row['Star4']}."
            )
        )
        for _, row in df.iterrows()
    ]

    return documents

def get_vector_store(QDRANT_HOST, API_KEY, QDRANT_COLLECTION_NAME, OPENAI_API_KEY):
    # Initialize Qdrant Client
    client = qdrant_client.QdrantClient(url=QDRANT_HOST, api_key=API_KEY, timeout=120)

    # Check if collection exists, then create it
    if not client.collection_exists(QDRANT_COLLECTION_NAME):
        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )

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
    print(chunked_documents[:5])

    return chunked_documents

def store_data_to_vdb(vector_store, chunked_documents):
    vector_store.add_texts(chunked_documents)

    return {"message": "Data stored to Vector DB successfully"}

def get_retriever(GROQ_API_KEY, MODEL_NAME_LLAMA, vector_store):
    retriever=RetrievalQA.from_chain_type(
        llm=ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME_LLAMA, temperature=0.5, streaming=True),
        chain_type='stuff',
        retriever=vector_store.as_retriever())
    return retriever

def get_response(query, retriever):
    response=retriever.invoke(query)
    if 'query' in response:
        response=remove_query(response)
    if "<think>" in response:
        response=remove_think_tags(response)
    return response

def remove_think_tags(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def remove_query(text):
    return text['result']
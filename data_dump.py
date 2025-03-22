import os
import pandas as pd
import qdrant_client
from dotenv import load_dotenv
from langchain.schema import Document
from langchain.vectorstores import Qdrant
from langchain.embeddings import OpenAIEmbeddings
from qdrant_client.http.models import VectorParams, Distance
from langchain.text_splitter import RecursiveCharacterTextSplitter




load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST")
API_KEY = os.getenv("API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_COLLECTION_NAME = "imdb"

# Load IMDb dataset
df = pd.read_csv("C:/Users/saisu/Documents/Learning/RAG_project_imdb/data/imdb_top_1000.csv")

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

# Initialize Qdrant Client
client = qdrant_client.QdrantClient(url=QDRANT_HOST, api_key=API_KEY, timeout=120)

# Check if collection exists, then create it
if not client.collection_exists(QDRANT_COLLECTION_NAME):
    client.create_collection(
        collection_name=QDRANT_COLLECTION_NAME,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
    )

# Initialize embeddings
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
embeddings = OpenAIEmbeddings()

# Connect vector store
vector_store = Qdrant(
    client=client,
    collection_name=QDRANT_COLLECTION_NAME,
    embeddings=embeddings
)

# Define text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=50,
    separators=["\n"]
)

# Process documents and split text correctly
chunked_documents = []
for doc in documents:
    chunks = text_splitter.split_text(doc.page_content)  # Use page_content instead of passing Document object
    chunked_documents.extend(chunks)

# Display some chunked samples
print(chunked_documents[:5])

vector_store.add_texts(chunked_documents)
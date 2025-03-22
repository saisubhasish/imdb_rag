import warnings

from src.utils import format_data_n_get_documents, get_vector_store, get_chunked_data, store_data_to_vdb
from src.config import DATA_DUMP_FILE_PATH, QDRANT_HOST, QDRANT_API_KEY, QDRANT_COLLECTION_NAME, CHUNK_SIZE, CHUNK_OVERLAP, OPENAI_API_KEY


warnings.filterwarnings("ignore")

if __name__=="__main__":
    documents=format_data_n_get_documents(DATA_DUMP_FILE_PATH=DATA_DUMP_FILE_PATH)

    vector_store=get_vector_store(QDRANT_HOST=QDRANT_HOST, API_KEY=QDRANT_API_KEY, QDRANT_COLLECTION_NAME=QDRANT_COLLECTION_NAME, OPENAI_API_KEY=OPENAI_API_KEY)

    chunked_documents=get_chunked_data(documents=documents, CHUNK_SIZE=CHUNK_SIZE, CHUNK_OVERLAP=CHUNK_OVERLAP)

    store_data_to_vdb(vector_store=vector_store, chunked_documents=chunked_documents)
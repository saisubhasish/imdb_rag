import os
import warnings, asyncio
from dotenv import load_dotenv, find_dotenv

from src.utils import format_data_n_get_documents, get_vector_store, get_chunked_data, store_data_to_vdb
from src.config import DATA_DUMP_FILE_PATH, QDRANT_COLLECTION_NAME, CHUNK_SIZE, CHUNK_OVERLAP, OPENAI_API_KEY


load_dotenv(find_dotenv())

warnings.filterwarnings("ignore")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_HOST="https://f6599bdf-ee6e-46fb-a827-7d34ff7d1aeb.us-west-2-0.aws.cloud.qdrant.io:6333"

async def main():
    documents= await format_data_n_get_documents(DATA_DUMP_FILE_PATH=DATA_DUMP_FILE_PATH)

    vector_store= await get_vector_store(QDRANT_HOST=QDRANT_HOST, API_KEY=QDRANT_API_KEY, QDRANT_COLLECTION_NAME=QDRANT_COLLECTION_NAME, OPENAI_API_KEY=OPENAI_API_KEY)

    chunked_documents= await get_chunked_data(documents=documents, CHUNK_SIZE=CHUNK_SIZE, CHUNK_OVERLAP=CHUNK_OVERLAP)

    await store_data_to_vdb(vector_store=vector_store, chunked_documents=chunked_documents)


if __name__ == "__main__":
    asyncio.run(main())
# IMDB RAG POC
![Screenshot 2025-03-23 214813](https://github.com/user-attachments/assets/62ed1b28-d692-4b3e-aed3-aa001b2110cf)

## Flow DIagram

![IMDB drawio](https://github.com/user-attachments/assets/a5f9000f-8f85-482b-ae10-6965d4e45c26)

# IMDB Movie Bot

The IMDB Movie Bot is a prototype system designed to help users find movies from an IMDb dataset using natural language queries. The system leverages a Large Language Model (LLM) and a vector store to process user queries, extract relevant filters (e.g., genre, actors, plot details), and return a list of movies with a natural language summary. Built using the Langchain framework, the system also supports follow-up questions related to the initial query.

---

## **Features**

- **Natural Language Query Processing**: Interpret conversational queries to find movies.
- **Filter Extraction**: Extract filters like genre, actors, and plot details from user queries.
- **Vector Store Integration**: Efficiently search and retrieve movies using a vector store.
- **Natural Language Summaries**: Generate summaries of movie results in natural language.
- **Follow-Up Interaction**: Handle follow-up questions based on the initial query context.
- **User Authentication**: Manage user sessions and maintain context for follow-up queries.

---

## **Technology Stack**

- **Framework**: [Langchain](https://www.langchain.com/)
- **Vector Store**: [Qdrant](https://qdrant.tech/)
- **LLM**: [Groq](https://groq.com/) (LLaMA 3.2)
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/)
- **Frontend**: [Streamlit](https://streamlit.io/)
- **Database**: [MongoDB](https://www.mongodb.com/)
- **Embeddings**: [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- **Containerization**: [Docker](https://www.docker.com/)

---

## **System Setup**

### **Prerequisites**

1. **Docker**: Install Docker from [here](https://docs.docker.com/get-docker/).
2. **Python**: Ensure Python 3.11.11 is installed.
3. **Environment Variables**: Create a `.env` file in the root directory with the following variables:

   ```env
   GROQ_API_KEY="your_groq_api_key"
   OPENAI_API_KEY="your_openai_api_key"
   QDRANT_API_KEY="your_qdrant_api_key"
   QDRANT_HOST="your_qdrant_host"
   MONGODB_URI="your_mongodb_uri"

## Steps to Run the System
**1. Clone the Repository**:

```
git clone https://github.com/your-username/imdb-movie-bot.git
cd imdb-movie-bot
```

**2. Build and Run the Docker Containers**:

```
docker-compose build
docker-compose up
```
**3.Access the Application**:
- FastAPI Backend: http://localhost:8080
- Streamlit Frontend: http://localhost:8501

**4. Streamlit UI guide**:
Enter your user ID under “Enter your User ID:” field.
Enter your queries under “Ask your question:” field.


## Docker Command	Description
- docker-compose build:	Build the Docker images.
- docker-compose up:	Start the services.
- docker-compose up -d:	Start the services in detached mode.
- docker-compose down:	Stop and remove the services.
- docker-compose logs -f:	View logs for the services.
- docker-compose ps:	List running services.

## Usage
### User Interaction
1. **Start a Session**:
- Enter your User ID in the Streamlit interface and click "Start Session".
- A unique session ID will be generated and displayed.

2. **Submit a Query**:
- Enter a natural language query (e.g., "Find action movies with Tom Cruise from the 1990s").
- The system will process the query, extract filters, and return a list of relevant movies with a summary.

3. **Follow-Up Questions**:
- Ask follow-up questions related to the initial query (e.g., "Which one has the best reviews?").
- The system will maintain context and provide relevant responses.

## Code Structure

```
imdb-movie-bot/
├── data/                     # Dataset files
├── notebooks/                # Jupyter notebooks for experimentation
├── research_notebook/        # Research and development notes
├── src/                      # Source code
│   ├── config.py             # Configuration settings
│   ├── exception.py          # Custom exception handling
│   ├── logger.py             # Logging setup
│   ├── utils.py              # Utility functions
├── user_authentication/      # User authentication module
├── .dockerignore             # Files to ignore in Docker builds
├── .gitignore                # Files to ignore in Git
├── Dockerfile                # Dockerfile for containerization
├── LICENSE                   # License file
├── README.md                 # Project documentation
├── app.py                    # Streamlit frontend
├── compose.yaml              # Docker Compose configuration
├── data_dump.py              # Script for preprocessing and loading data
├── main.py                   # FastAPI backend
├── requirements.txt          # Python dependencies
└── test.py                   # Test scripts
```

## Flow Diagram
1. **User Query**:
- The user submits a natural language query via the Streamlit frontend.

2. **Query Processing**:
- The FastAPI backend processes the query using an LLM to extract filters and search terms.

3. **Vector Store Search**:
- The system queries the Qdrant vector store to retrieve relevant movies.

4. **Results Generation**:
- The LLM generates a natural language summary of the results.

5. **Follow-Up Interaction**:
- The system maintains context for follow-up questions and refines the search results.

## User Guide
### Starting a Session
1. Open the Streamlit frontend at http://localhost:8501.
2. Enter your User ID in the "Enter your User ID" field.
3. Click "Start Session" to generate a unique session ID.

### Submitting a Query
1. Enter your query in the "Ask your question" field (e.g., "Find action movies with Tom Cruise").
2. Click "Submit" to process the query and view the results.

### Follow-Up Questions
1. After submitting the initial query, you can ask follow-up questions (e.g., "Which one has the best reviews?").
2. The system will maintain context and provide relevant responses.

## Enhancements to be done
1. User signup, loging
2. Authentication Layer


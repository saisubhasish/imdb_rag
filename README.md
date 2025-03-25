# IMDB RAG POC
![Screenshot 2025-03-25 012110](https://github.com/user-attachments/assets/d6de1f1a-4315-4ee6-a4e6-b945941b1ba6)


## Architecture Overview
![imdb drawio (1)](https://github.com/user-attachments/assets/e9e7e1ad-f685-4db3-83fd-7ba7a384e6a3)

## Overview
The IMDB Movie Bot is a Retrieval-Augmented Generation (RAG) system that enables natural language search across a dataset of top 1000 IMDB movies. It combines vector search with LLM-powered response generation for intuitive movie discovery.

## Key Features
- 🗣️ Natural language query understanding
- � Context-aware follow-up questions
- 🏎️ High-performance vector search via Qdrant
- 🔒 JWT-based user authentication
- 📊 Session-based conversation history
- 🐳 Dockerized deployment

## Technology Stack
| Component               | Technology                          |
|-------------------------|-------------------------------------|
| Vector Database         | Qdrant Cloud                        |
| LLM Provider            | Groq (Llama 3 70B)                  |
| Embeddings              | OpenAI                              |
| Backend Framework       | FastAPI                             |
| Frontend                | Streamlit                           |
| Database                | MongoDB                             |
| Authentication          | JWT/OAuth2                          |
| Containerization        | Docker + Docker Compose             |

## Dataset
The system uses the [IMDB Top 1000 Movies Dataset](https://www.kaggle.com/datasets/harshitshankhdhar/imdb-dataset-of-top-1000-movies-and-tv-shows) from Kaggle.

## Getting Started

### Prerequisites
- Docker 20.10+
- Python 3.11
- API keys for:
  - Groq
  - OpenAI
  - Qdrant Cloud

### Installation
1. Clone the repository:
```
git clone https://github.com/your-username/imdb-movie-bot.git
cd imdb-movie-bot
```
2. Set up environment variables:
```
cp .env.example .env
# Fill in your API keys in the .env file
```
3. Build and launch services:
```
docker-compose up --build
```

### Accessing the System

Service	      URL

API Docs:	http://localhost:8080/docs

Web Interface:	http://localhost:8501

MongoDB Admin:	http://localhost:8081

## Usage Guide

1. User Authentication
- Register a new account via the Streamlit sidebar
- Login with your credentials to obtain a JWT token

2. Session Management
- Start a new session with your User ID
- Each session maintains independent conversation history

3. Making Queries

## Picture guide
![Screenshot 2025-03-25 012221](https://github.com/user-attachments/assets/c5ea42ff-3268-431f-a77c-53a6d221edd8)

![Screenshot 2025-03-25 012314](https://github.com/user-attachments/assets/d54632c6-3da6-4a4c-8760-30454a2a1fd8)

![Screenshot 2025-03-25 012339](https://github.com/user-attachments/assets/7b293ede-d9e4-4459-8b08-d76d4ce57379)

![Screenshot 2025-03-25 012544](https://github.com/user-attachments/assets/88a9efdd-b0f5-406f-9c62-c79b90b2e2f3)

![Screenshot 2025-03-25 012602](https://github.com/user-attachments/assets/fb3d6fb9-19f2-475f-9be6-b1e06c7773f9)

![Screenshot 2025-03-25 012643](https://github.com/user-attachments/assets/1c12ca93-4032-4db5-9909-95b41e7b7b87)

![Screenshot 2025-03-25 012733](https://github.com/user-attachments/assets/198255f6-0522-45fe-b1a7-cdd20d23f8e2)

Example searches:
```
"Find sci-fi movies from the 1980s with high ratings"
"Show me action movies starring Tom Cruise"
"What are the best comedies from the 2000s?"
```

4. Follow-up Questions
The system maintains context within each session:
```
Initial query: "Show me Christopher Nolan movies"
Follow-up: "Which one has the highest rating?"
```
### Project Structure
```
imdb-movie-bot/
├── data/                       # Dataset and processing scripts
├── src/
│   ├── config.py               # Configuration management
│   ├── exception.py            # Authentication services
│   ├── logger.py               # Pydantic models
│   ├── utils.py                # Helper functions
├── main.py                     # fastapi routes
├── frontend/                   # Streamlit application
├── Dockerfile                  # Docker-related files
├── data_dump.py                # Dump data to qdrant
├── docker-compose.yml       # Service orchestration
├── requirements.txt         # Python dependencies
└── README.md               # Documentation
```

## API Reference
The FastAPI backend provides these key endpoints:


Endpoint      	            Method	            Description
/register	               POST	            User registration
/generate_access_token	   POST	            JWT token generation
/start_session	            POST	            Initialize new chat session
/query	                  POST	            Submit movie search query

## Development Commands
```
# Run tests
docker-compose run app pytest

# View logs
docker-compose logs -f

# Rebuild containers
docker-compose up --build

# Teardown environment
docker-compose down -v
```

## Roadmap
- Enhanced user profiles

- Personalized recommendations

- Advanced filtering options

- Rate limiting

- Async query processing


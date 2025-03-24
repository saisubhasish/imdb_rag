# IMDB RAG POC
![Screenshot 2025-03-23 214813](https://github.com/user-attachments/assets/62ed1b28-d692-4b3e-aed3-aa001b2110cf)

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
├── docker/                  # Docker-related files
├── data/                    # Dataset and processing scripts
├── src/
│   ├── config/              # Configuration management
│   ├── auth/                # Authentication services
│   ├── models/              # Pydantic models
│   ├── services/            # Core business logic
│   ├── utils/               # Helper functions
│   └── main.py              # FastAPI entrypoint
├── tests/                   # Test cases
├── frontend/                # Streamlit application
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


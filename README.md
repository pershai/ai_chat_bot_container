# AI Chat Bot Container

A production-ready, Dockerized AI chatbot featuring LangGraph, LLM Guard, Qdrant, and Postgres.

## Features
- **Agentic Workflow**: Uses LangGraph for robust decision making.
- **Security**: Integrated LLM Guard for input/output scanning + database-backed authentication.
- **RAG**: Hybrid search (Vector + Keyword) with Qdrant, BM25, and Reciprocal Rank Fusion (RRF).
- **Chat History**: Persistent conversation history stored in PostgreSQL.
- **Logging & Monitoring**: Loki, Promtail, and Grafana stack.
- **Web UI**: Streamlit frontend with authentication.
- **CI/CD**: GitHub Actions for automated testing and linting.
- **Containerized**: Fully dockerized setup.

## Quick Start

1.  Clone the repo.
2.  Create `.env` from `.env.example` and add your API keys.
3.  Run `docker-compose up --build`.
4.  Access the UI at `http://localhost:8501`.

## Project Structure

```
src/
├── core/              # Core infrastructure
│   ├── config.py      # Configuration management
│   ├── database.py    # Database connection
│   ├── security.py    # JWT authentication
│   └── cache.py       # Redis caching
├── models/            # SQLAlchemy models
│   ├── user.py        # User model
│   ├── document.py    # Document model
│   └── conversation.py # Conversation & Message models
├── schemas/           # Pydantic schemas
│   ├── user.py        # User schemas
│   ├── chat.py        # Chat schemas
│   ├── token.py       # JWT token schemas
│   └── conversation.py # Conversation schemas
├── services/          # Business logic
│   ├── auth_service.py         # Authentication logic
│   ├── chat_service.py         # Chat processing
│   ├── ingestion_service.py    # Document ingestion
│   ├── conversation_service.py # Conversation management
│   ├── hybrid_search.py        # Hybrid search (Vector + BM25)
│   └── document_processor.py   # Multi-format document processing
├── routers/           # API routes
│   ├── auth.py        # /auth/* endpoints
│   ├── chat.py        # /chat endpoint
│   ├── upload.py      # /upload endpoint
│   └── conversations.py # /conversations/* endpoints
├── agent.py           # LangGraph agent
├── tools.py           # Agent tools
├── frontend.py        # Streamlit UI
└── main.py            # FastAPI app

tests/
└── integration/       # Integration tests
    ├── test_auth_internal.py
    ├── test_chat_internal.py
    └── test_ingestion_full.py

scripts/
├── init/              # Initialization scripts
│   ├── init_qdrant.py
│   ├── check_embedding_dim.py
│   └── add_db_indexes.py
├── batch_upload.py    # Batch PDF upload
└── qa_benchmark.py    # QA evaluation
```

## API Endpoints

- `GET /` - Health check
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login (returns JWT token)
- `POST /chat` - Chat with the bot (requires authentication)
- `POST /upload` - Upload documents (PDF, DOCX, TXT, etc.)
- `GET /conversations` - List user's conversations
- `GET /conversations/{id}` - Get conversation with messages
- `POST /conversations` - Create new conversation
- `DELETE /conversations/{id}` - Delete conversation

## Development

```bash
# Run integration tests
docker-compose exec app pytest tests/integration/

# Run specific test
docker-compose exec app python -m tests.integration.test_auth_internal

# Run linting
ruff check .

# Format code
ruff format .

# Initialize Qdrant collection
docker-compose exec app python -m scripts.init.init_qdrant

# Add database indexes
docker-compose exec app python scripts/add_db_indexes.py

# Run QA benchmark
docker-compose exec app python scripts/qa_benchmark.py
```

## Performance Optimizations

- **Hybrid Search**: Combines semantic search with keyword matching for better accuracy.
- **Redis Caching**: Chat responses cached with 1-hour TTL.
- **Connection Pooling**: PostgreSQL connection pool (10 connections, 20 overflow).
- **Database Indexes**: Optimized queries on user_id, username, upload_date.
- **Multi-stage Docker Build**: Smaller image size (~30-40% reduction).

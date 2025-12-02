# AI Chatbot Testing Suite

This directory contains integration tests for the AI chatbot application.

## Running Tests

### Integration Tests
```bash
# Run all integration tests
docker-compose exec app pytest tests/integration/

# Run specific test
docker-compose exec app python -m tests.integration.test_auth_internal
docker-compose exec app python -m tests.integration.test_chat_internal
docker-compose exec app python -m tests.integration.test_ingestion_full
```

## Test Files

- `test_auth_internal.py` - Tests user authentication and registration
- `test_chat_internal.py` - Tests chat functionality with Gemini
- `test_ingestion_full.py` - Tests PDF document ingestion
- `test_ingestion_internal.py` - Tests vector store connectivity

## Notes

- Tests require the app container to be running
- Database and Qdrant must be initialized before running tests
- Use `scripts/init/init_qdrant.py` to initialize the vector store

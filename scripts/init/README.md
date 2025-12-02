# Initialization Scripts

This directory contains scripts for initializing and checking the application infrastructure.

## Scripts

### `init_qdrant.py`
Initializes or recreates the Qdrant vector store collection with the correct dimensions.

```bash
docker-compose exec app python -m scripts.init.init_qdrant
```

### `check_embedding_dim.py`
Checks the embedding model and its dimension to ensure Qdrant collection is configured correctly.

```bash
docker-compose exec app python -m scripts.init.check_embedding_dim
```

### `add_db_indexes.py`
Adds performance indexes to the PostgreSQL database.

```bash
docker-compose exec app python scripts/add_db_indexes.py
```

## Usage

Run these scripts after the first deployment or when changing embedding models:

1. Check embedding dimensions
2. Initialize Qdrant collection
3. Add database indexes

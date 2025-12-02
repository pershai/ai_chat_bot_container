import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for the application"""

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
    QDRANT_URL = os.getenv("QDRANT_URL")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL")

    # If not set, construct from components
    if not DATABASE_URL:
        DB_SCHEME = os.getenv("DB_SCHEME", "postgresql")
        DATABASE_URL = f"{DB_SCHEME}://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
    APP_HOST = os.getenv("APP_HOST")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


config = Config()

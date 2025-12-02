from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.core.config import config

DATABASE_URL = config.DATABASE_URL

"""Create engine with connection pooling"""
engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # Number of connections to keep open
    max_overflow=20,  # Max connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Initialize the database"""
    # Import models to register them with Base.metadata
    # noqa: F401 is used to suppress "unused import" warnings
    from src.models.user import User  # noqa: F401
    from src.models.document import Document  # noqa: F401
    from src.models.conversation import Conversation, Message  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    """Get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

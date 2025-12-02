"""
Database migration script to add indexes for performance optimization.
Run this after the initial database setup.
"""

from sqlalchemy import create_engine, text
from src.core.config import config

DATABASE_URL = f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}/{config.POSTGRES_DB}"


def add_indexes():
    """Add performance indexes to database tables."""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        print("Adding database indexes...")

        # Index on users.username for faster login lookups
        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);"
                )
            )
            print("✓ Added index on users.username")
        except Exception as e:
            print(f"  Index on users.username may already exist: {e}")

        # Index on documents.user_id for faster user document queries
        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);"
                )
            )
            print("✓ Added index on documents.user_id")
        except Exception as e:
            print(f"  Index on documents.user_id may already exist: {e}")

        # Index on documents.upload_date for sorting
        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date);"
                )
            )
            print("✓ Added index on documents.upload_date")
        except Exception as e:
            print(f"  Index on documents.upload_date may already exist: {e}")

        # Composite index for user_id + upload_date
        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_documents_user_date ON documents(user_id, upload_date DESC);"
                )
            )
            print("✓ Added composite index on documents(user_id, upload_date)")
        except Exception as e:
            print(f"  Composite index may already exist: {e}")

        conn.commit()
        print("\n✅ Database indexes added successfully!")


if __name__ == "__main__":
    add_indexes()

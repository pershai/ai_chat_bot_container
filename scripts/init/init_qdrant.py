from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.core.config import config


def recreate_qdrant():
    client = QdrantClient(url=config.QDRANT_URL)

    collection_name = config.QDRANT_COLLECTION_NAME

    # Delete if exists
    collections = client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)

    if exists:
        print(f"Deleting existing collection: {collection_name}")
        client.delete_collection(collection_name)

    print(f"Creating collection: {collection_name} with dimension 1024")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=1024,  # Size for BAAI/bge-large-en-v1.5
            distance=models.Distance.COSINE,
        ),
    )
    print("✅ Collection created!")


if __name__ == "__main__":
    recreate_qdrant()

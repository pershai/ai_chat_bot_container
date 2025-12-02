from qdrant_client import QdrantClient

from src.core.config import config


def check_qdrant_contents():
    client = QdrantClient(url=config.QDRANT_URL)

    collection_name = config.QDRANT_COLLECTION_NAME

    # Get collection info
    collection_info = client.get_collection(collection_name)
    print(f"Collection: {collection_name}")
    print(f"Vectors count: {collection_info.vectors_count}")
    print(f"Points count: {collection_info.points_count}")

    # Scroll through points to see what's stored
    points, _ = client.scroll(
        collection_name=collection_name, limit=10, with_payload=True, with_vectors=False
    )

    print(f"\nFound {len(points)} points:")
    for i, point in enumerate(points):
        print(f"\nPoint {i + 1}:")
        print(f"  ID: {point.id}")
        print(f"  Payload: {point.payload}")


if __name__ == "__main__":
    check_qdrant_contents()

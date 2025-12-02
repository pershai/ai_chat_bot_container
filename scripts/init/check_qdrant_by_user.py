from qdrant_client import QdrantClient
from src.core.config import config


def check_qdrant_by_user():
    client = QdrantClient(url=config.QDRANT_URL)

    collection_name = config.QDRANT_COLLECTION_NAME

    # Get collection info
    collection_info = client.get_collection(collection_name)
    print(f"Collection: {collection_name}")
    print(f"Total points: {collection_info.points_count}")

    # Check for user_id 1
    points_user1, _ = client.scroll(
        collection_name=collection_name,
        scroll_filter={"must": [{"key": "metadata.user_id", "match": {"value": 1}}]},
        limit=100,
        with_payload=True,
        with_vectors=False,
    )

    print(f"\nPoints for user_id=1: {len(points_user1)}")
    for point in points_user1:
        print(f"  Content: {point.payload.get('page_content', '')[:100]}...")
        print(f"  Metadata: {point.payload.get('metadata', {})}")

    # Check for user_id 2
    points_user2, _ = client.scroll(
        collection_name=collection_name,
        scroll_filter={"must": [{"key": "metadata.user_id", "match": {"value": 2}}]},
        limit=100,
        with_payload=True,
        with_vectors=False,
    )

    print(f"\nPoints for user_id=2: {len(points_user2)}")


if __name__ == "__main__":
    check_qdrant_by_user()

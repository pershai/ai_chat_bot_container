from langchain_community.vectorstores import Qdrant
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient, models

from src.core.config import config

# Test different filter formats
embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)
qdrant_client = QdrantClient(url=config.QDRANT_URL)

vector_store = Qdrant(
    client=qdrant_client,
    collection_name=config.QDRANT_COLLECTION_NAME,
    embeddings=embeddings,
)

query = "Hello Gemini"
user_id = 1

print("Testing filter formats...")

# Test 1: Simple dict
try:
    print("\n1. Testing {'metadata.user_id': 1}")
    docs = vector_store.similarity_search(
        query, k=3, filter={"metadata.user_id": user_id}
    )
    print(f"   Found {len(docs)} documents")
    if docs:
        print(f"   First doc: {docs[0].page_content[:50]}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Qdrant models.Filter
try:
    print("\n2. Testing models.Filter with FieldCondition")
    filter_obj = models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.user_id", match=models.MatchValue(value=user_id)
            )
        ]
    )
    docs = vector_store.similarity_search(query, k=3, filter=filter_obj)
    print(f"   Found {len(docs)} documents")
    if docs:
        print(f"   First doc: {docs[0].page_content[:50]}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: No filter
try:
    print("\n3. Testing no filter")
    docs = vector_store.similarity_search(query, k=3)
    print(f"   Found {len(docs)} documents")
    if docs:
        for i, doc in enumerate(docs):
            print(
                f"   Doc {i + 1}: {doc.page_content[:30]}... (user_id: {doc.metadata.get('user_id', 'N/A')})"
            )
except Exception as e:
    print(f"   Error: {e}")

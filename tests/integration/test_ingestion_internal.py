from src.services.ingestion_service import get_vector_store
print("Checking Vector Store connection...")
try:
    vs = get_vector_store()
    print("✅ Vector Store connected successfully!")
except Exception as e:
    print(f"❌ Vector Store connection failed: {e}")

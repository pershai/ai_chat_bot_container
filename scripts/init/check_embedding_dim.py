from langchain_huggingface import HuggingFaceEmbeddings
from src.core.config import config

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)

# Get dimension by embedding a test string
test_embedding = embeddings.embed_query("test")
dimension = len(test_embedding)

print(f"Model: {config.EMBEDDING_MODEL_NAME}")
print(f"Embedding dimension: {dimension}")

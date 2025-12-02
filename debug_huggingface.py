import sys
import time
print("Starting langchain_huggingface import test...")
start = time.time()
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    print(f"Import langchain_huggingface took {time.time() - start:.2f}s")
except Exception as e:
    print(f"Error importing langchain_huggingface: {e}")

print("Test complete")

import time

print("Starting import test...")
start = time.time()
try:
    print(f"Import src.tools took {time.time() - start:.2f}s")
except Exception as e:
    print(f"Error importing src.tools: {e}")

print("Test complete")

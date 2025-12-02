import sys
import time
print("Starting llm_guard import test...")
start = time.time()
try:
    from llm_guard.input_scanners import PromptInjection
    print(f"Import llm_guard.input_scanners took {time.time() - start:.2f}s")
except Exception as e:
    print(f"Error importing llm_guard: {e}")

print("Test complete")

# QA Benchmark

This script evaluates the quality of chatbot responses using **Ragas** (Retrieval Augmented Generation Assessment).

## Metrics Evaluated

1. **Answer Relevancy**: How relevant is the answer to the question?
2. **Faithfulness**: Is the answer faithful to the retrieved context?
3. **Context Recall**: How much of the ground truth is captured in the retrieved context?
4. **Context Precision**: How precise is the retrieved context?

## Usage

### 1. Prepare Your Evaluation Dataset

Edit `scripts/qa_benchmark.py` and update the `EVAL_DATA` list with your questions and ground truth answers:

```python
EVAL_DATA = [
    {
        "question": "What is the main purpose of this document?",
        "ground_truth": "Expected answer here...",
    },
    # Add more test cases
]
```

### 2. Upload Documents

Make sure you have uploaded some PDF documents to your knowledge base first (via the UI or batch upload script).

### 3. Run the Benchmark

```bash
# From the project root
python scripts/qa_benchmark.py
```

### 4. View Results

Results will be displayed in the terminal and saved to `qa_benchmark_results.csv`.

## Example Output

```
📊 EVALUATION RESULTS
============================================================
answer_relevancy    : 0.92
faithfulness        : 0.88
context_recall      : 0.85
context_precision   : 0.90
============================================================
```

## Notes

- The script uses Google's API for evaluation (requires `GOOGLE_API_KEY`)
- Adjust `user_id` in the script if testing with specific users
- Add more test cases to `EVAL_DATA` for comprehensive evaluation

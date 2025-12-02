"""
QA Benchmark Script for AI Chatbot

This script evaluates the quality of chatbot responses using Ragas metrics.
"""

import asyncio
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    faithfulness,
    context_recall,
    context_precision,
)
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from src.core.config import config
from src.services.chat_service import process_chat
from src.tools import get_vector_store

# Sample evaluation dataset
# Format: question, ground_truth (expected answer), contexts (retrieved docs)
EVAL_DATA = [
    {
        "question": "What is the main purpose of this document?",
        "ground_truth": "This is a sample ground truth answer that should match the chatbot's response.",
    },
    {
        "question": "What are the key features mentioned?",
        "ground_truth": "The key features include X, Y, and Z as described in the document.",
    },
]


async def generate_answers_and_contexts(questions: list[str], user_id: int = 1):
    """Generate chatbot answers and retrieve contexts for evaluation."""
    results = []
    vector_store = get_vector_store()

    for question in questions:
        # Get chatbot answer
        answer = await process_chat(question, user_id)

        # Get retrieved contexts
        docs = vector_store.similarity_search(
            question, k=config.RAG_TOP_K, filter={"user_id": user_id}
        )
        contexts = [doc.page_content for doc in docs]

        results.append(
            {
                "question": question,
                "answer": answer,
                "contexts": contexts,
            }
        )

    return results


async def run_evaluation():
    """Run the QA evaluation using Ragas."""
    print("🔍 Starting QA Benchmark Evaluation...\n")

    # Prepare questions and ground truths
    questions = [item["question"] for item in EVAL_DATA]
    ground_truths = [[item["ground_truth"]] for item in EVAL_DATA]

    # Generate answers and contexts
    print("📝 Generating answers and retrieving contexts...")
    results = await generate_answers_and_contexts(questions)

    # Prepare dataset for Ragas
    data = {
        "question": [r["question"] for r in results],
        "answer": [r["answer"] for r in results],
        "contexts": [r["contexts"] for r in results],
        "ground_truth": ground_truths,
    }

    dataset = Dataset.from_dict(data)

    # Initialize LLM and embeddings for evaluation
    llm = ChatGoogleGenerativeAI(
        google_api_key=config.GOOGLE_API_KEY, model=config.LLM_MODEL_NAME
    )
    embeddings = GoogleGenerativeAIEmbeddings(
        google_api_key=config.GOOGLE_API_KEY, model="models/embedding-001"
    )

    # Run evaluation
    print("⚡ Running Ragas evaluation...\n")
    result = evaluate(
        dataset,
        metrics=[
            answer_relevancy,
            faithfulness,
            context_recall,
            context_precision,
        ],
        llm=llm,
        embeddings=embeddings,
    )

    # Display results
    print("=" * 60)
    print("📊 EVALUATION RESULTS")
    print("=" * 60)
    print(f"\n{result}\n")
    print("=" * 60)

    # Save results to file
    result_df = result.to_pandas()
    result_df.to_csv("qa_benchmark_results.csv", index=False)
    print("\n✅ Results saved to qa_benchmark_results.csv")

    return result


if __name__ == "__main__":
    asyncio.run(run_evaluation())

import logging
from langchain_core.tools import tool
from langchain_community.utilities import SerpAPIWrapper
from langchain_qdrant import Qdrant
from langchain_huggingface import HuggingFaceEmbeddings

from qdrant_client import QdrantClient, models
from llm_guard import scan_prompt, scan_output
from llm_guard.input_scanners import PromptInjection, TokenLimit, Toxicity
from llm_guard.output_scanners import NoRefusal
from llm_guard.vault import Vault
from src.core.config import config
from src.services.hybrid_search import get_hybrid_search_service

# Initialize Embeddings
embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)

# Initialize Qdrant Client
qdrant_client = QdrantClient(url=config.QDRANT_URL)

# Initialize Vector Store (ensure collection exists in a real app, here we assume it might be created or we handle it)
# For simplicity, we'll define a function to get the vector store
def get_vector_store():
    """
    Get a configured Qdrant vector store instance.
    
    Returns:
        Qdrant: A Qdrant vector store configured with the client, collection name, and embeddings.
    """
    return Qdrant(
        client=qdrant_client,
        collection_name=config.QDRANT_COLLECTION_NAME,
        embeddings=embeddings,
    )

# Initialize Search
search = SerpAPIWrapper(serpapi_api_key=config.SERPAPI_API_KEY)

# LLM Guard Scanners - Tuned for reduced false positives
vault = Vault()

# Input scanners with adjusted thresholds
input_scanners = [
    # Anonymize disabled - was causing false positives on common words like "Gemini"
    # Anonymize(vault=vault),
    
    # PromptInjection with higher threshold (0.92 instead of default 0.5)
    # This reduces false positives while still catching actual injection attempts
    PromptInjection(threshold=0.92),
    
    # TokenLimit - keep as is, prevents excessive input
    TokenLimit(limit=4096, encoding_name="cl100k_base"),
    
    # Toxicity - keep as is, prevents abusive content
    Toxicity(threshold=0.7)
]

# Output scanners - simplified to reduce over-filtering
output_scanners = [
    # Deanonymize disabled since we disabled Anonymize
    # Deanonymize(vault=vault),
    
    # NoRefusal - prevents the model from refusing to answer
    NoRefusal(threshold=0.75),
    
    # Relevance and Sensitive disabled to reduce false positives
    # Relevance(),
    # Sensitive()
]

@tool
def verify_input(query: str) -> str:
    """Verifies the user input using LLM Guard. Returns 'SAFE' if safe, otherwise the error message."""
    sanitized_prompt, results_valid, results_score = scan_prompt(input_scanners, query)
    if any(not result for result in results_valid.values()):
        return f"Input verification failed: {results_score}"
    return "SAFE"

@tool
def search_rag(query: str, state: dict = None, use_hybrid: bool = True) -> str:
    """
    Searches the RAG (VectorDB) for relevant information filtered by user_id.
    
    Uses hybrid search (vector + BM25) by default for better retrieval accuracy.
    Falls back to vector-only search if hybrid search fails.
    
    Args:
        query: Search query
        state: State dict containing user_id
        use_hybrid: Whether to use hybrid search (default: True)
        
    Returns:
        Relevant information from knowledge base
    """
    try:
        # Get user_id from state if available
        user_id = state.get("user_id") if state else None
        
        if not user_id:
            return "Error: User ID not found in state"
        
        # Try hybrid search first
        if use_hybrid:
            try:
                
                
                hybrid_search = get_hybrid_search_service()
                results = hybrid_search.search(
                    query=query,
                    user_id=user_id,
                    k=config.RAG_TOP_K
                )
                
                if results:
                    # Format results with metadata
                    formatted_results = []
                    for result in results:
                        content = result.document.page_content
                        metadata = result.document.metadata
                        source = metadata.get("filename", "Unknown")
                        formatted_results.append(f"[Source: {source}]\n{content}")
                    
                    return "\n\n".join(formatted_results)
                
            except Exception as e:
                # Log hybrid search failure and fall back to vector search

                logger = logging.getLogger(__name__)
                logger.warning("Hybrid search failed, falling back to vector search: %s", e)
        
        # Fallback to vector-only search
        vector_store = get_vector_store()
        
        # Build filter for user-specific documents
        search_kwargs = {"k": config.RAG_TOP_K}
        if user_id:
            search_kwargs["filter"] = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            )
        
        docs = vector_store.similarity_search(query, **search_kwargs)
        if not docs:
            return "No relevant information found in the knowledge base."
        
        # Format results
        formatted_results = []
        for doc in docs:
            source = doc.metadata.get("filename", "Unknown")
            formatted_results.append(f"[Source: {source}]\n{doc.page_content}")
        
        return "\n\n".join(formatted_results)
        
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"

@tool
def search_internet(query: str) -> str:
    """Searches the internet for information."""
    try:
        return search.run(query)
    except Exception as e:
        return f"Error searching internet: {str(e)}"

@tool
def verify_output(prompt: str, response: str) -> str:
    """Verifies the LLM output using LLM Guard. Returns 'SAFE' if safe, otherwise the error message."""
    sanitized_response, results_valid, results_score = scan_output(output_scanners, prompt, response)
    if any(not result for result in results_valid.values()):
        return f"Output verification failed: {results_score}"
    return "SAFE"

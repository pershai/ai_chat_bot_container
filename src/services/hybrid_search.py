"""
Hybrid search service combining vector similarity and keyword search.

Uses vector embeddings (semantic) + BM25 (keyword) with Reciprocal Rank Fusion.
"""

import logging
from typing import List, Dict, Optional, TYPE_CHECKING
from dataclasses import dataclass

from langchain_core.documents import Document
from src.core.config import config

if TYPE_CHECKING:
    from qdrant_client import QdrantClient
    from langchain_huggingface import HuggingFaceEmbeddings
    from src.services.hybrid_search import SearchResult

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with score and metadata"""

    document: Document
    score: float
    rank: int
    source: str  # "vector" or "bm25" or "hybrid"


class BM25Search:
    """
    BM25 keyword search implementation.

    BM25 is a ranking function used for keyword-based search.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 search.

        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.corpus: List[Document] = []
        self.corpus_tokens: List[List[str]] = []
        self.avgdl: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_len: List[int] = []

    def tokenize(self, text: str) -> List[str]:
        """Simple tokenization by splitting on whitespace and lowercasing"""
        return text.lower().split()

    def build_index(self, documents: List[Document]):
        """
        Build BM25 index from documents.

        Args:
            documents: List of documents to index
        """
        self.corpus = documents
        self.corpus_tokens = [self.tokenize(doc.page_content) for doc in documents]
        self.doc_len = [len(tokens) for tokens in self.corpus_tokens]
        self.avgdl = sum(self.doc_len) / len(self.doc_len) if self.doc_len else 0

        # Calculate document frequencies
        self.doc_freqs = {}
        for tokens in self.corpus_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        # Calculate IDF scores
        num_docs = len(self.corpus)
        self.idf = {}
        for token, freq in self.doc_freqs.items():
            self.idf[token] = self._calc_idf(freq, num_docs)

    def _calc_idf(self, doc_freq: int, num_docs: int) -> float:
        """Calculate IDF score for a term"""
        import math

        return math.log((num_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)

    def get_scores(self, query: str) -> List[float]:
        """
        Calculate BM25 scores for query against all documents.

        Args:
            query: Search query

        Returns:
            List of BM25 scores for each document
        """
        query_tokens = self.tokenize(query)
        scores = []

        for i, doc_tokens in enumerate(self.corpus_tokens):
            score = 0.0
            doc_len = self.doc_len[i]

            # Count term frequencies in document
            term_freqs = {}
            for token in doc_tokens:
                term_freqs[token] = term_freqs.get(token, 0) + 1

            # Calculate BM25 score
            for token in query_tokens:
                if token not in self.idf:
                    continue

                idf = self.idf[token]
                tf = term_freqs.get(token, 0)

                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * (doc_len / self.avgdl)
                )
                score += idf * (numerator / denominator)

            scores.append(score)

        return scores

    def search(self, query: str, k: int = 5) -> List[SearchResult]:
        """
        Search for top-k documents using BM25.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of search results
        """
        if not self.corpus:
            return []

        scores = self.get_scores(query)

        # Get top-k indices
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        top_k = indexed_scores[:k]

        results = []
        for rank, (idx, score) in enumerate(top_k, start=1):
            results.append(
                SearchResult(
                    document=self.corpus[idx], score=score, rank=rank, source="bm25"
                )
            )

        return results


class HybridSearchService:
    """
    Hybrid search combining vector similarity and BM25 keyword search.

    Uses Reciprocal Rank Fusion (RRF) to combine results.
    """

    def __init__(
        self,
        qdrant_client: Optional["QdrantClient"] = None,
        embeddings: Optional["HuggingFaceEmbeddings"] = None,
        collection_name: str = "documents",
        rrf_k: int = 60,
    ):
        """
        Initialize hybrid search service.

        Args:
            qdrant_client: Qdrant client instance
            embeddings: Embedding model
            collection_name: Qdrant collection name
            rrf_k: RRF constant (default: 60)
        """
        if qdrant_client:
            self.qdrant_client = qdrant_client
        else:
            from qdrant_client import QdrantClient
            self.qdrant_client = QdrantClient(
                url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY
            )
            
        if embeddings:
            self.embeddings = embeddings
        else:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name=config.EMBEDDING_MODEL_NAME
            )
            
        self.collection_name = collection_name
        self.rrf_k = rrf_k
        self.bm25 = BM25Search()

    def vector_search(
        self, query: str, user_id: int, k: int = 10, score_threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        Perform vector similarity search.

        Args:
            query: Search query
            user_id: User ID for filtering
            k: Number of results
            score_threshold: Minimum similarity score

        Returns:
            List of search results
        """
        from qdrant_client import models
        
        # Generate query embedding
        query_vector = self.embeddings.embed_query(query)

        # Search in Qdrant
        search_result = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.user_id", match=models.MatchValue(value=user_id)
                    )
                ]
            ),
            limit=k,
            score_threshold=score_threshold,
        )

        # Convert to SearchResult objects
        results = []
        for rank, hit in enumerate(search_result, start=1):
            doc = Document(
                page_content=hit.payload.get("page_content", ""),
                metadata=hit.payload.get("metadata", {}),
            )
            results.append(
                SearchResult(document=doc, score=hit.score, rank=rank, source="vector")
            )

        return results

    def bm25_search(self, query: str, user_id: int, k: int = 10) -> List[SearchResult]:
        """
        Perform BM25 keyword search.

        Args:
            query: Search query
            user_id: User ID for filtering
            k: Number of results

        Returns:
            List of search results
        """
        from qdrant_client import models
        
        # Fetch all user documents from Qdrant
        # Note: In production, you'd want to cache this or use a separate BM25 index
        scroll_result = self.qdrant_client.scroll(
            collection_name=self.collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.user_id", match=models.MatchValue(value=user_id)
                    )
                ]
            ),
            limit=1000,  # Adjust based on expected document count
        )

        # Convert to Document objects
        documents = []
        for point in scroll_result[0]:
            doc = Document(
                page_content=point.payload.get("page_content", ""),
                metadata=point.payload.get("metadata", {}),
            )
            documents.append(doc)

        if not documents:
            logger.warning(f"No documents found for user {user_id}")
            return []

        # Build BM25 index
        self.bm25.build_index(documents)

        # Search
        results = self.bm25.search(query, k=k)

        return results

    def reciprocal_rank_fusion(
        self,
        vector_results: List[SearchResult],
        bm25_results: List[SearchResult],
        k: int = 5,
    ) -> List[SearchResult]:
        """
        Combine results using Reciprocal Rank Fusion.

        RRF formula: score = sum(1 / (k + rank_i)) for each result list

        Args:
            vector_results: Results from vector search
            bm25_results: Results from BM25 search
            k: RRF constant (default: 60)

        Returns:
            Fused and ranked results
        """
        # Create a dictionary to accumulate RRF scores
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, SearchResult] = {}

        # Process vector results
        for result in vector_results:
            doc_id = result.document.page_content[:100]  # Use content prefix as ID
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (
                1.0 / (self.rrf_k + result.rank)
            )
            doc_map[doc_id] = result

        # Process BM25 results
        for result in bm25_results:
            doc_id = result.document.page_content[:100]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (
                1.0 / (self.rrf_k + result.rank)
            )
            if doc_id not in doc_map:
                doc_map[doc_id] = result

        # Sort by RRF score
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # Create final results
        final_results = []
        for rank, (doc_id, score) in enumerate(sorted_docs[:k], start=1):
            result = doc_map[doc_id]
            final_results.append(
                SearchResult(
                    document=result.document, score=score, rank=rank, source="hybrid"
                )
            )

        return final_results

    def search(
        self,
        query: str,
        user_id: int,
        k: int = 5,
        use_hybrid: bool = True,
        vector_weight: float = 0.5,
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining vector and keyword search.

        Args:
            query: Search query
            user_id: User ID for filtering
            k: Number of results to return
            use_hybrid: If False, use vector search only
            vector_weight: Weight for vector search (0-1), BM25 gets (1-weight)

        Returns:
            List of search results
        """
        logger.info(f"Hybrid search for user {user_id}: '{query}' (k={k})")

        if not use_hybrid:
            # Vector search only
            return self.vector_search(query, user_id, k=k)

        # Perform both searches with higher k for better fusion
        search_k = k * 2

        vector_results = self.vector_search(query, user_id, k=search_k)
        logger.info(f"Vector search returned {len(vector_results)} results")

        bm25_results = self.bm25_search(query, user_id, k=search_k)
        logger.info(f"BM25 search returned {len(bm25_results)} results")

        # Fuse results
        hybrid_results = self.reciprocal_rank_fusion(vector_results, bm25_results, k=k)

        logger.info(f"Hybrid search returned {len(hybrid_results)} fused results")

        return hybrid_results


# Singleton instance
_hybrid_search_instance: Optional[HybridSearchService] = None


def get_hybrid_search_service() -> HybridSearchService:
    """Get singleton hybrid search service instance"""
    global _hybrid_search_instance
    if _hybrid_search_instance is None:
        _hybrid_search_instance = HybridSearchService()
    return _hybrid_search_instance

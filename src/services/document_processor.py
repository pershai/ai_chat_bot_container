"""
PDF document processor for RAG system.

Supports: PDF only
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Process PDF documents"""

    def extract_text(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from PDF with page numbers"""
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        chunks = []
        for doc in documents:
            chunks.append(
                {
                    "text": doc.page_content,
                    "metadata": {
                        "page_number": doc.metadata.get("page", 0),
                        "source": doc.metadata.get("source", file_path),
                    },
                }
            )

        return chunks

    def get_file_type(self) -> str:
        return "pdf"


class DocumentProcessor:
    """
    PDF document processor for RAG system.

    Supports: PDF only
    """

    SUPPORTED_FORMATS = {
        "pdf": PDFProcessor,
    }

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        add_start_index: bool = True,
    ):
        """
        Initialize document processor.

        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            add_start_index: Whether to add start index to metadata
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.add_start_index = add_start_index

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=add_start_index,
        )

    def get_file_extension(self, file_path: str) -> str:
        """Extract file extension from path"""
        return file_path.split(".")[-1].lower()

    def is_supported(self, file_path: str) -> bool:
        """Check if file format is supported"""
        ext = self.get_file_extension(file_path)
        return ext in self.SUPPORTED_FORMATS

    def process_document(
        self,
        file_path: str,
        user_id: int,
        filename: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Document]:
        """
        Process document with format-specific handler.

        Args:
            file_path: Path to document file
            user_id: User ID for metadata
            filename: Original filename (if different from file_path)
            tags: Optional tags for categorization

        Returns:
            List of LangChain Document objects with rich metadata

        Raises:
            ValueError: If file format is not supported
        """
        ext = self.get_file_extension(file_path)

        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {ext}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS.keys())}"
            )

        logger.info("Processing %s document: %s", ext.upper(), file_path)

        # Get appropriate processor
        processor_class = self.SUPPORTED_FORMATS[ext]
        processor = processor_class()

        # Extract text and metadata
        try:
            raw_chunks = processor.extract_text(file_path)
            logger.info("Extracted %d raw chunks from %s", len(raw_chunks), file_path)
        except Exception as e:
            logger.error("Failed to extract text from %s: %s", file_path, e)
            raise

        # Convert to LangChain documents
        documents = []
        for chunk in raw_chunks:
            doc = Document(
                page_content=chunk["text"], metadata=chunk.get("metadata", {})
            )
            documents.append(doc)

        # Split documents into optimized chunks
        optimized_chunks = self.optimize_chunks(documents)

        # Add rich metadata
        final_chunks = self.enrich_metadata(
            optimized_chunks,
            user_id=user_id,
            filename=filename or os.path.basename(file_path),
            file_type=ext,
            tags=tags or [],
        )

        logger.info("Created %d optimized chunks", len(final_chunks))

        return final_chunks

    def optimize_chunks(self, documents: List[Document]) -> List[Document]:
        """
        Optimize document chunks with intelligent splitting.

        Args:
            documents: Raw documents to optimize

        Returns:
            Optimized document chunks
        """
        # Use text splitter for intelligent chunking
        optimized = self.text_splitter.split_documents(documents)
        return optimized

    def enrich_metadata(
        self,
        documents: List[Document],
        user_id: int,
        filename: str,
        file_type: str,
        tags: List[str],
    ) -> List[Document]:
        """
        Enrich documents with comprehensive metadata.

        Args:
            documents: Documents to enrich
            user_id: User ID
            filename: Original filename
            file_type: File type/extension
            tags: Document tags

        Returns:
            Documents with enriched metadata
        """
        upload_date = datetime.now().isoformat()

        for i, doc in enumerate(documents):
            # Preserve existing metadata
            existing_metadata = doc.metadata.copy()

            # Add rich metadata
            doc.metadata.update(
                {
                    "user_id": user_id,
                    "filename": filename,
                    "file_type": file_type,
                    "upload_date": upload_date,
                    "tags": tags,
                    "chunk_index": i,
                    "total_chunks": len(documents),
                    "word_count": len(doc.page_content.split()),
                    **existing_metadata,  # Keep original metadata
                }
            )

        return documents

    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return list(self.SUPPORTED_FORMATS.keys())


# Singleton instance for easy access
_processor_instance: Optional[DocumentProcessor] = None


def get_document_processor() -> DocumentProcessor:
    """Get singleton document processor instance"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = DocumentProcessor()
    return _processor_instance

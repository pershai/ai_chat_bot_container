"""
Document ingestion service with multi-format support.

Supports: PDF, DOCX, TXT, MD, HTML, CSV, XLSX
"""

import os
import logging
from typing import Optional, List
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from src.tools import get_vector_store
from src.models.document import Document
from src.services.document_processor import get_document_processor

logger = logging.getLogger(__name__)


async def ingest_document(
    file: UploadFile, user_id: int, db: Session, tags: Optional[List[str]] = None
) -> str:
    """
    Ingest a document into the vector store with user_id metadata.

    Supports multiple formats: PDF, DOCX, TXT, MD, HTML, CSV, XLSX

    Args:
        file: Uploaded file
        user_id: User ID for metadata
        db: Database session
        tags: Optional tags for categorization

    Returns:
        Success message with ingestion details

    Raises:
        HTTPException: If file format is unsupported or processing fails
    """
    temp_file_path = f"temp_{file.filename}"

    try:
        # Save uploaded file temporarily
        logger.info("Saving temporary file: %s", temp_file_path)
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Get document processor
        processor = get_document_processor()

        # Check if format is supported
        if not processor.is_supported(temp_file_path):
            supported = ", ".join(processor.get_supported_formats())
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Supported formats: {supported}",
            )

        # Process document with multi-format support
        logger.info("Processing document: %s", file.filename)
        splits = processor.process_document(
            file_path=temp_file_path,
            user_id=user_id,
            filename=file.filename,
            tags=tags or [],
        )

        logger.info("Created %d chunks from %s", len(splits), file.filename)

        # Index to Qdrant
        vector_store = get_vector_store()
        vector_store.add_documents(documents=splits)
        logger.info("Indexed %d chunks to vector store", len(splits))

        # Store document metadata in database
        file_type = processor.get_file_extension(temp_file_path)
        db_document = Document(
            filename=file.filename,
            user_id=user_id,
            file_type=file_type,
            chunk_count=len(splits),
        )
        db.add(db_document)
        db.commit()
        logger.info("Saved document metadata to database")

        return (
            f"Successfully ingested {len(splits)} chunks from {file.filename} "
            f"(format: {file_type.upper()})"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error ingesting file %s: %s", file.filename, e, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error ingesting file: {str(e)}"
        ) from e

    finally:
        # Cleanup temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.debug("Cleaned up temporary file: %s", temp_file_path)


# Backward compatibility - keep old function name
async def ingest_pdf(file: UploadFile, user_id: int, db: Session) -> str:
    """
    Legacy function for PDF ingestion. Use ingest_document instead.

    This function is kept for backward compatibility.
    """
    return await ingest_document(file, user_id, db)

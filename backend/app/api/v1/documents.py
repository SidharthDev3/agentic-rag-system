import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from app.api.deps import get_chunk_repo, get_document_repo, get_ingestion_service
from app.core.config import settings
from app.core.errors import DocumentNotFoundError, UnsupportedFileTypeError
from app.core.security import sanitize_filename, validate_file_extension, validate_file_size
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.document_repo import DocumentRepository
from app.schemas.chunk import ChunkResponse
from app.schemas.document import DocumentDetailResponse, DocumentListResponse, DocumentResponse
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Upload and ingest a document (PDF, DOCX, TXT, MD).
    Extracts text, splits into semantic chunks, generates embeddings, and indexes into vector/keyword stores.
    """
    clean_filename = sanitize_filename(file.filename or "uploaded_file.txt")
    validate_file_extension(clean_filename)

    # Save to temp upload storage
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = settings.UPLOAD_DIR / f"{uuid.uuid4()}_{clean_filename}"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = temp_path.stat().st_size
        validate_file_size(file_size)

        document = await ingestion_service.ingest_file(
            file_path=temp_path,
            original_filename=clean_filename,
            file_size=file_size,
        )
        return document
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    doc_repo: DocumentRepository = Depends(get_document_repo),
):
    """List all uploaded documents with pagination and optional status filter."""
    docs, total = await doc_repo.list_documents(skip=skip, limit=limit, status=status)
    return DocumentListResponse(total=total, documents=docs)


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    doc_repo: DocumentRepository = Depends(get_document_repo),
    chunk_repo: ChunkRepository = Depends(get_chunk_repo),
):
    """Retrieve full details of a document including its indexed chunks."""
    doc = await doc_repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found",
        )

    chunks = await chunk_repo.list_by_document(document_id, limit=200)
    return DocumentDetailResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        content_hash=doc.content_hash,
        status=doc.status,
        error_message=doc.error_message,
        chunk_count=doc.chunk_count,
        doc_metadata=doc.doc_metadata,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        chunks=[ChunkResponse.model_validate(c) for c in chunks],
    )


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    doc_repo: DocumentRepository = Depends(get_document_repo),
):
    """Delete a document and all its associated indexed chunks."""
    deleted = await doc_repo.delete(document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found",
        )
    return {"message": "Document deleted successfully", "id": document_id}


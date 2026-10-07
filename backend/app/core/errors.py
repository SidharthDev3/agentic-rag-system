from typing import Any, Optional
from fastapi import HTTPException, status


class NexusRAGException(Exception):
    """Base exception for NexusRAG domain errors."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class DocumentNotFoundError(NexusRAGException):
    """Raised when a requested document does not exist."""
    pass


class IngestionError(NexusRAGException):
    """Raised when document ingestion or parsing fails."""
    pass


class UnsupportedFileTypeError(NexusRAGException):
    """Raised when an uploaded file type is not supported."""
    pass


class RetrievalError(NexusRAGException):
    """Raised when retrieval operations fail."""
    pass


class LLMServiceError(NexusRAGException):
    """Raised when LLM invocation or streaming fails."""
    pass


def http_exception_from_domain(exc: NexusRAGException) -> HTTPException:
    if isinstance(exc, DocumentNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    elif isinstance(exc, UnsupportedFileTypeError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    elif isinstance(exc, IngestionError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    elif isinstance(exc, LLMServiceError):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message)
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.message)


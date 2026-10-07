import os
import re
from pathlib import Path
from app.core.config import settings
from app.core.errors import UnsupportedFileTypeError

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def sanitize_filename(filename: str) -> str:
    """Strip dangerous characters and directory traversal markers."""
    clean_name = os.path.basename(filename)
    # Remove null bytes and non-alphanumeric/safe chars
    clean_name = re.sub(r"[^\w\s\.-]", "_", clean_name)
    return clean_name.strip()


def validate_file_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    return ext


def validate_file_size(size_bytes: int) -> None:
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise UnsupportedFileTypeError(
            f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )


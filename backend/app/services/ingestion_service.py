import hashlib
from pathlib import Path
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.errors import IngestionError, UnsupportedFileTypeError
from app.core.logging import logger
from app.core.security import sanitize_filename, validate_file_extension
from app.ingestion.chunker import semantic_chunker
from app.ingestion.parsers.docx_parser import DocxParser
from app.ingestion.parsers.markdown_parser import MarkdownParser
from app.ingestion.parsers.pdf_parser import PDFParser
from app.ingestion.parsers.text_parser import TextParser
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.document_repo import DocumentRepository
from app.services.embedding_service import embedding_service


class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)

    def _get_parser(self, ext: str):
        if ext == ".pdf":
            return PDFParser
        elif ext == ".docx":
            return DocxParser
        elif ext == ".txt":
            return TextParser
        elif ext == ".md":
            return MarkdownParser
        raise UnsupportedFileTypeError(f"No parser available for {ext}")

    async def ingest_file(
        self,
        file_path: Path,
        original_filename: str,
        file_size: int,
    ) -> Document:
        filename = sanitize_filename(original_filename)
        ext = validate_file_extension(filename)

        # 1. Compute SHA-256 hash
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        content_hash = hasher.hexdigest()

        # 2. Check for duplicate
        existing_doc = await self.doc_repo.get_by_hash(content_hash)
        if existing_doc and existing_doc.status == "indexed":
            logger.info(f"File '{filename}' already indexed (ID: {existing_doc.id}).")
            return existing_doc

        # 3. Create initial Document record
        doc = Document(
            filename=filename,
            file_type=ext.lstrip("."),
            file_size=file_size,
            content_hash=content_hash,
            status="processing",
            doc_metadata={"original_name": original_filename, "extension": ext},
        )
        doc = await self.doc_repo.create(doc)

        try:
            # 4. Parse document
            parser = self._get_parser(ext)
            sections = parser.parse(file_path)

            if not sections:
                raise IngestionError(f"No extractable text found in '{filename}'")

            # 5. Chunk text
            raw_chunks = semantic_chunker.create_chunks(
                document_id=doc.id,
                filename=filename,
                parsed_sections=sections,
            )

            if not raw_chunks:
                raise IngestionError("Document produced 0 chunks after splitting")

            # 6. Generate Embeddings in batch
            chunk_texts = [c["content"] for c in raw_chunks]
            embeddings = await embedding_service.get_embeddings(chunk_texts)

            # 7. Create DocumentChunk entities
            chunk_entities = []
            for raw_chunk, emb in zip(raw_chunks, embeddings):
                chunk_obj = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=raw_chunk["chunk_index"],
                    content=raw_chunk["content"],
                    token_count=raw_chunk["token_count"],
                    page_number=raw_chunk["page_number"],
                    section=raw_chunk["section"],
                    source=raw_chunk["source"],
                    char_offset_start=raw_chunk["char_offset_start"],
                    char_offset_end=raw_chunk["char_offset_end"],
                    embedding=emb,
                    chunk_metadata=raw_chunk["chunk_metadata"],
                )
                chunk_entities.append(chunk_obj)

            await self.chunk_repo.create_many(chunk_entities)

            # 8. Update Document status to indexed
            await self.doc_repo.update_status(
                document_id=doc.id,
                status="indexed",
                chunk_count=len(chunk_entities),
            )
            logger.info(f"Document '{filename}' successfully indexed with {len(chunk_entities)} chunks.")
            return doc

        except Exception as e:
            logger.error(f"Failed to ingest document '{filename}': {e}", exc_info=True)
            await self.doc_repo.update_status(
                document_id=doc.id,
                status="failed",
                error_message=str(e),
            )
            raise


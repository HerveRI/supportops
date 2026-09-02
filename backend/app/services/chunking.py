from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.services.text_extraction import TextExtractionResult

DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 200


@dataclass(frozen=True)
class TextChunk:
    document_id: UUID
    original_filename: str
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    page_number: int | None


def chunk_extracted_text(
    extraction: TextExtractionResult,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """split extracted text into ordered overlapping chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    text = extraction.text

    if not text:
        return []

    step_size = chunk_size - chunk_overlap
    chunks: list[TextChunk] = []

    chunk_index = 0
    start_char = 0

    while start_char < len(text):
        end_char = min(start_char + chunk_size, len(text))

        chunks.append(
            TextChunk(
                document_id=extraction.document_id,
                original_filename=extraction.original_filename,
                chunk_index=chunk_index,
                text=text[start_char:end_char],
                start_char=start_char,
                end_char=end_char,
                page_number=extraction.page_number,
            )
        )

        if end_char == len(text):
            break

        start_char += step_size
        chunk_index += 1

    return chunks


def store_document_chunks(
    db: Session, document_id: UUID, chunks: list[TextChunk]
) -> list[DocumentChunk]:
    """Replace the stored chunks for one document."""
    db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))

    chunk_rows = [
        DocumentChunk(
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            page_number=chunk.page_number,
        )
        for chunk in chunks
    ]

    db.add_all(chunk_rows)
    db.flush()

    return chunk_rows

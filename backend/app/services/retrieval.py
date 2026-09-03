from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embeddings import embed_texts

DEFAULT_TOP_K = 5


@dataclass(frozen=True)
class SimilaritySearchResult:
    chunk_id: UUID
    document_id: UUID
    original_filename: str
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    page_number: int | None
    cosine_similarity: float


def search_knowledge_base(
    db: Session,
    query: str,
    top_k: int = DEFAULT_TOP_K,
) -> list[SimilaritySearchResult]:
    """Return the document chunks most semantically similar to a query."""
    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty")

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    query_embedding = embed_texts([query])[0]

    cosine_distance = DocumentChunk.embedding.cosine_distance(query_embedding).label(
        "cosine_distance"
    )

    statement = (
        select(
            DocumentChunk,
            Document.original_filename,
            cosine_distance,
        )
        .join(
            Document,
            Document.id == DocumentChunk.document_id,
        )
        .where(DocumentChunk.embedding.is_not(None))
        .order_by(
            cosine_distance.asc(),
            DocumentChunk.document_id,
            DocumentChunk.chunk_index,
        )
        .limit(top_k)
    )

    rows = db.execute(statement).all()

    return [
        SimilaritySearchResult(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            original_filename=original_filename,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            page_number=chunk.page_number,
            cosine_similarity=1.0 - float(distance),
        )
        for chunk, original_filename, distance in rows
    ]

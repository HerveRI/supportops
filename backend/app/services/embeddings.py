from functools import lru_cache
from uuid import UUID

from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_chunk import EMBEDDING_DIMENSIONS, DocumentChunk

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it for this process."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate normalized embeddings for a batch of texts."""
    if not texts:
        return []

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    vectors = embeddings.tolist()

    # Catch a model/schema mismatch before sending invalid vectors to PostgreSQL.
    if any(len(vector) != EMBEDDING_DIMENSIONS for vector in vectors):
        raise RuntimeError(
            f"Embedding model did not return {EMBEDDING_DIMENSIONS}-dimensional vectors"
        )

    return vectors


def embed_document_chunks(
    db: Session,
    document_id: UUID,
) -> int:
    """Generate and store embeddings for all chunks belonging to one document"""
    chunks = db.scalars(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    ).all()

    if not chunks:
        return 0

    vectors = embed_texts([chunk.text for chunk in chunks])

    for chunk, vector in zip(chunks, vectors, strict=True):
        chunk.embedding = vector

    db.flush()

    return len(chunks)

import math
from collections import Counter
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.search_text import tokenize_keyword_text

DEFAULT_TOP_K = 5
DEFAULT_BM25_K1 = 1.5
DEFAULT_BM25_B = 0.75


@dataclass(frozen=True)
class KeywordSearchResult:
    chunk_id: UUID
    document_id: UUID
    original_filename: str
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    page_number: int | None
    bm25_score: float
    source_title: str | None = None

    @property
    def source_name(self) -> str:
        """Return the logical source title, falling back to the uploaded filename."""
        return self.source_title or self.original_filename


def _bm25_idf(total_chunks: int, document_frequency: int) -> float:
    return math.log(
        (total_chunks - document_frequency + 0.5) / (document_frequency + 0.5) + 1
    )


def _bm25_term_score(
    term_frequency: int,
    document_length: int,
    average_document_length: float,
    k1: float,
    b: float,
) -> float:
    if term_frequency <= 0:
        return 0.0

    if average_document_length <= 0:
        return 0.0

    length_normalization = 1 - b + b * (document_length / average_document_length)

    return (term_frequency * (k1 + 1)) / (term_frequency + k1 * length_normalization)


def keyword_search(
    db: Session,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    k1: float = DEFAULT_BM25_K1,
    b: float = DEFAULT_BM25_B,
) -> list[KeywordSearchResult]:
    """Rank stored chunks with BM25 over normalized lexical terms."""
    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty")

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    if k1 <= 0:
        raise ValueError("k1 must be greater than zero")

    if not 0 <= b <= 1:
        raise ValueError("b must be between zero and one")

    query_terms = tokenize_keyword_text(query)

    if not query_terms:
        return []

    statement = (
        select(
            DocumentChunk,
            Document.original_filename,
        )
        .join(
            Document,
            Document.id == DocumentChunk.document_id,
        )
        .order_by(
            DocumentChunk.document_id,
            DocumentChunk.chunk_index,
        )
    )

    rows = db.execute(statement).all()

    if not rows:
        return []

    chunk_terms: list[list[str]] = []
    term_frequencies: list[Counter[str]] = []
    document_frequencies: Counter[str] = Counter()

    for chunk, _ in rows:
        searchable_text = f"{chunk.source_title or ''} {chunk.text}"
        tokens = tokenize_keyword_text(searchable_text)
        chunk_terms.append(tokens)

        frequencies = Counter(tokens)
        term_frequencies.append(frequencies)

        for term in set(tokens):
            document_frequencies[term] += 1

    total_chunks = len(rows)
    average_document_length = sum(len(tokens) for tokens in chunk_terms) / total_chunks

    scored_rows: list[tuple[float, object, str]] = []

    for index, (chunk, original_filename) in enumerate(rows):
        frequencies = term_frequencies[index]
        document_length = len(chunk_terms[index])
        score = 0.0

        for term in query_terms:
            term_frequency = frequencies.get(term, 0)

            if term_frequency == 0:
                continue

            idf = _bm25_idf(
                total_chunks=total_chunks,
                document_frequency=document_frequencies[term],
            )
            term_score = _bm25_term_score(
                term_frequency=term_frequency,
                document_length=document_length,
                average_document_length=average_document_length,
                k1=k1,
                b=b,
            )
            score += idf * term_score

        if score > 0:
            scored_rows.append((score, chunk, original_filename))

    scored_rows.sort(
        key=lambda item: (
            -item[0],
            str(item[1].document_id),
            item[1].chunk_index,
        )
    )

    return [
        KeywordSearchResult(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            original_filename=original_filename,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            page_number=chunk.page_number,
            bm25_score=score,
            source_title=chunk.source_title,
        )
        for score, chunk, original_filename in scored_rows[:top_k]
    ]

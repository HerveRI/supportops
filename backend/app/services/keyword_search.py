import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from threading import Lock
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


@dataclass(frozen=True)
class _IndexedChunk:
    chunk_id: UUID
    document_id: UUID
    original_filename: str
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    page_number: int | None
    source_title: str | None


@dataclass(frozen=True)
class _BM25Index:
    chunks: dict[UUID, _IndexedChunk]
    postings: dict[str, frozenset[UUID]]
    term_frequencies: dict[UUID, Counter[str]]
    document_lengths: dict[UUID, int]
    document_frequencies: Counter[str]
    average_document_length: float
    total_chunks: int


_index_lock = Lock()
_cached_index: _BM25Index | None = None


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


def _build_keyword_index(db: Session) -> _BM25Index:
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

    chunks: dict[UUID, _IndexedChunk] = {}
    postings: defaultdict[str, set[UUID]] = defaultdict(set)
    term_frequencies: dict[UUID, Counter[str]] = {}
    document_lengths: dict[UUID, int] = {}
    document_frequencies: Counter[str] = Counter()

    total_document_length = 0

    for chunk, original_filename in rows:
        searchable_text = f"{chunk.source_title or ''} {chunk.text}"
        tokens = tokenize_keyword_text(searchable_text)
        frequencies = Counter(tokens)

        chunks[chunk.id] = _IndexedChunk(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            original_filename=original_filename,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            page_number=chunk.page_number,
            source_title=chunk.source_title,
        )
        term_frequencies[chunk.id] = frequencies
        document_lengths[chunk.id] = len(tokens)
        total_document_length += len(tokens)

        for term in frequencies:
            postings[term].add(chunk.id)
            document_frequencies[term] += 1

    total_chunks = len(chunks)
    average_document_length = (
        total_document_length / total_chunks if total_chunks else 0.0
    )

    return _BM25Index(
        chunks=chunks,
        postings={term: frozenset(ids) for term, ids in postings.items()},
        term_frequencies=term_frequencies,
        document_lengths=document_lengths,
        document_frequencies=document_frequencies,
        average_document_length=average_document_length,
        total_chunks=total_chunks,
    )


def rebuild_keyword_index(db: Session) -> None:
    """Build and publish the BM25 corpus index from the current database state."""
    global _cached_index

    new_index = _build_keyword_index(db)

    with _index_lock:
        _cached_index = new_index


def invalidate_keyword_index() -> None:
    """Discard the cached BM25 index so the next search rebuilds it."""
    global _cached_index

    with _index_lock:
        _cached_index = None


def _get_keyword_index(db: Session) -> _BM25Index:
    """Return the cached index, rebuilding only as a restart/failure fallback."""
    global _cached_index

    with _index_lock:
        cached_index = _cached_index

    if cached_index is not None:
        return cached_index

    new_index = _build_keyword_index(db)

    with _index_lock:
        if _cached_index is None:
            _cached_index = new_index

        return _cached_index


def keyword_search(
    db: Session,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    k1: float = DEFAULT_BM25_K1,
    b: float = DEFAULT_BM25_B,
) -> list[KeywordSearchResult]:
    """Rank matching stored chunks with BM25 over normalized lexical terms."""
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

    index = _get_keyword_index(db)

    if index.total_chunks == 0:
        return []

    candidate_chunk_ids: set[UUID] = set()

    for term in query_terms:
        candidate_chunk_ids.update(index.postings.get(term, ()))

    scored_chunks: list[tuple[float, _IndexedChunk]] = []

    for chunk_id in candidate_chunk_ids:
        frequencies = index.term_frequencies[chunk_id]
        document_length = index.document_lengths[chunk_id]
        score = 0.0

        for term in query_terms:
            term_frequency = frequencies.get(term, 0)

            if term_frequency == 0:
                continue

            idf = _bm25_idf(
                total_chunks=index.total_chunks,
                document_frequency=index.document_frequencies[term],
            )
            term_score = _bm25_term_score(
                term_frequency=term_frequency,
                document_length=document_length,
                average_document_length=index.average_document_length,
                k1=k1,
                b=b,
            )
            score += idf * term_score

        if score > 0:
            scored_chunks.append((score, index.chunks[chunk_id]))

    scored_chunks.sort(
        key=lambda item: (
            -item[0],
            str(item[1].document_id),
            item[1].chunk_index,
        )
    )

    return [
        KeywordSearchResult(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            original_filename=chunk.original_filename,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            page_number=chunk.page_number,
            bm25_score=score,
            source_title=chunk.source_title,
        )
        for score, chunk in scored_chunks[:top_k]
    ]

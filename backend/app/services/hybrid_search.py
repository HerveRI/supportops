from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.services.keyword_search import KeywordSearchResult, keyword_search
from app.services.retrieval import SimilaritySearchResult, search_knowledge_base

DEFAULT_TOP_K = 3
DEFAULT_RRF_K = 60
DEFAULT_CANDIDATE_MULTIPLIER = 3

SearchResult = KeywordSearchResult | SimilaritySearchResult


@dataclass(frozen=True)
class HybridSearchResult:
    chunk_id: UUID
    document_id: UUID
    original_filename: str
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    page_number: int | None
    rrf_score: float
    keyword_rank: int | None
    semantic_rank: int | None
    source_title: str | None = None

    @property
    def source_name(self) -> str:
        """Return the logical source title, falling back to the uploaded filename."""
        return self.source_title or self.original_filename


def reciprocal_rank_score(rank: int | None, k: int = DEFAULT_RRF_K) -> float:
    if rank is None:
        return 0.0

    if rank <= 0:
        raise ValueError("rank must be greater than zero")

    if k <= 0:
        raise ValueError("k must be greater than zero")

    return 1.0 / (k + rank)


def _result_key(result: SearchResult) -> str:
    if result.source_title:
        return f"title:{result.source_title}"

    return f"chunk:{result.chunk_id}"


def _add_ranked_results(
    combined: dict[str, dict[str, object]],
    results: Sequence[SearchResult],
    rank_name: str,
) -> None:
    for rank, result in enumerate(results, start=1):
        key = _result_key(result)
        entry = combined.get(key)

        if entry is None:
            combined[key] = {
                "result": result,
                "keyword_rank": None,
                "semantic_rank": None,
                rank_name: rank,
                "best_rank": rank,
            }
            continue

        if entry[rank_name] is None:
            entry[rank_name] = rank

        best_rank = entry["best_rank"]

        if isinstance(best_rank, int) and rank < best_rank:
            entry["result"] = result
            entry["best_rank"] = rank


def hybrid_search(
    db: Session,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    rrf_k: int = DEFAULT_RRF_K,
    candidate_multiplier: int = DEFAULT_CANDIDATE_MULTIPLIER,
    keyword_query: str | None = None,
) -> list[HybridSearchResult]:
    """Combine BM25 and semantic rankings with reciprocal rank fusion."""
    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty")

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    if rrf_k <= 0:
        raise ValueError("rrf_k must be greater than zero")

    if candidate_multiplier <= 0:
        raise ValueError("candidate_multiplier must be greater than zero")

    if keyword_query is None:
        keyword_query = query
    else:
        keyword_query = keyword_query.strip()
        if not keyword_query:
            raise ValueError("Keyword search query cannot be empty")

    candidate_k = top_k * candidate_multiplier

    keyword_results = keyword_search(
        db=db,
        query=keyword_query,
        top_k=candidate_k,
    )
    semantic_results = search_knowledge_base(
        db=db,
        query=query,
        top_k=candidate_k,
    )

    combined: dict[str, dict[str, object]] = {}

    _add_ranked_results(
        combined=combined,
        results=keyword_results,
        rank_name="keyword_rank",
    )
    _add_ranked_results(
        combined=combined,
        results=semantic_results,
        rank_name="semantic_rank",
    )

    fused_results: list[HybridSearchResult] = []

    for entry in combined.values():
        result = entry["result"]
        keyword_rank = entry["keyword_rank"]
        semantic_rank = entry["semantic_rank"]

        if not isinstance(result, (KeywordSearchResult, SimilaritySearchResult)):
            raise TypeError("Unexpected search result type")

        if keyword_rank is not None and not isinstance(keyword_rank, int):
            raise TypeError("Unexpected keyword rank type")

        if semantic_rank is not None and not isinstance(semantic_rank, int):
            raise TypeError("Unexpected semantic rank type")

        score = reciprocal_rank_score(keyword_rank, rrf_k) + reciprocal_rank_score(
            semantic_rank, rrf_k
        )

        fused_results.append(
            HybridSearchResult(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                original_filename=result.original_filename,
                chunk_index=result.chunk_index,
                text=result.text,
                start_char=result.start_char,
                end_char=result.end_char,
                page_number=result.page_number,
                rrf_score=score,
                keyword_rank=keyword_rank,
                semantic_rank=semantic_rank,
                source_title=result.source_title,
            )
        )

    fused_results.sort(
        key=lambda result: (
            -result.rrf_score,
            result.source_name,
            result.chunk_index,
        )
    )

    return fused_results[:top_k]

from uuid import uuid4

import pytest

from app.services import hybrid_search
from app.services.keyword_search import KeywordSearchResult
from app.services.retrieval import SimilaritySearchResult


def _keyword_result(title: str, chunk_index: int) -> KeywordSearchResult:
    text = f"Description for {title}"
    return KeywordSearchResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        original_filename="movies.json",
        chunk_index=chunk_index,
        text=text,
        start_char=0,
        end_char=len(text),
        page_number=None,
        bm25_score=2.0,
        source_title=title,
    )


def _semantic_result(title: str, chunk_index: int) -> SimilaritySearchResult:
    text = f"Another chunk for {title}"
    return SimilaritySearchResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        original_filename="movies.json",
        chunk_index=chunk_index,
        text=text,
        start_char=0,
        end_char=len(text),
        page_number=None,
        cosine_similarity=0.8,
        source_title=title,
    )


def test_hybrid_search_fuses_different_chunks_from_same_movie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        hybrid_search,
        "keyword_search",
        lambda **kwargs: [
            _keyword_result("Nightly", 10),
            _keyword_result("Daybreak", 20),
        ],
    )
    monkeypatch.setattr(
        hybrid_search,
        "search_knowledge_base",
        lambda **kwargs: [
            _semantic_result("Nightly", 11),
            _semantic_result("Elsewhere", 30),
        ],
    )

    results = hybrid_search.hybrid_search(
        db=object(),  # type: ignore[arg-type]
        query="Nightly",
        top_k=3,
    )

    assert results[0].source_name == "Nightly"
    assert results[0].keyword_rank == 1
    assert results[0].semantic_rank == 1


def test_reciprocal_rank_score() -> None:
    assert hybrid_search.reciprocal_rank_score(1, 60) == pytest.approx(1 / 61)
    assert hybrid_search.reciprocal_rank_score(None, 60) == 0.0

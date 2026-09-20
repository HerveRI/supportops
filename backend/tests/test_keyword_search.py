from types import SimpleNamespace
from uuid import uuid4

from app.services.keyword_search import (
    invalidate_keyword_index,
    keyword_search,
    rebuild_keyword_index,
)


class FakeExecutionResult:
    def __init__(self, rows: list[tuple[object, str]]) -> None:
        self.rows = rows

    def all(self) -> list[tuple[object, str]]:
        return self.rows


class FakeSession:
    def __init__(self, rows: list[tuple[object, str]]) -> None:
        self.rows = rows
        self.execute_count = 0

    def execute(self, statement: object) -> FakeExecutionResult:
        self.execute_count += 1
        return FakeExecutionResult(self.rows)


def _chunk(title: str, text: str, index: int = 0) -> object:
    return SimpleNamespace(
        id=uuid4(),
        document_id=uuid4(),
        chunk_index=index,
        text=text,
        start_char=0,
        end_char=len(text),
        page_number=None,
        source_title=title,
    )


def test_rebuild_keyword_index_prepares_cache_before_search() -> None:
    invalidate_keyword_index()

    nightly = _chunk("Nightly", "A reporter investigates a strange late-night signal.")
    session = FakeSession([(nightly, "movies.json")])

    rebuild_keyword_index(session)  # type: ignore[arg-type]

    results = keyword_search(
        db=session,  # type: ignore[arg-type]
        query="What is the movie Nightly about?",
    )

    assert results[0].source_name == "Nightly"
    assert session.execute_count == 1


def test_keyword_search_reuses_cached_index() -> None:
    invalidate_keyword_index()

    nightly = _chunk("Nightly", "A reporter investigates a strange late-night signal.")
    session = FakeSession([(nightly, "movies.json")])

    first_results = keyword_search(
        db=session,  # type: ignore[arg-type]
        query="What is the movie Nightly about?",
    )
    second_results = keyword_search(
        db=session,  # type: ignore[arg-type]
        query="Nightly reporter",
    )

    assert first_results[0].source_name == "Nightly"
    assert second_results[0].source_name == "Nightly"
    assert session.execute_count == 1


def test_keyword_search_rebuilds_after_invalidation() -> None:
    invalidate_keyword_index()

    nightly = _chunk("Nightly", "A reporter investigates a strange late-night signal.")
    session = FakeSession([(nightly, "movies.json")])

    keyword_search(
        db=session,  # type: ignore[arg-type]
        query="Nightly",
    )

    invalidate_keyword_index()

    keyword_search(
        db=session,  # type: ignore[arg-type]
        query="Nightly",
    )

    assert session.execute_count == 2


def test_keyword_search_only_returns_matching_candidates() -> None:
    invalidate_keyword_index()

    nightly = _chunk("Nightly", "A reporter investigates a strange late-night signal.")
    daybreak = _chunk("Daybreak", "A family begins a new life in another city.")
    session = FakeSession(
        [
            (nightly, "movies.json"),
            (daybreak, "movies.json"),
        ]
    )

    results = keyword_search(
        db=session,  # type: ignore[arg-type]
        query="Nightly",
        top_k=5,
    )

    assert len(results) == 1
    assert results[0].source_name == "Nightly"


def test_keyword_search_rejects_empty_query() -> None:
    invalidate_keyword_index()

    try:
        keyword_search(
            db=object(),  # type: ignore[arg-type]
            query="   ",
        )
    except ValueError as exc:
        assert str(exc) == "Search query cannot be empty"
    else:
        raise AssertionError("Expected ValueError")

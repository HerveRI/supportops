from types import SimpleNamespace
from uuid import uuid4

from app.services.keyword_search import keyword_search


class FakeExecutionResult:
    def __init__(self, rows: list[tuple[object, str]]) -> None:
        self.rows = rows

    def all(self) -> list[tuple[object, str]]:
        return self.rows


class FakeSession:
    def __init__(self, rows: list[tuple[object, str]]) -> None:
        self.rows = rows

    def execute(self, statement: object) -> FakeExecutionResult:
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


def test_keyword_search_rewards_exact_title_term() -> None:
    nightly = _chunk("Nightly", "A reporter investigates a strange late-night signal.")
    other = _chunk("Daybreak", "A family begins a new life in another city.")

    results = keyword_search(
        db=FakeSession(  # type: ignore[arg-type]
            [
                (nightly, "movies.json"),
                (other, "movies.json"),
            ]
        ),
        query="What is the movie Nightly about?",
        top_k=2,
    )

    assert len(results) == 1
    assert results[0].source_name == "Nightly"
    assert results[0].bm25_score > 0


def test_keyword_search_rejects_empty_query() -> None:
    try:
        keyword_search(
            db=object(),  # type: ignore[arg-type]
            query="   ",
        )
    except ValueError as exc:
        assert str(exc) == "Search query cannot be empty"
    else:
        raise AssertionError("Expected ValueError")

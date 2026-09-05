from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import retrieval


class FakeExecutionResult:
    def __init__(self, rows: list[tuple[object, str, float]]) -> None:
        self.rows = rows

    def all(self) -> list[tuple[object, str, float]]:
        return self.rows


class FakeSession:
    def __init__(self, rows: list[tuple[object, str, float]]) -> None:
        self.rows = rows

    def execute(self, statement: object) -> FakeExecutionResult:
        return FakeExecutionResult(self.rows)


def test_search_knowledge_base_maps_database_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chunk_id = uuid4()
    document_id = uuid4()

    chunk = SimpleNamespace(
        id=chunk_id,
        document_id=document_id,
        chunk_index=2,
        text="Reset the device before reconnecting it.",
        start_char=100,
        end_char=142,
        page_number=None,
    )

    session = FakeSession(
        rows=[
            (
                chunk,
                "support-guide.txt",
                0.2,
            )
        ]
    )

    monkeypatch.setattr(
        retrieval,
        "embed_texts",
        lambda texts: [[0.0] * 384],
    )

    results = retrieval.search_knowledge_base(
        db=session,  # type: ignore[arg-type]
        query="How do I reset the device?",
        top_k=5,
    )

    assert len(results) == 1

    result = results[0]

    assert result.chunk_id == chunk_id
    assert result.document_id == document_id
    assert result.original_filename == "support-guide.txt"
    assert result.chunk_index == 2
    assert result.cosine_similarity == pytest.approx(0.8)


def test_search_knowledge_base_rejects_empty_query() -> None:
    with pytest.raises(ValueError):
        retrieval.search_knowledge_base(
            db=object(),  # type: ignore[arg-type]
            query="   ",
        )


def test_search_knowledge_base_rejects_invalid_top_k() -> None:
    with pytest.raises(ValueError):
        retrieval.search_knowledge_base(
            db=object(),  # type: ignore[arg-type]
            query="reset procedure",
            top_k=0,
        )

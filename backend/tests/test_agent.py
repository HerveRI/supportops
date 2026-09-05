from uuid import uuid4

import pytest

from app.services import agent
from app.services.llm import LLMError
from app.services.retrieval import SimilaritySearchResult


def make_search_result() -> SimilaritySearchResult:
    return SimilaritySearchResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        original_filename="support-guide.txt",
        chunk_index=3,
        text="Reset the device before reconnecting it.",
        start_char=100,
        end_char=142,
        page_number=None,
        cosine_similarity=0.91,
    )


def test_agent_can_answer_without_retrieval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_chat_with_ollama(
        messages: list[dict],
        tools: list[dict] | None = None,
        think: bool = False,
    ) -> dict:
        return {
            "role": "assistant",
            "content": "Hello!",
        }

    def fail_if_retrieval_runs(*args: object, **kwargs: object) -> None:
        raise AssertionError("Retrieval should not run for a greeting")

    monkeypatch.setattr(
        agent,
        "chat_with_ollama",
        fake_chat_with_ollama,
    )
    monkeypatch.setattr(
        agent,
        "search_knowledge_base",
        fail_if_retrieval_runs,
    )

    result = agent.answer_with_agent(
        db=object(),  # type: ignore[arg-type]
        question="Hi",
    )

    assert result.answer == "Hello!"
    assert result.used_retrieval is False
    assert result.citations == []


def test_agent_returns_validated_citation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = make_search_result()

    responses = iter(
        [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "search_knowledge_base",
                            "arguments": {
                                "query": "device reset procedure",
                            },
                        }
                    }
                ],
            },
            {
                "role": "assistant",
                "content": ("Reset the device before reconnecting it. [1]"),
            },
        ]
    )

    def fake_chat_with_ollama(
        messages: list[dict],
        tools: list[dict] | None = None,
        think: bool = False,
    ) -> dict:
        return next(responses)

    def fake_search_knowledge_base(
        db: object,
        query: str,
        top_k: int,
    ) -> list[SimilaritySearchResult]:
        assert query == "device reset procedure"
        return [source]

    monkeypatch.setattr(
        agent,
        "chat_with_ollama",
        fake_chat_with_ollama,
    )
    monkeypatch.setattr(
        agent,
        "search_knowledge_base",
        fake_search_knowledge_base,
    )

    result = agent.answer_with_agent(
        db=object(),  # type: ignore[arg-type]
        question="How do I reset the device?",
    )

    assert result.used_retrieval is True
    assert len(result.citations) == 1
    assert result.citations[0].citation_number == 1
    assert result.citations[0].source == source


def test_agent_rejects_invented_citation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = make_search_result()

    responses = iter(
        [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "search_knowledge_base",
                            "arguments": {
                                "query": "device reset procedure",
                            },
                        }
                    }
                ],
            },
            {
                "role": "assistant",
                "content": "Use the reset procedure. [2]",
            },
        ]
    )

    monkeypatch.setattr(
        agent,
        "chat_with_ollama",
        lambda **kwargs: next(responses),
    )

    monkeypatch.setattr(
        agent,
        "search_knowledge_base",
        lambda **kwargs: [source],
    )

    with pytest.raises(
        LLMError,
        match="invalid citation",
    ):
        agent.answer_with_agent(
            db=object(),  # type: ignore[arg-type]
            question="How do I reset the device?",
        )

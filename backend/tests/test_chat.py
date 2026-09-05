from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.api.routes import chat as chat_route
from app.db.session import get_db_session
from app.main import app
from app.services.agent import AgentCitation, AgentResult
from app.services.retrieval import SimilaritySearchResult


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides.clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def override_db_session():
    yield object()


def override_current_user():
    return SimpleNamespace(
        id=uuid4(),
        email="member@example.com",
        role="member",
        is_active=True,
    )


def test_chat_requires_authentication(
    client: TestClient,
) -> None:
    app.dependency_overrides[get_db_session] = override_db_session

    response = client.post(
        "/chat",
        json={"question": "Hello"},
    )

    assert response.status_code == 401


def test_chat_returns_answer_and_citations(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = SimilaritySearchResult(
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

    agent_result = AgentResult(
        answer="Reset the device before reconnecting it. [1]",
        citations=[
            AgentCitation(
                citation_number=1,
                source=source,
            )
        ],
        used_retrieval=True,
    )

    monkeypatch.setattr(
        chat_route,
        "answer_with_agent",
        lambda **kwargs: agent_result,
    )

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_current_user] = override_current_user

    response = client.post(
        "/chat",
        json={
            "question": "How do I reset the device?",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == ("Reset the device before reconnecting it. [1]")
    assert len(data["citations"]) == 1
    assert data["citations"][0]["citation_number"] == 1
    assert data["citations"][0]["original_filename"] == ("support-guide.txt")


def test_chat_rejects_whitespace_question(
    client: TestClient,
) -> None:
    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_current_user] = override_current_user

    response = client.post(
        "/chat",
        json={"question": "   "},
    )

    assert response.status_code == 422

import json
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.chat import ChatCitation, ChatRequest, ChatResponse
from app.services.agent import (
    AgentCitation,
    answer_with_agent,
    stream_answer_with_agent,
)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


def _to_chat_citation(citation: AgentCitation) -> ChatCitation:
    """Convert an internal agent citation to the public API schema."""

    return ChatCitation(
        citation_number=citation.citation_number,
        chunk_id=citation.source.chunk_id,
        document_id=citation.source.document_id,
        original_filename=citation.source.original_filename,
        chunk_index=citation.source.chunk_index,
        text=citation.source.text,
        page_number=citation.source.page_number,
    )


def _stream_chat_events(db: Session, question: str) -> Iterator[str]:
    """Convert agent stream events to newline-delimeted JSON."""

    for event in stream_answer_with_agent(
        db=db,
        question=question,
    ):
        if event.type == "content":
            if event.content is None:
                raise RuntimeError("Content stream event is missing content")

            payload = {
                "type": "content",
                "content": event.content,
            }
        elif event.type == "citations":
            if event.citations is None:
                raise RuntimeError("Citation stream event is missing citations")

            payload = {
                "type": "citations",
                "citations": [
                    _to_chat_citation(citation).model_dump(mode="json")
                    for citation in event.citations
                ],
            }
        elif event.type == "done":
            if event.used_retrieval is None:
                raise RuntimeError("Done stream event is missing retrieval status")

            payload = {
                "type": "done",
                "used_retrieval": event.used_retrieval,
            }
        else:
            raise RuntimeError(f"Unknown stream event type: {event.type}")

        yield json.dumps(payload, ensure_ascii=False) + "\n"


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ChatResponse:
    result = answer_with_agent(
        db=session,
        question=request.question,
    )

    return ChatResponse(
        answer=result.answer,
        citations=[_to_chat_citation(citation) for citation in result.citations],
    )


@router.post("/stream")
def stream_chat(
    request: ChatRequest,
    session: Annotated[Session, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    return StreamingResponse(
        _stream_chat_events(
            db=session,
            question=request.question,
        ),
        media_type="application/x-ndjson",
    )

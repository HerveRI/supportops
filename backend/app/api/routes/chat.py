from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.chat import ChatCitation, ChatRequest, ChatResponse
from app.services.agent import answer_with_agent

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


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
        citations=[
            ChatCitation(
                citation_number=citation.citation_number,
                chunk_id=citation.source.chunk_id,
                document_id=citation.source.document_id,
                original_filename=citation.source.original_filename,
                chunk_index=citation.source.chunk_index,
                text=citation.source.text,
                page_number=citation.source.page_number,
            )
            for citation in result.citations
        ],
    )

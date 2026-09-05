from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be empty")

        return value


class ChatCitation(BaseModel):
    citation_number: int
    chunk_id: UUID
    document_id: UUID
    original_filename: str
    chunk_index: int
    text: str
    page_number: int | None


class ChatResponse(BaseModel):
    answer: str
    citations: list[ChatCitation]

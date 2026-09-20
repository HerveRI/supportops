from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.config import settings
from app.db.session import get_db_session
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.chunking import chunk_extractions, store_document_chunks
from app.services.embeddings import embed_document_chunks
from app.services.text_extraction import TextExtractionError, extract_document_texts

router = APIRouter(
    prefix="/admin/documents",
    tags=["documents"],
)

SUPPORTED_DOCUMENT_TYPES = {
    ".txt": "text/plain",
    ".json": "application/json",
}


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    file: Annotated[UploadFile, File()],
    db_session: Annotated[Session, Depends(get_db_session)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> Document:
    original_filename = Path(file.filename or "").name

    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename",
        )

    if len(original_filename) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is too long",
        )

    suffix = Path(original_filename).suffix.lower()
    content_type = SUPPORTED_DOCUMENT_TYPES.get(suffix)

    if content_type is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .txt and .json files are supported",
        )

    contents = file.file.read(settings.max_document_size_bytes + 1)

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file cannot be empty",
        )

    if len(contents) > settings.max_document_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file exceeds the maximum allowed size",
        )

    try:
        contents.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must contain valid UTF-8 text",
        ) from exc

    document_id = uuid4()
    storage_key = f"{document_id}{suffix}"

    storage_directory = settings.document_storage_dir
    storage_directory.mkdir(parents=True, exist_ok=True)

    storage_path = storage_directory / storage_key

    try:
        storage_path.write_bytes(contents)

        document = Document(
            id=document_id,
            original_filename=original_filename,
            content_type=content_type,
            file_size_bytes=len(contents),
            storage_key=storage_key,
            uploaded_by_user_id=admin_user.id,
        )

        db_session.add(document)
        db_session.flush()

        extractions = extract_document_texts(
            document=document,
            storage_root=storage_directory,
        )
        chunks = chunk_extractions(extractions)
        store_document_chunks(
            db=db_session,
            document_id=document.id,
            chunks=chunks,
        )
        embed_document_chunks(
            db=db_session,
            document_id=document.id,
        )

        db_session.commit()
        db_session.refresh(document)

    except TextExtractionError as exc:
        db_session.rollback()

        if storage_path.exists():
            storage_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        db_session.rollback()

        if storage_path.exists():
            storage_path.unlink()

        raise

    return document

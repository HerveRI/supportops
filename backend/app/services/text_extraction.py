from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.models.document import Document


@dataclass(frozen=True)
class TextExtractionResult:
    document_id: UUID
    original_filename: str
    text: str
    page_number: int | None = None


class TextExtractionError(Exception):
    """Base error for document text extraction failures."""


class UnsafeDocumentStoragePathError(TextExtractionError):
    """Raised when a storage key resolves outside the configured storage root."""


class StoredDocumentNotFoundError(TextExtractionError):
    """Raised when the stored document file cannot be found."""


class StoredDocumentMetadataError(TextExtractionError):
    """Raised when document metadata does not match the stored file."""


class StoredDocumentDecodeError(TextExtractionError):
    """Raised when stored document bytes are not valid UTF-8."""


class StoredDocumentReadError(TextExtractionError):
    """Raised when the stored document cannot be read."""


def _resolve_document_path(storage_root: Path, storage_key: str) -> Path:
    root = storage_root.resolve()
    key_path = Path(storage_key)

    if key_path.is_absolute() or key_path.name != storage_key:
        raise UnsafeDocumentStoragePathError(
            f"Invalid document storage key: {storage_key!r}"
        )

    document_path = (root / key_path).resolve()

    if not document_path.is_relative_to(root):
        raise UnsafeDocumentStoragePathError(
            f"Document storage path escapes configured storage root: {storage_key!r}"
        )

    return document_path


def extract_document_text(
    document: Document,
    storage_root: Path,
) -> TextExtractionResult:
    """Read and decode one stored UTF-8 text document."""
    if Path(document.original_filename).suffix.lower() != ".txt":
        raise StoredDocumentMetadataError(
            "Document original filename is not a supported .txt file"
        )

    if Path(document.storage_key).suffix.lower() != ".txt":
        raise StoredDocumentMetadataError(
            "Document storage key is not a supported .txt file"
        )

    if document.file_size_bytes <= 0:
        raise StoredDocumentMetadataError(
            "Document file size metadata must be greater than zero"
        )

    document_path = _resolve_document_path(
        storage_root,
        document.storage_key,
    )

    if not document_path.is_file():
        raise StoredDocumentNotFoundError(
            f"Stored file not found for document {document.id}"
        )

    try:
        file_bytes = document_path.read_bytes()
    except OSError as e:
        raise StoredDocumentReadError(
            f"Could not read stored file for document {document.id}"
        ) from e

    if len(file_bytes) != document.file_size_bytes:
        raise StoredDocumentMetadataError(
            "Stored file size does not match document metadata"
        )

    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        raise StoredDocumentDecodeError(
            f"Stored file for document {document.id} is not valid UTF-8"
        ) from e

    return TextExtractionResult(
        document_id=document.id,
        original_filename=document.original_filename,
        text=text,
        page_number=None,
    )

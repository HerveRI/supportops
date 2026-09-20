import json
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
    source_title: str | None = None


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


class StoredDocumentFormatError(TextExtractionError):
    """Raised when a structured document has an invalid format."""


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


def _read_stored_document(document: Document, storage_root: Path) -> str:
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
    except OSError as exc:
        raise StoredDocumentReadError(
            f"Could not read stored file for document {document.id}"
        ) from exc

    if len(file_bytes) != document.file_size_bytes:
        raise StoredDocumentMetadataError(
            "Stored file size does not match document metadata"
        )

    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StoredDocumentDecodeError(
            f"Stored file for document {document.id} is not valid UTF-8"
        ) from exc


def _validate_matching_suffix(document: Document, expected_suffix: str) -> None:
    if Path(document.original_filename).suffix.lower() != expected_suffix:
        raise StoredDocumentMetadataError(
            f"Document original filename is not a supported {expected_suffix} file"
        )

    if Path(document.storage_key).suffix.lower() != expected_suffix:
        raise StoredDocumentMetadataError(
            f"Document storage key is not a supported {expected_suffix} file"
        )


def extract_document_text(
    document: Document,
    storage_root: Path,
) -> TextExtractionResult:
    """Read and decode one stored UTF-8 text document."""
    _validate_matching_suffix(document, ".txt")
    text = _read_stored_document(document, storage_root)

    return TextExtractionResult(
        document_id=document.id,
        original_filename=document.original_filename,
        text=text,
        page_number=None,
        source_title=None,
    )


def _extract_movie_json(
    document: Document,
    storage_root: Path,
) -> list[TextExtractionResult]:
    _validate_matching_suffix(document, ".json")
    text = _read_stored_document(document, storage_root)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StoredDocumentFormatError("Movie dataset is not valid JSON") from exc

    if not isinstance(data, dict):
        raise StoredDocumentFormatError("The Dataset must be a JSON object")

    records = data.get("movies")

    if not isinstance(records, list) or not records:
        raise StoredDocumentFormatError("Movie dataset must be a non-empty JSON list")

    extractions: list[TextExtractionResult] = []

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise StoredDocumentFormatError(
                f"Movie record at index {index} must be a JSON object"
            )

        if "id" not in record:
            raise StoredDocumentFormatError(
                f"Movie record at index {index} is missing id"
            )

        title = record.get("title")
        description = record.get("description")

        if not isinstance(title, str) or not title.strip():
            raise StoredDocumentFormatError(
                f"Movie record at index {index} must have a non-empty title"
            )

        if not isinstance(description, str) or not description.strip():
            raise StoredDocumentFormatError(
                f"Movie record at index {index} must have a non-empty description"
            )

        extractions.append(
            TextExtractionResult(
                document_id=document.id,
                original_filename=document.original_filename,
                text=description.strip(),
                page_number=None,
                source_title=title.strip(),
            )
        )

    return extractions


def extract_document_texts(
    document: Document,
    storage_root: Path,
) -> list[TextExtractionResult]:
    """Extract one or more searchable text records from a stored document."""
    suffix = Path(document.original_filename).suffix.lower()

    if suffix == ".txt":
        return [extract_document_text(document, storage_root)]

    if suffix == ".json":
        return _extract_movie_json(document, storage_root)

    raise StoredDocumentMetadataError(
        f"Unsupported document type: {suffix or 'no extension'}"
    )

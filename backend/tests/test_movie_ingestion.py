import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.chunking import chunk_extractions
from app.services.text_extraction import (
    StoredDocumentFormatError,
    extract_document_texts,
)


def test_movie_json_extraction_and_chunking_preserve_titles(tmp_path) -> None:
    records = [
        {
            "id": 1,
            "title": "Short Movie",
            "description": "short",
        },
        {
            "id": 2,
            "title": "Long Movie",
            "description": "abcdefghijklmnop",
        },
    ]
    contents = json.dumps({"movies": records}).encode("utf-8")
    storage_key = "movies.json"
    (tmp_path / storage_key).write_bytes(contents)

    document = SimpleNamespace(
        id=uuid4(),
        original_filename="movies.json",
        storage_key=storage_key,
        file_size_bytes=len(contents),
    )

    extractions = extract_document_texts(document, tmp_path)

    assert len(extractions) == 2
    assert extractions[0].source_title == "Short Movie"
    assert extractions[0].text == "short"
    assert extractions[1].source_title == "Long Movie"

    chunks = chunk_extractions(
        extractions,
        chunk_size=10,
        chunk_overlap=2,
    )

    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert [chunk.source_title for chunk in chunks] == [
        "Short Movie",
        "Long Movie",
        "Long Movie",
    ]
    assert chunks[1].text == "abcdefghij"
    assert chunks[2].text == "ijklmnop"


def test_movie_json_requires_title_and_description(tmp_path) -> None:
    records = [
        {
            "id": 1,
            "description": "A movie without a title.",
        }
    ]
    contents = json.dumps({"movies": records}).encode("utf-8")
    storage_key = "movies.json"
    (tmp_path / storage_key).write_bytes(contents)

    document = SimpleNamespace(
        id=uuid4(),
        original_filename="movies.json",
        storage_key=storage_key,
        file_size_bytes=len(contents),
    )

    with pytest.raises(StoredDocumentFormatError, match="non-empty title"):
        extract_document_texts(document, tmp_path)

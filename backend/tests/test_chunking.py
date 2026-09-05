from uuid import uuid4

import pytest

from app.services.chunking import chunk_extracted_text
from app.services.text_extraction import TextExtractionResult


def test_chunk_extracted_text_uses_expected_overlap() -> None:
    extraction = TextExtractionResult(
        document_id=uuid4(),
        original_filename="test.txt",
        text="abcdefghij",
        page_number=None,
    )

    chunks = chunk_extracted_text(
        extraction,
        chunk_size=6,
        chunk_overlap=2,
    )

    assert len(chunks) == 2

    assert chunks[0].chunk_index == 0
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == 6
    assert chunks[0].text == "abcdef"

    assert chunks[1].chunk_index == 1
    assert chunks[1].start_char == 4
    assert chunks[1].end_char == 10
    assert chunks[1].text == "efghij"


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"),
    [
        (0, 0),
        (-1, 0),
        (100, -1),
        (100, 100),
        (100, 101),
    ],
)
def test_chunk_extracted_text_rejects_invalid_configuration(
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    extraction = TextExtractionResult(
        document_id=uuid4(),
        original_filename="test.txt",
        text="example text",
        page_number=None,
    )

    with pytest.raises(ValueError):
        chunk_extracted_text(
            extraction,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

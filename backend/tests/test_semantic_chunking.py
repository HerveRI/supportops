from uuid import uuid4

from app.services.semantic_chunking import chunk_extracted_text_semantically
from app.services.text_extraction import TextExtractionResult


def test_semantic_chunking_uses_sentence_boundaries_and_overlap() -> None:
    extraction = TextExtractionResult(
        document_id=uuid4(),
        original_filename="movies.json",
        text="One. Two. Three. Four. Five.",
        source_title="Example Movie",
    )

    chunks = chunk_extracted_text_semantically(
        extraction=extraction,
        sentences_per_chunk=3,
        sentence_overlap=1,
    )

    assert [chunk.text for chunk in chunks] == [
        "One. Two. Three.",
        "Three. Four. Five.",
    ]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1]
    assert all(chunk.source_title == "Example Movie" for chunk in chunks)

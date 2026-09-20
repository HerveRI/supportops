import re

from app.services.chunking import TextChunk
from app.services.text_extraction import TextExtractionResult

DEFAULT_SENTENCES_PER_CHUNK = 4
DEFAULT_SENTENCE_OVERLAP = 1

_SENTENCE_PATTERN = re.compile(r"[^.!?]+(?:[.!?]+|$)", re.MULTILINE)


def _sentence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []

    for match in _SENTENCE_PATTERN.finditer(text):
        start_char = match.start()
        end_char = match.end()

        while start_char < end_char and text[start_char].isspace():
            start_char += 1

        while end_char > start_char and text[end_char - 1].isspace():
            end_char -= 1

        if start_char < end_char:
            spans.append((start_char, end_char))

    return spans


def chunk_extracted_text_semantically(
    extraction: TextExtractionResult,
    sentences_per_chunk: int = DEFAULT_SENTENCES_PER_CHUNK,
    sentence_overlap: int = DEFAULT_SENTENCE_OVERLAP,
    starting_chunk_index: int = 0,
) -> list[TextChunk]:
    """Chunk extracted text on sentence boundaries with sentence overlap."""
    if sentences_per_chunk <= 0:
        raise ValueError("sentences_per_chunk must be greater than zero")

    if sentence_overlap < 0:
        raise ValueError("sentence_overlap cannot be negative")

    if sentence_overlap >= sentences_per_chunk:
        raise ValueError("sentence_overlap must be smaller than sentences_per_chunk")

    if starting_chunk_index < 0:
        raise ValueError("starting_chunk_index cannot be negative")

    text = extraction.text

    if not text.strip():
        return []

    sentence_spans = _sentence_spans(text)

    if not sentence_spans:
        return []

    chunks: list[TextChunk] = []
    chunk_index = starting_chunk_index
    first_sentence = 0
    step_size = sentences_per_chunk - sentence_overlap

    while first_sentence < len(sentence_spans):
        last_sentence = min(
            first_sentence + sentences_per_chunk,
            len(sentence_spans),
        )

        start_char = sentence_spans[first_sentence][0]
        end_char = sentence_spans[last_sentence - 1][1]

        chunks.append(
            TextChunk(
                document_id=extraction.document_id,
                original_filename=extraction.original_filename,
                chunk_index=chunk_index,
                text=text[start_char:end_char],
                start_char=start_char,
                end_char=end_char,
                page_number=extraction.page_number,
                source_title=extraction.source_title,
            )
        )

        if last_sentence == len(sentence_spans):
            break

        first_sentence += step_size
        chunk_index += 1

    return chunks


def chunk_extractions_semantically(
    extractions: list[TextExtractionResult],
    sentences_per_chunk: int = DEFAULT_SENTENCES_PER_CHUNK,
    sentence_overlap: int = DEFAULT_SENTENCE_OVERLAP,
) -> list[TextChunk]:
    """Semantic-chunk multiple extractions while keeping chunk indexes unique."""
    chunks: list[TextChunk] = []
    next_chunk_index = 0

    for extraction in extractions:
        extraction_chunks = chunk_extracted_text_semantically(
            extraction=extraction,
            sentences_per_chunk=sentences_per_chunk,
            sentence_overlap=sentence_overlap,
            starting_chunk_index=next_chunk_index,
        )

        chunks.extend(extraction_chunks)

        if extraction_chunks:
            next_chunk_index = extraction_chunks[-1].chunk_index + 1

    return chunks

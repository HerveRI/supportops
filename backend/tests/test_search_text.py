from app.services.search_text import preprocess_keyword_text, tokenize_keyword_text


def test_preprocess_keyword_text_normalizes_case_and_punctuation() -> None:
    assert preprocess_keyword_text("Nightly: A Movie!") == "nightly  a movie "


def test_tokenize_keyword_text_removes_stop_words_and_stems() -> None:
    tokens = tokenize_keyword_text("What is the movie Nightly about?")

    assert "what" not in tokens
    assert "the" not in tokens
    assert "about" not in tokens
    assert "nightli" in tokens

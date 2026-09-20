import string

from nltk.stem import PorterStemmer

STOP_WORDS = frozenset(
    {
        "a",
        "about",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "but",
        "by",
        "can",
        "could",
        "did",
        "do",
        "does",
        "for",
        "from",
        "had",
        "has",
        "have",
        "he",
        "her",
        "hers",
        "him",
        "his",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "me",
        "my",
        "of",
        "on",
        "or",
        "our",
        "ours",
        "she",
        "should",
        "that",
        "tell",
        "the",
        "their",
        "theirs",
        "them",
        "they",
        "this",
        "to",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "will",
        "with",
        "would",
        "you",
        "your",
        "yours",
    }
)

_STEMMER = PorterStemmer()
_PUNCTUATION_TO_SPACES = str.maketrans({char: " " for char in string.punctuation})


def preprocess_keyword_text(text: str) -> str:
    """Normalize case and punctuation for lexical search."""
    return text.lower().translate(_PUNCTUATION_TO_SPACES)


def tokenize_keyword_text(text: str) -> list[str]:
    """Tokenize lexical-search text, remove stop words, and stem terms."""
    normalized_text = preprocess_keyword_text(text)
    tokens = normalized_text.split()

    return [
        _STEMMER.stem(token) for token in tokens if token and token not in STOP_WORDS
    ]

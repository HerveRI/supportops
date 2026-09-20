import pytest

from app.services.evaluation import calculate_retrieval_metrics, deduplicate_titles


def test_deduplicate_titles_preserves_rank() -> None:
    assert deduplicate_titles(["The Matrix", "The Matrix", "Inception"]) == [
        "The Matrix",
        "Inception",
    ]


def test_calculate_retrieval_metrics() -> None:
    metrics = calculate_retrieval_metrics(
        retrieved_titles=["Wrong", "The Matrix", "The Matrix", "Inception"],
        relevant_titles=["The Matrix", "Inception"],
        k=3,
    )

    assert metrics.precision_at_k == pytest.approx(2 / 3)
    assert metrics.recall_at_k == pytest.approx(1.0)
    assert metrics.f1_at_k == pytest.approx(0.8)
    assert metrics.mrr == pytest.approx(0.5)

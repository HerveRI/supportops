from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalMetrics:
    precision_at_k: float
    recall_at_k: float
    f1_at_k: float
    mrr: float


def deduplicate_titles(titles: list[str]) -> list[str]:
    """Remove repeated titles while preserving retrieval order."""
    seen: set[str] = set()
    deduplicated: list[str] = []

    for title in titles:
        if title in seen:
            continue

        seen.add(title)
        deduplicated.append(title)

    return deduplicated


def calculate_retrieval_metrics(
    retrieved_titles: list[str],
    relevant_titles: list[str],
    k: int,
) -> RetrievalMetrics:
    """Calculate Precision@K, Recall@K, F1@K, and MRR."""
    if k <= 0:
        raise ValueError("k must be greater than zero")

    ranked_titles = deduplicate_titles(retrieved_titles)[:k]
    relevant = set(relevant_titles)

    if not relevant:
        raise ValueError("relevant_titles cannot be empty")

    relevant_retrieved = sum(title in relevant for title in ranked_titles)

    precision = relevant_retrieved / k
    recall = relevant_retrieved / len(relevant)

    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    reciprocal_rank = 0.0

    for rank, title in enumerate(ranked_titles, start=1):
        if title in relevant:
            reciprocal_rank = 1.0 / rank
            break

    return RetrievalMetrics(
        precision_at_k=precision,
        recall_at_k=recall,
        f1_at_k=f1,
        mrr=reciprocal_rank,
    )

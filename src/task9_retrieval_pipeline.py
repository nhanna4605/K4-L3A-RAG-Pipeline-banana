"""Hybrid retrieval with one RRF fusion and optional PageIndex fallback."""

import logging
import os

from dotenv import load_dotenv

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search

load_dotenv()
logger = logging.getLogger(__name__)
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD") or "0.3")
DEFAULT_TOP_K = 5


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Use the original dense cosine score to decide whether to try fallback."""
    if not query.strip() or top_k <= 0:
        return []
    dense = semantic_search(query, top_k=top_k * 2)
    if not use_reranking:
        # Dense-only baseline: neither fusion nor fallback changes its results.
        return dense[:top_k]
    sparse = lexical_search(query, top_k=top_k * 2)
    hybrid = rerank_rrf([dense, sparse], top_k=top_k)
    best_dense_score = dense[0]["score"] if dense else 0.0
    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback[:top_k]
        except Exception as exc:
            logger.warning("PageIndex unavailable (%s); using hybrid results", type(exc).__name__)
    return hybrid[:top_k]


if __name__ == "__main__":
    for result in retrieve("test query", top_k=3):
        print(result)

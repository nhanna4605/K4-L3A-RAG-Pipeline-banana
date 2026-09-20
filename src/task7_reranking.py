"""
Task 7 — Reciprocal Rank Fusion.

RRF gộp nhiều bảng xếp hạng mà không cộng trực tiếp cosine score với BM25
score. Công thức: RRF(d) = sum(1 / (k + rank)), rank bắt đầu từ 1.

Lưu ý: RRF score chỉ phản ánh thứ hạng, không dùng để quyết định fallback.
"""


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse nhiều ranked lists và trả hybrid SearchResult.

    Dense score (cosine 0..1) và BM25 score (không chặn trên) khác thang đo nên
    không cộng trực tiếp được; RRF chỉ dùng thứ hạng nên miễn nhiễm với việc này.
    """
    if top_k <= 0:
        return []

    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    best_rank: dict[str, int] = {}

    for ranked_list in ranked_lists:
        if not ranked_list:
            continue
        for rank, item in enumerate(ranked_list, 1):  # rank bắt đầu từ 1
            item_id = item["id"]
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
            # Giữ bản ghi từ list xếp nó cao nhất để content/metadata ổn định.
            if item_id not in best_rank or rank < best_rank[item_id]:
                best_rank[item_id] = rank
                items[item_id] = item

    # Tie-break bằng ID để thứ tự tái lập được giữa các lần chạy.
    ranked_ids = sorted(scores, key=lambda item_id: (-scores[item_id], item_id))

    results = []
    for item_id in ranked_ids[:top_k]:
        result = dict(items[item_id])  # copy: không mutate input
        result["score"] = scores[item_id]
        result["retrieval_method"] = "hybrid"
        results.append(result)
    return results


if __name__ == "__main__":
    print("Implement rerank_rrf, then run contract tests.")

"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

import re


# Corpus chunks dùng chung với Task 4/5. Để rỗng lúc import và nạp lười trong
# lexical_search() để test có thể monkeypatch mà không chạm vào ChromaDB.
CORPUS: list[dict] = []

_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)

# Cache index theo đúng object corpus đang dùng, tránh rebuild mỗi query.
_index_cache: tuple[list[dict], object, list[set]] | None = None


def tokenize(text: str) -> list[str]:
    """Tách token, bỏ dấu câu và hạ chữ thường.

    Giữ nguyên dấu tiếng Việt vì `\\w` ở chế độ Unicode coi chúng là ký tự chữ,
    nhờ vậy "điểm chuẩn" không bị vỡ thành token vô nghĩa.
    """
    return _TOKEN_PATTERN.findall(text.lower())


def load_corpus() -> list[dict]:
    """Nạp toàn bộ chunks đã index từ ChromaDB làm corpus cho BM25."""
    from .task4_chunking_indexing import get_collection

    response = get_collection().get(include=["documents", "metadatas"])
    return [
        {"id": item_id, "content": content, "metadata": dict(metadata)}
        for item_id, content, metadata in zip(
            response["ids"], response["documents"], response["metadatas"]
        )
    ]


def _build_index(corpus: list[dict]):
    """Trả về (bm25, token_sets) và cache theo object corpus hiện hành."""
    from rank_bm25 import BM25Okapi

    global _index_cache
    if _index_cache is not None and _index_cache[0] is corpus:
        return _index_cache[1], _index_cache[2]

    tokenized = [tokenize(item["content"]) for item in corpus]
    bm25 = BM25Okapi(tokenized)
    token_sets = [set(tokens) for tokens in tokenized]
    _index_cache = (corpus, bm25, token_sets)
    return bm25, token_sets


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    return _build_index(corpus)[0]


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if not query or not query.strip() or top_k <= 0:
        return []

    global CORPUS
    if not CORPUS:
        CORPUS = load_corpus()
    corpus = CORPUS
    if not corpus:
        return []

    tokens = tokenize(query)
    if not tokens:
        return []

    bm25, token_sets = _build_index(corpus)
    scores = bm25.get_scores(tokens)
    query_tokens = set(tokens)

    # Chỉ giữ document thực sự khớp ít nhất một token. Không thể lọc bằng
    # `score > 0`: khi một token xuất hiện trong mọi document, idf của BM25Okapi
    # bằng log(N-n+0.5) - log(n+0.5) = 0 nên document khớp vẫn nhận score 0.
    matched = [
        index
        for index in range(len(corpus))
        if query_tokens & token_sets[index]
    ]
    matched.sort(key=lambda index: scores[index], reverse=True)

    results = []
    for index in matched[:top_k]:
        item = corpus[index]
        results.append(
            {
                "id": item["id"],
                "content": item["content"],
                "score": float(scores[index]),
                "metadata": dict(item["metadata"]),
                "retrieval_method": "bm25",
            }
        )
    return results


if __name__ == "__main__":
    for result in lexical_search("Điểm chuẩn ngành Khoa học máy tính", top_k=3):
        print(f"{result['score']:.4f}  {result['id']}")
        print(f"    {result['content'][:120]}...")

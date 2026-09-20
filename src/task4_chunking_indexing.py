"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
# 500/50: đề án tuyển sinh và quy chế gồm nhiều điều/khoản ngắn. Chunk 500 ký tự
# thường giữ trọn một khoản mà không kéo theo khoản không liên quan; overlap 50
# (10%) đủ để câu bị cắt giữa chừng vẫn còn ngữ cảnh ở chunk kế tiếp.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"

BATCH_SIZE = 32

# Cache trong process: model local rất nặng, không load lại mỗi lần gọi.
_model_cache = None
_collection_cache = None


def _get_sentence_transformer():
    """Load và cache SentenceTransformer model."""
    global _model_cache
    if _model_cache is None:
        from sentence_transformers import SentenceTransformer

        print(f"Loading embedding model: {EMBEDDING_MODEL} (lần đầu sẽ tải model)")
        _model_cache = SentenceTransformer(EMBEDDING_MODEL)
    return _model_cache


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed danh sách text bằng provider cấu hình trong .env.

    Task 5 phải gọi đúng hàm này để query và corpus nằm cùng không gian vector.
    """
    if not texts:
        return []

    if EMBEDDING_PROVIDER == "sentence_transformers":
        model = _get_sentence_transformer()
        vectors = model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=len(texts) > BATCH_SIZE,
            normalize_embeddings=True,
        )
        return [vector.tolist() for vector in vectors]

    if EMBEDDING_PROVIDER == "gemini":
        from google import genai

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
        vectors = []
        for start in range(0, len(texts), BATCH_SIZE):
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts[start : start + BATCH_SIZE],
            )
            vectors.extend(item.values for item in response.embeddings)
        return vectors

    if EMBEDDING_PROVIDER == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        vectors = []
        for start in range(0, len(texts), BATCH_SIZE):
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts[start : start + BATCH_SIZE],
            )
            vectors.extend(item.embedding for item in response.data)
        return vectors

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    global _collection_cache
    if _collection_cache is None:
        import chromadb

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection_cache = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection_cache


def _extract_title(text: str, fallback: str) -> str:
    """Lấy H1 đầu tiên làm title, không có thì dùng tên file."""
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if match and match.group(1).strip():
        return match.group(1).strip()
    return fallback


def _extract_url(text: str) -> str | None:
    """Đọc URL gốc từ header `**Source:**` do Task 3 sinh ra.

    Chấp nhận cả biến thể có khoảng trắng (`** Source :**`) vì Task 2/3 sinh ra
    dạng này; khớp chặt theo đúng một format sẽ làm mất URL của toàn bộ news.
    """
    match = re.search(r"^\*\*\s*Source\s*:\s*\*\*\s*(\S+)", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def load_documents() -> list[dict]:
    """Đọc Markdown trong data/standardized và trả về danh sách Document."""
    documents = []
    if not STANDARDIZED_DIR.is_dir():
        return documents

    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            print(f"Skip empty file: {path.name}")
            continue

        doc_type = "legal" if "legal" in path.parts else "news"
        documents.append(
            {
                # Relative path là ID ổn định: chạy lại pipeline không sinh trùng.
                "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
                "content": content,
                "metadata": {
                    "source": path.name,
                    "title": _extract_title(content, path.stem),
                    "doc_type": doc_type,
                    "url": _extract_url(content),
                },
            }
        )
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id ổn định và chunk_index."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for document in documents:
        index = 0
        for text in splitter.split_text(document["content"]):
            text = text.strip()
            if not text:
                # Contract: chunk không được rỗng.
                continue
            chunks.append(
                {
                    "id": f"{document['id']}::chunk-{index}",
                    "content": text,
                    "metadata": {**document["metadata"], "chunk_index": index},
                }
            )
            index += 1
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk, giữ nguyên các field còn lại."""
    if not chunks:
        return []

    vectors = embed_texts([chunk["content"] for chunk in chunks])
    if len(vectors) != len(chunks):
        raise ValueError(
            f"Embedding count mismatch: {len(vectors)} vectors / {len(chunks)} chunks"
        )
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks


def _chroma_metadata(metadata: dict) -> dict:
    """Chroma không nhận giá trị None nên url=None được lưu thành chuỗi rỗng."""
    return {key: ("" if value is None else value) for key, value in metadata.items()}


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB; upsert nên chạy lại không tạo bản trùng."""
    if not chunks:
        print("Nothing to index")
        return

    collection = get_collection()
    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["content"] for chunk in batch],
            embeddings=[chunk["embedding"] for chunk in batch],
            metadatas=[_chroma_metadata(chunk["metadata"]) for chunk in batch],
        )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    if not documents:
        print(
            f"Không tìm thấy Markdown trong {STANDARDIZED_DIR}.\n"
            "Chạy Task 1-3 để thu thập và chuẩn hoá dữ liệu trước."
        )
        return

    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)

    legal = sum(1 for doc in documents if doc["metadata"]["doc_type"] == "legal")
    print(f"Documents: {len(documents)} ({legal} legal, {len(documents) - legal} news)")
    print(f"Indexed {len(embedded_chunks)} chunks -> {CHROMA_DIR}")
    print(f"Collection '{COLLECTION_NAME}' holds {get_collection().count()} chunks")


if __name__ == "__main__":
    run_pipeline()

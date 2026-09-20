"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Đề tài: Quy chế và phương thức xét tuyển đại học Việt Nam 2025-2026.

Nguồn là cổng văn bản pháp luật của Chính phủ và Bộ GD&ĐT. Lý do không dùng
"đề án tuyển sinh" của từng trường: các đề án đều là bản scan có chữ ký và con
dấu nên không có lớp text, MarkItDown bóc ra 0 ký tự. Đã kiểm chứng với đề án
của VinUni (4.9MB -> 0 ký tự) và NEU (10.5MB -> 0 ký tự).

Mọi file tải về đều phải qua verify_pdf(). Tải lỗi thì dừng và báo lỗi; không
được tạo dữ liệu thay thế để test xanh.
"""

import tempfile
from pathlib import Path

import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

# Ngưỡng text tối thiểu để loại bản scan. Văn bản pháp luật thật đều vượt xa
# mức này (thấp nhất trong danh sách dưới đây là 19.202 ký tự).
MIN_TEXT_CHARS = 500

TIMEOUT = 90
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Mỗi URL đã được kiểm tra bằng verify_pdf() trước khi đưa vào danh sách.
DOCUMENTS = [
    {
        "filename": "thong-tu-06-2026-quy-che-tuyen-sinh.pdf",
        "url": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/3/06-bgddt.pdf",
        "note": "Quy chế tuyển sinh đại học và cao đẳng ngành GD Mầm non",
    },
    {
        "filename": "thong-tu-06-2025-sua-doi-quy-che-tuyen-sinh.pdf",
        "url": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/3/06-bgddt.pdf",
        "note": "Sửa đổi, bổ sung Quy chế tuyển sinh kèm Thông tư 08/2022",
    },
    {
        "filename": "vbhn-02-2026-quy-che-thi-tot-nghiep-thpt.pdf",
        "url": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/4/02-vbhn-bgddt-kem.pdf",
        "note": "Quy chế thi tốt nghiệp THPT (văn bản hợp nhất)",
    },
]


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def verify_pdf(content: bytes) -> int:
    """Trả về số ký tự text bóc được, raise nếu file không dùng được.

    Bắt ba lỗi đã thực sự xảy ra khi thu thập corpus:
      1. Trang HTML báo lỗi được trả về với đuôi .pdf
      2. Server trả HTTP 200 kèm nội dung trang lỗi
      3. PDF hợp lệ nhưng là bản scan ảnh, không có lớp text
    """
    if not content.startswith(b"%PDF"):
        raise ValueError(f"Không phải PDF (bytes đầu: {content[:12]!r})")

    from pdfminer.high_level import extract_text

    path = Path(tempfile.gettempdir()) / "_verify_legal.pdf"
    path.write_bytes(content)
    try:
        text = extract_text(str(path)).strip()
    finally:
        path.unlink(missing_ok=True)

    if len(text) < MIN_TEXT_CHARS:
        raise ValueError(
            f"Chỉ bóc được {len(text)} ký tự (<{MIN_TEXT_CHARS}) — nhiều khả năng là bản scan ảnh"
        )
    return len(text)


def download_documents() -> None:
    """Tải các văn bản và chỉ ghi ra đĩa khi đã verify thành công."""
    failures = []

    for document in DOCUMENTS:
        filename = document["filename"]
        try:
            response = requests.get(
                document["url"], headers=HEADERS, timeout=TIMEOUT
            )
            response.raise_for_status()
            chars = verify_pdf(response.content)
        except Exception as error:
            # Không tạo file thay thế: corpus giả làm test xanh nhưng sản phẩm hỏng.
            print(f"FAILED  {filename}\n        {type(error).__name__}: {error}")
            failures.append(filename)
            continue

        (DATA_DIR / filename).write_bytes(response.content)
        size_kb = len(response.content) // 1024
        print(f"OK      {filename}\n        {size_kb}KB, {chars} ký tự text — {document['note']}")

    if failures:
        raise RuntimeError(
            f"{len(failures)}/{len(DOCUMENTS)} tài liệu tải lỗi: {', '.join(failures)}. "
            "Tìm URL thay thế trên vanban.chinhphu.vn, không tạo dữ liệu giả."
        )
    print(f"\nĐã thu thập {len(DOCUMENTS)} tài liệu vào {DATA_DIR}")


if __name__ == "__main__":
    setup_directory()
    download_documents()

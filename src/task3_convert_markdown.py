"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Legal: MarkItDown convert PDF sang Markdown.
News:  đọc JSON và gắn header metadata lên đầu file.

Header `**Source:**` được Task 4 dùng để bóc URL gốc cho citation — đổi format
là toàn bộ news mất link nguồn.

File nào convert ra quá ngắn thì bị loại và báo lỗi. Không độn thêm chữ cho đủ
ngưỡng của test: test xanh mà nội dung rỗng thì chatbot trả lời bằng rác.
"""

import json
from pathlib import Path


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

# Test acceptance yêu cầu >=200 ký tự; đặt cao hơn để bắt lỗi sớm và rõ.
MIN_CHARS = 500


def convert_legal_docs() -> None:
    """Convert PDF/DOCX trong landing/legal sang standardized/legal."""
    from markitdown import MarkItDown

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    converter = MarkItDown()
    converted, skipped = 0, []

    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue

        try:
            text = converter.convert(str(path)).text_content.strip()
        except Exception as error:
            print(f"FAILED  {path.name}: {type(error).__name__}: {error}")
            skipped.append(path.name)
            continue

        if len(text) < MIN_CHARS:
            print(f"SKIP    {path.name}: chỉ {len(text)} ký tự — bản scan hoặc file hỏng")
            skipped.append(path.name)
            continue

        # Tiêu đề từ tên file để Task 4 có title đọc được, giữ metadata nguồn.
        title = path.stem.replace("-", " ")
        body = f"# {title}\n\n**Source:** {path.name}\n\n---\n\n{text}"
        (output_dir / f"{path.stem}.md").write_text(body, encoding="utf-8")
        converted += 1
        print(f"OK      {path.stem}.md  {len(text)} ký tự")

    if skipped:
        raise RuntimeError(
            f"{len(skipped)} tài liệu legal không convert được: {', '.join(skipped)}. "
            "Thay tài liệu khác, không độn chữ cho đủ ngưỡng."
        )
    print(f"Legal: {converted} file")


def convert_news_articles() -> None:
    """Convert JSON trong landing/news sang standardized/news."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    converted, skipped = 0, []

    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        content = data["content_markdown"].strip()

        if len(content) < MIN_CHARS:
            print(f"SKIP    {path.name}: chỉ {len(content)} ký tự")
            skipped.append(path.name)
            continue

        # Task 4 regex đúng dòng `**Source:**` để lấy URL cho citation.
        header = (
            f"# {data['title']}\n\n"
            f"**Source:** {data['url']}\n\n"
            f"**Crawled:** {data['date_crawled']}\n\n---\n\n"
        )
        (output_dir / f"{path.stem}.md").write_text(header + content, encoding="utf-8")
        converted += 1
        print(f"OK      {path.stem}.md  {len(content)} ký tự")

    if skipped:
        raise RuntimeError(
            f"{len(skipped)} bài news quá ngắn: {', '.join(skipped)}. Crawl lại hoặc bỏ URL đó."
        )
    print(f"News: {converted} file")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"\nSaved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()

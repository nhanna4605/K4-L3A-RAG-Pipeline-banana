"""
Task 2 — Crawl bài viết/thông báo.

Đề tài: Quy chế và phương thức xét tuyển đại học Việt Nam 2025-2026.

URL được chọn tay theo đúng chủ đề, không lấy từ RSS feed. Feed giáo dục chung
trả về bài thuộc mọi chủ đề (ẩm thực, du học, tin vặt), đưa vào corpus sẽ làm
context precision tụt và citation trỏ tới bài không liên quan.

Mỗi bài chỉ lưu đúng nội dung crawl được. Không chèn thêm văn bản soạn sẵn vào
content: kiến thức phải nằm trong corpus, không nằm trong mã nguồn crawler.
"""

import asyncio
import datetime
import json
import re
from pathlib import Path

import markdownify
import requests
from bs4 import BeautifulSoup


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

TIMEOUT = 45
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Độ dài tối thiểu để coi là crawl thành công. Ngắn hơn nghĩa là trúng trang
# chặn bot hoặc trang lỗi; khi đó bỏ bài, không độn thêm chữ cho đủ.
MIN_CONTENT_CHARS = 600

# Bài về quy chế và phương thức xét tuyển đại học, chọn tay từ VnExpress.
ARTICLE_URLS = [
    "https://vnexpress.net/du-kien-doi-cach-xet-tuyen-dai-hoc-2027-gioi-han-moi-nganh-chi-xet-bang-mot-phuong-thuc-5121397.html",
    "https://vnexpress.net/du-kien-bo-diem-cong-ielts-giai-hoc-sinh-gioi-trong-xet-tuyen-dai-hoc-5121573.html",
    "https://vnexpress.net/bo-giao-duc-va-dao-tao-neu-ly-do-siet-phuong-thuc-tuyen-sinh-dai-hoc-2027-5121541.html",
    "https://vnexpress.net/bo-giao-duc-va-dao-tao-doi-y-lui-lich-siet-phuong-thuc-tuyen-sinh-dai-hoc-5121531.html",
    "https://vnexpress.net/phu-huynh-thi-sinh-choi-voi-vi-du-kien-siet-phuong-thuc-tuyen-sinh-dai-hoc-5121727.html",
    "https://vnexpress.net/nhieu-hoc-sinh-lo-mat-loi-the-neu-bo-cong-diem-ielts-5122195.html",
    "https://vnexpress.net/sap-xep-doi-ten-hang-loat-nganh-o-dai-hoc-5121259.html",
    "https://vnexpress.net/giu-ky-thi-tot-nghiep-thpt-voi-da-muc-tieu-5122460.html",
    "https://vnexpress.net/chua-thi-diem-thi-tot-nghiep-thpt-tren-may-tinh-nam-2027-5122463.html",
]


def extract_article(html: bytes, url: str) -> tuple[str, str]:
    """Bóc tiêu đề và nội dung chính, bỏ nav/footer/script."""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else url
    # VnExpress đặt tiêu đề bài trong h1, chính xác hơn thẻ <title> có hậu tố báo.
    heading = soup.find("h1")
    if heading and heading.get_text(strip=True):
        title = heading.get_text(strip=True)

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
        tag.decompose()

    body = soup.find("article") or soup.body or soup
    content = markdownify.markdownify(str(body)).strip()
    # Bỏ ảnh placeholder lazy-load (GIF 1x1 nhúng base64) — chỉ là nhiễu trong chunk.
    content = re.sub(r"!\[[^\]]*\]\(data:[^)]*\)", "", content)
    # Gộp các dòng trống liên tiếp cho Markdown gọn.
    while "\n\n\n" in content:
        content = content.replace("\n\n\n", "\n\n")
    return title, content


async def crawl_article(url: str) -> dict:
    """Crawl một bài và trả về dict theo contract của Task 2."""
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()

    title, content = extract_article(response.content, url)
    if len(content) < MIN_CONTENT_CHARS:
        raise ValueError(
            f"Chỉ bóc được {len(content)} ký tự (<{MIN_CONTENT_CHARS}) — "
            "nhiều khả năng trúng trang chặn bot"
        )

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.datetime.now().isoformat(),
        "content_markdown": content,
    }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    saved = 0

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
        except Exception as error:
            print(f"FAILED  {url}\n        {type(error).__name__}: {error}")
            continue

        output = DATA_DIR / f"news_{index:02d}.json"
        output.write_text(
            json.dumps(article, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        saved += 1
        print(f"OK      news_{index:02d}.json  {len(article['content_markdown'])} ký tự")
        print(f"        {article['title'][:70]}")

    print(f"\nĐã lưu {saved}/{len(ARTICLE_URLS)} bài vào {DATA_DIR}")
    if saved < 5:
        raise RuntimeError(
            f"Chỉ crawl được {saved} bài, contract yêu cầu tối thiểu 5. "
            "Bổ sung URL công khai khác, không hạ tiêu chuẩn nội dung."
        )


if __name__ == "__main__":
    asyncio.run(crawl_all())

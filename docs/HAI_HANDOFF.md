# Bàn giao track data — Hải

## Đề tài

**Quy chế và phương thức xét tuyển đại học Việt Nam 2025–2026.**

Không bám vào một trường cụ thể. Lý do nằm ở phần dưới.

## Vì sao không dùng đề án tuyển sinh của trường

Đề án tuyển sinh là văn bản có chữ ký và con dấu nên trường nào cũng phát hành
bản scan ảnh — không có lớp text, MarkItDown bóc ra 0 ký tự. Đã đo:

| Tài liệu | Dung lượng | Text bóc được |
| -------- | ---------: | ------------: |
| Đề án tuyển sinh VinUni 2025 | 4.9MB | **0 ký tự** |
| Đề án tuyển sinh NEU 2025 | 10.5MB | **0 ký tự** |
| Thông tư 06/2026/TT-BGDĐT | 1.2MB | 66.536 ký tự |
| Thông tư 06/2025/TT-BGDĐT | 3.8MB | 19.202 ký tự |
| VBHN 02/2026 Quy chế thi THPT | 1.5MB | 188.353 ký tự |

Văn bản pháp luật trên `datafiles.chinhphu.vn` được xuất từ Word nên bóc text
sạch. Đó là lý do corpus xoay quanh quy chế thay vì quanh một trường.

Bản scan vẫn qua được `test_corpus_has_required_legal_documents` (chỉ kiểm tra
>1KB) nhưng trượt `test_standardized_output_covers_both_source_types` (yêu cầu
≥200 ký tự). Đây chính là chỗ dễ bị cám dỗ độn chữ cho test xanh.

## Corpus hiện tại

`data/landing/legal/` — 3 PDF, tải từ cổng văn bản Chính phủ:

- `thong-tu-06-2026-quy-che-tuyen-sinh.pdf`
- `thong-tu-06-2025-sua-doi-quy-che-tuyen-sinh.pdf`
- `vbhn-02-2026-quy-che-thi-tot-nghiep-thpt.pdf`

`data/landing/news/` — 9 bài VnExpress chọn tay về chính sách tuyển sinh: siết
phương thức xét tuyển 2027, bỏ cộng điểm IELTS, đổi tên ngành, kỳ thi tốt
nghiệp THPT.

Chọn tay thay vì lấy RSS feed. Feed giáo dục chung trả về bài thuộc mọi chủ đề;
đưa vào corpus sẽ kéo tụt context precision và làm citation trỏ tới bài không
liên quan.

## Ba cổng kiểm tra trong code

Thay cho việc tạo dữ liệu thay thế khi tải lỗi.

| Nơi | Hàm | Bắt lỗi gì |
| --- | --- | --- |
| Task 1 | `verify_pdf()` | Trang HTML đội lốt `.pdf`; HTTP lỗi; PDF là bản scan |
| Task 2 | `MIN_CONTENT_CHARS` | Trúng trang chặn bot, nội dung rỗng |
| Task 3 | `MIN_CHARS` | File convert ra quá ngắn |

Cả ba đều **raise** thay vì ghi dữ liệu thay thế. Corpus giả làm test xanh
nhưng chatbot trả lời bằng rác, và giảng viên chấm cả demo.

## Chạy lại

```bash
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown
pytest tests/test_acceptance.py -q -k "corpus or standardized"
```

Kiểm tra bằng mắt, đây là phần test không bắt được:

```bash
md5sum data/standardized/legal/*.md      # 3 hash phai KHAC nhau
head -30 data/standardized/legal/*.md    # noi dung that, khong lap cau
```

## Khi cần thay tài liệu

Nếu một URL chết, tìm URL thay thế trên `vanban.chinhphu.vn` rồi kiểm tra trước
khi thêm vào `DOCUMENTS`:

```python
from src.task1_collect_legal_docs import verify_pdf
import requests
print(verify_pdf(requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=90).content))
```

Đừng đoán URL theo mẫu — đã thử đoán 3 lần đều trả 404.

Một số site `.edu.vn` có chuỗi chứng chỉ hỏng và ném `SSLError`. Tải tay bằng
trình duyệt rồi verify file local, **không** vá bằng `verify=False`.

## Hạn chế còn lại

- Cả 9 bài news đều từ VnExpress. Đa dạng nguồn hơn sẽ tốt hơn, nhưng cần kiểm
  tra từng site có chặn bot không.
- Quy chế thi tốt nghiệp THPT (184K ký tự) dài hơn hẳn hai văn bản còn lại nên
  chiếm phần lớn số chunk. Nếu retrieval thiên lệch về văn bản này, cân nhắc bỏ
  bớt hoặc thêm tài liệu tuyển sinh khác để cân lại.
- Chưa có tài liệu của một trường cụ thể. Nếu tìm được đề án dạng văn bản (không
  scan) thì thêm vào sẽ giúp golden dataset có câu hỏi số liệu cụ thể hơn.

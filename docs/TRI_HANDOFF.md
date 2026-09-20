# Bàn giao phần Trí — feat/generation

## Đã triển khai

- Task 9: dense + BM25, gọi RRF một lần, dùng dense cosine score gốc cho fallback; PageIndex lỗi/không có kết quả thì giữ hybrid.
- `use_reranking=False` trả dense-only, bỏ BM25/RRF/PageIndex để dùng làm baseline.
- Task 10: reorder không sửa input; context chứa ID, title, source; số citation gắn theo thứ tự sources trước khi reorder.
- Dispatch OpenAI, Gemini, Anthropic; đọc model/key từ môi trường; timeout; lỗi trả safe refusal.
- Citation `[n]` phải nằm trong sources; thiếu citation hoặc sai số nguồn thì từ chối. Kiểm tra này chỉ xác minh liên kết nguồn, không chứng minh mọi phát biểu được nguồn hỗ trợ; vẫn cần đánh giá faithfulness trên corpus thật.
- UI hiển thị câu trả lời, nguồn, đoạn nội dung, phương thức và score; giữ sources khi rerun; xóa hội thoại.

## Cấu hình và chạy

Từ thư mục repo, dùng Python 3.10–3.13:

```bash
python -m pip install -e ".[dev]"
cp .env.example .env  # chỉ khi chưa có .env
```

Điền `LLM_PROVIDER`, `LLM_MODEL` và API key tương ứng. Không commit `.env`.
`SCORE_THRESHOLD` để trống dùng 0.3; nhóm phải hiệu chỉnh với corpus thật.

```bash
python -m pytest tests/test_contracts.py -q -k 'retrieve or reorder'
python -m pytest tests/test_generation.py -q
python -m streamlit run app.py
```

## Điểm tích hợp

Task 4–7 trong checkout ban đầu vẫn là skeleton; cần phần của các bạn trước để chạy dữ liệu thật. Task 8 tùy chọn chưa triển khai, được Task 9 bắt lỗi. Không có dữ liệu thật để điền golden dataset hay báo cáo metric; không coi mock test là kết quả evaluation.

Test offline thay search/LLM bằng dữ liệu giả, không gọi API và không cần API key. Chưa xác minh gọi thật ba provider.

Tài liệu API tham khảo:

- OpenAI: https://developers.openai.com/api/docs/quickstart
- Gemini: https://googleapis.github.io/python-genai/
- Anthropic: https://github.com/anthropics/anthropic-sdk-python

## Kết quả kiểm tra local

Chạy `python -m pytest -q --tb=short` bằng Python 3.11 trong môi trường test tạm:

- 27 passed, 9 failed.
- 4 test retrieve/reorder được giao: đạt.
- 16 test bổ sung trong `tests/test_generation.py`: đạt, gồm UI AppTest và dispatch provider giả.
- 4 contract test chưa đạt: Task 4 chunking, Task 5 dense, Task 6 BM25, Task 7 RRF vẫn `NotImplementedError`.
- 5 acceptance test chưa đạt: thiếu legal/news/Markdown, golden dataset trống và báo cáo còn TODO.
- Kiểm tra cú pháp Python và `git diff --check`: đạt.

Môi trường test: `/private/tmp/tri-rag-tests` (pytest, python-dotenv, Streamlit); không thay thế bước cài toàn bộ dependencies cho app thật.

## Commit sau khi review

```bash
git add src/task9_retrieval_pipeline.py src/task10_generation.py app.py tests/test_generation.py docs/TRI_HANDOFF.md
git commit -m "feat: implement retrieval, cited generation and chat UI"
git push -u origin feat/generation
```

# Day 8 — RAG Pipeline — Nhóm banana

Chatbot RAG trả lời câu hỏi về **quy chế và phương thức xét tuyển đại học Việt Nam 2025–2026**.

| Thành viên | MSV | Phụ trách |
| ---------- | --- | --------- |
| Võ Doanh Nhân | 2A202602770 | Task 4–7: chunking, indexing, dense search, BM25, RRF |
| Ngô Minh Trí | 2A202602993 | Task 8–10 + `app.py`: fallback, pipeline, generation, UI |
| Đào Đức Hải | 2A202602752 | Task 1–3: thu thập và chuẩn hoá corpus; evaluation |

## Corpus

| Loại | Số lượng | Nguồn |
| ---- | -------: | ----- |
| Văn bản pháp luật | 3 PDF | `datafiles.chinhphu.vn` — Thông tư 06/2026, Thông tư 06/2025, VBHN 02/2026 về quy chế thi tốt nghiệp THPT |
| Bài viết | 9 | VnExpress, chọn tay về chính sách tuyển sinh |

Không dùng đề án tuyển sinh của từng trường: các đề án đều là bản scan ảnh nên
bóc ra 0 ký tự text. Chi tiết và cách kiểm tra tài liệu trước khi nhận vào
corpus nằm trong [docs/HAI_HANDOFF.md](docs/HAI_HANDOFF.md).

## Cấu hình đã dùng

| Tham số | Giá trị |
| ------- | ------- |
| Embedding | `BAAI/bge-m3` (local, 1024 chiều) |
| Chunking | recursive, 500 ký tự, overlap 50 |
| Vector store | ChromaDB, cosine |
| Generation | Gemini `gemini-2.5-flash` |
| `SCORE_THRESHOLD` | 0.51 — hiệu chỉnh trên corpus thật, xem `RESULT.md` |

Mạng chập chờn thì đặt `HF_HUB_OFFLINE=1` sau khi đã tải model lần đầu, tránh
`sentence-transformers` gọi HF Hub kiểm tra cập nhật.

## Mục tiêu bài lab

Mỗi nhóm xây dựng một chatbot RAG trả lời câu hỏi từ bộ tài liệu do nhóm thu thập. Sản phẩm phải có hybrid retrieval, citation, giao diện chat và báo cáo đánh giá.

Nhóm tự chọn bài toán và thu thập dữ liệu phù hợp; repo không cung cấp dữ liệu mẫu.

## Sản phẩm phải nộp

- Repository nhóm chạy được.
- Tối thiểu 3 tài liệu chính sách và 5 bài viết/page do nhóm tự thu thập.
- Pipeline: convert → chunk → index → dense + BM25 → RRF → fallback → generation có citation.
- Chatbot Streamlit hiển thị câu trả lời và nguồn đã dùng.
- Golden dataset tối thiểu 15 câu; đánh giá 4 metric và so sánh A/B.
- `group_project/evaluation/RESULT.md`.
- Mỗi thành viên nộp báo cáo cá nhân theo template trong `group_project/ịndividual/INDIVIDUAL_REPORT.md`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
python -m playwright install chromium
cp .env.example .env
```

Điền API key cần dùng trong `.env`; không commit file này.

```bash
# 1. Thu thập và chuẩn hoá
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown

# 2. Index và kiểm tra contract
python -m src.task4_chunking_indexing
pytest -q

# 3. Chạy sản phẩm
streamlit run app.py
```

## Lộ trình 3 giờ

| Mốc                  | Thời gian | Kết quả cần có                           |
| -------------------- | --------: | ---------------------------------------- |
| 0. Setup             |   10 phút | Môi trường và `.env` sẵn sàng            |
| 1. Data              |   25 phút | ≥3 legal, ≥5 news, Markdown đã chuẩn hoá |
| 2. Index & search    |   30 phút | ChromaDB, dense search và BM25 chạy được |
| 3. Fusion & fallback |   25 phút | RRF và fallback tuân thủ contract        |
| 4. Generation & UI   |   30 phút | Chatbot trả lời có citation              |
| 5. Evaluation        |   30 phút | 15+ Q&A, 4 metric, A/B comparison        |
| 6. Demo & handoff    |   30 phút | Test, report, demo và push repository    |

## Lưu ý quy tắc để có code quality tốt:

- Dense và BM25 nên cùng trả về `SearchResult` theo một schema.
- RRF chỉ nên dùng để gộp thứ hạng và chỉ chạy một lần.
- Fallback dùng cosine score gốc của dense retrieval.
- Threshold phải được hiệu chỉnh trên query in domain và out of domain, không có một con số đúng cho mọi corpus.

## Tài liệu

- [Module contracts](docs/MODULE_CONTRACTS.md): schema, interface và invariant mà code/test nên tuân theo.
- [Step-by-step guide](docs/STEP_BY_STEP.md): thứ tự triển khai và tiêu chí hoàn thành từng bước.
- [Grading rubric](docs/GRADING_RUBRIC.md): Rubric thang điểm.
- [Individual report](group_project/ịndividual/INDIVIDUAL_REPORT.md): template báo cáo cá nhân.
- [Suggested topics](docs/SUGGESTED_TOPICS.md): danh sách chủ đề tham khảo, không bắt buộc.

## Kiểm tra

```bash
# Contract tests
pytest tests/test_contracts.py -q

# Acceptance tests
pytest tests/test_acceptance.py -q

# Toàn bộ
pytest -q
```

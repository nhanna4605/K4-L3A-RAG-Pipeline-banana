# Individual contribution report

## Thông tin

- Họ và tên: Võ Doanh Nhân
- Mã học viên: 2A202602770
- Nhóm: banana
- Repository/branch: https://github.com/nhanna4605/K4-L3A-RAG-Pipeline-banana — nhánh `feat/retrieval`, đã merge vào `main`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 4 — chunking, embedding, indexing | `embed_texts()` dispatch 3 provider, Chroma persistent cosine, `load_documents()` bóc title từ H1 và URL từ header, chunk 500/50 với `chunk_index` ổn định, upsert theo batch | `2890055` — `src/task4_chunking_indexing.py` | Done |
| Task 5 — dense search | Đổi cosine distance sang similarity, clamp `[0,1]`, dedupe ID, sort giảm dần | `2890055` — `src/task5_semantic_search.py` | Done |
| Task 6 — BM25 | BM25Okapi, tokenizer Unicode giữ dấu tiếng Việt, corpus nạp lười từ Chroma | `2890055` — `src/task6_lexical_search.py` | Done |
| Task 7 — RRF | `sum(1/(k+rank))` rank từ 1, copy item nên không mutate input, tie-break theo ID | `2890055` — `src/task7_reranking.py` | Done |
| Sửa lỗi tích hợp header | Regex bóc URL chấp nhận cả `** Source :**` | `4570a12` | Done |
| Hạ tầng repo | `.gitignore` cho `chroma_db/`; merge 3 nhánh vào `main` | `8a41ca8`, `c1c6d77`, `71f94df` | Done |
| Hiệu chỉnh threshold | Đo dense score in-domain và out-of-domain trên corpus thật, đề xuất `SCORE_THRESHOLD=0.51` | Số liệu trong `RESULT.md` | Done |
| Golden dataset | 5 câu G01–G05 dựa trên Thông tư 06/2026 | `group_project/evaluation/golden_dataset.json` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Lọc kết quả BM25 theo giao token giữa query và document, thay vì theo `score > 0`.
   **Lý do/evidence:** Cách lọc theo score làm `test_lexical_search_returns_bm25_contract` fail với `IndexError: list index out of range`. Nguyên nhân là `BM25Okapi` tính `idf = log(N-n+0.5) - log(n+0.5)`; với corpus 2 document và term xuất hiện ở 1 document thì `idf = log(1.5) - log(1.5) = 0`, nên document khớp hoàn hảo vẫn nhận score 0 và bị loại sạch.
   **Trade-off:** Cách mới có thể giữ lại document chỉ khớp một từ phổ biến với score 0. Chấp nhận được vì BM25 xếp chúng cuối bảng và RRF cho trọng số thấp; đổi lại không bao giờ mất document khớp thật trên corpus nhỏ.

2. **Quyết định:** Sanitize metadata trước khi upsert vào Chroma, đổi `url=None` thành chuỗi rỗng.
   **Lý do/evidence:** Tài liệu legal không có URL nên `metadata.url = None`. ChromaDB từ chối giá trị `None` trong metadata và làm `upsert()` crash. Contract cho phép `url` là `str` hoặc `None` nên lưu chuỗi rỗng vẫn hợp lệ.
   **Trade-off:** Mất khả năng phân biệt "không có URL" với "URL rỗng" khi đọc lại từ vector store. Không ảnh hưởng citation vì tài liệu legal vốn trích dẫn theo tên file.

## Kiểm thử và kết quả

- **Contract test:** `pytest tests/test_contracts.py -q` → 15 passed. Bốn test thuộc phần tôi: `chunk_documents`, `semantic_search`, `lexical_search`, `rrf`.
- **Smoke test trên Chroma thật:** contract test mock toàn bộ Chroma và embedding nên không chứng minh được pipeline chạy. Tôi dựng corpus nhỏ rồi kiểm tra 5 điểm: metadata `url=None` không làm crash upsert; chạy index hai lần cho count không đổi (11 → 11, ID ổn định); tokenize tiếng Việt có dấu đúng; dense và BM25 đồng thuận top-1; `rerank_rrf` không mutate list đầu vào.
- **Trên corpus thật (734 chunks / 12 documents):** dense score in-domain 0,6064–0,7233; out-of-domain 0,3766–0,4190; hai cụm tách rời với khoảng cách 0,1874.
- **Lỗi đã phát hiện và cách xử lý:**
  - Lỗi BM25 idf = 0 nêu ở phần trên.
  - `SCORE_THRESHOLD` mặc định 0,3 quá thấp: mọi câu hỏi lạc đề đều đạt 0,38–0,42, tức đều vượt ngưỡng, nên fallback không bao giờ kích hoạt và chatbot sẽ cố trả lời câu ngoài domain. Đề xuất nâng lên 0,51.
  - Regex bóc URL của tôi khớp chặt `**Source:**` trong khi Task 3 sinh ra `** Source :**`, làm toàn bộ news mất link nguồn. Sửa regex nhận cả hai dạng.

## Điều còn hạn chế

- **Hạn chế cụ thể:** Corpus lệch nặng về một tài liệu. Quy chế thi tốt nghiệp THPT dài 184.260 ký tự, chiếm phần lớn trong 734 chunk, trong khi Thông tư 06/2025 chỉ có 18.724 ký tự. Retrieval do đó thiên về tài liệu dài, và câu hỏi thuộc văn bản ngắn dễ bị chunk của văn bản dài lấn át.
- **Nếu có thêm thời gian:** Thử chunking theo cấu trúc điều/khoản thay vì cắt cứng 500 ký tự. Văn bản pháp luật có ranh giới ngữ nghĩa rõ ràng ở mỗi Điều, cắt theo đó sẽ giữ trọn một quy định trong một chunk và giảm hiện tượng câu trả lời bị đứt giữa hai chunk.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Võ Doanh Nhân

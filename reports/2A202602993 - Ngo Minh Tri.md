# Individual contribution report

## Thông tin

- Họ và tên: Ngô Minh Trí
- Mã học viên: 2A202602993
- Nhóm: banana
- Repository: https://github.com/nhanna4605/K4-L3A-RAG-Pipeline-banana
- Nhánh đóng góp: `feat/generation`; commit `a1bb215`, được tích hợp qua merge commit `71f94df`.
- Đề tài: Chatbot hỏi đáp quy chế và phương thức xét tuyển đại học Việt Nam 2025–2026.

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 9 — Retrieval pipeline | Ghép dense + BM25, gọi RRF một lần; dùng cosine score gốc để quyết định fallback; giữ hybrid khi PageIndex lỗi hoặc trả rỗng; hỗ trợ dense-only | `src/task9_retrieval_pipeline.py`, `a1bb215` | Done |
| Task 10 — Generation | Reorder không sửa input; format context có ID/title/source; citation ổn định; dispatch OpenAI/Gemini/Anthropic; trả safe refusal khi thiếu nguồn, citation không hợp lệ hoặc provider lỗi | `src/task10_generation.py`, `a1bb215` | Done — kiểm chứng offline |
| Giao diện chat | Nối generation; hiển thị answer, sources, retrieval method, score và link nguồn; lưu lịch sử kèm nguồn, xóa hội thoại | `app.py`, `a1bb215` | Done |
| Kiểm thử và bàn giao | Bổ sung 16 test offline cho generation, provider dispatch, retrieval và UI; ghi hướng dẫn cấu hình, chạy và tích hợp | `tests/test_generation.py`, `docs/TRI_HANDOFF.md`, `a1bb215` | Done |
| Task 8 — PageIndex | Đã xử lý lỗi tại nơi gọi trong Task 9; chưa triển khai upload/search của dịch vụ PageIndex | `src/task8_pageindex_vectorless.py` còn `NotImplementedError` | Partial |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** So sánh threshold với cosine score gốc của dense, chỉ fuse RRF một lần; bọc PageIndex trong `try/except`.
   **Lý do/evidence:** Cosine và RRF khác thang đo; dùng RRF score sẽ kích hoạt fallback sai. Ba test `test_retrieve_*` kiểm tra score, số lần fuse và khả năng chịu lỗi provider.
   **Trade-off:** Dịch vụ fallback lỗi thì vẫn có hybrid để trả lời, nhưng mất khả năng bổ sung bằng chứng từ PageIndex. Threshold cần hiệu chỉnh theo corpus.

2. **Quyết định:** Đánh số citation theo thứ tự retrieval trước khi reorder context, giữ nguyên danh sách `sources` theo score.
   **Lý do/evidence:** Tránh `[n]` trỏ nhầm nguồn sau reorder; test kiểm tra ánh xạ ID, số nguồn và input không bị sửa. Thiếu citation hoặc số ngoài phạm vi thì trả safe refusal.
   **Trade-off:** Kiểm tra được liên kết nguồn, chưa chứng minh mọi phát biểu được tài liệu hỗ trợ; cần đánh giá faithfulness riêng.

## Kiểm thử và kết quả

- **Lệnh chạy lại:** `python -m pytest tests/test_contracts.py -q -k 'retrieve or reorder'` và `python -m pytest tests/test_generation.py -q`.
- **Kết quả tại commit bàn giao `a1bb215`:** 4 test retrieve/reorder được giao và 16 test bổ sung đều đạt. Test bao phủ fallback lỗi/rỗng, citation sai, thiếu evidence, provider lỗi, dispatch ba SDK bằng mock, lưu nguồn khi UI rerun và xóa hội thoại; không gọi API thật.
- **Trạng thái toàn repo tại lần kiểm tra đó:** 27 passed, 9 failed do Task 4–7 chưa hoàn thiện và thiếu dữ liệu/evaluation. Đây là kết quả lịch sử trong `docs/TRI_HANDOFF.md`, không phải kết quả chạy lại sau khi merge các phần của nhóm.
- **Cấu hình tích hợp theo README hiện tại:** Gemini `gemini-2.5-flash`; embedding local `BAAI/bge-m3` (1024 chiều); chunk 500 ký tự, overlap 50; ChromaDB cosine; threshold nhóm đề xuất `0.51`. Phần tôi mặc định `top_k=5`, threshold `0.3` nếu biến môi trường trống; cần đặt `SCORE_THRESHOLD=0.51` để áp dụng cấu hình nhóm. Code gọi provider với timeout 30 giây. Nhóm đã đổi từ `gemini-3.6-flash` sang `gemini-2.5-flash` vì free tier chỉ cho 20 request/ngày cho mỗi model và `gemini-3.6-flash` hết quota ngay trong lần chạy thử đầu tiên.
- **Lỗi đã xử lý:** PageIndex/provider lỗi không làm luồng chat crash; citation giữ đúng nguồn khi đổi thứ tự context. Việc thu thập corpus, triển khai Task 4–7 và hiệu chỉnh threshold là phần đóng góp của các thành viên khác.

## Điều còn hạn chế

- Task 8 chưa có triển khai thực tế; phần generation mới có bằng chứng test offline, chưa xác minh gọi thật cả ba provider. Báo cáo `group_project/evaluation/RESULT.md` vẫn còn placeholder nên chưa có cơ sở công bố điểm metric hoặc kết luận A/B.
- Nếu có thêm thời gian: chạy generation với corpus và golden dataset của nhóm, kiểm tra từng citation có hỗ trợ câu trả lời, sau đó đo faithfulness và so sánh dense-only với hybrid trước khi hoàn thiện PageIndex.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Ngô Minh Trí

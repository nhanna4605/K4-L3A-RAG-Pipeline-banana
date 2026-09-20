# RAG evaluation results

Báo cáo đánh giá của nhóm nằm ở **[`group_project/evaluation/RESULT.md`](../group_project/evaluation/RESULT.md)**.

File này là bản sao template có sẵn trong repo gốc. Nhóm giữ lại một bản duy nhất
trong `group_project/evaluation/` theo đúng danh mục sản phẩm phải nộp trong README,
để tránh hai bản số liệu lệch nhau.

Dữ liệu thô và script tái lập kết quả cũng nằm cùng thư mục đó:

| File | Nội dung |
| ---- | -------- |
| `RESULT.md` | Báo cáo đánh giá đã điền đầy đủ |
| `golden_dataset.json` | 15 câu hỏi vàng kèm `expected_context` |
| `retrieval_ab.json` | Kết quả retrieval thô của hai config |
| `eval_raw.json` | Câu trả lời sinh ra và điểm từng câu |
| `phase1_retrieve.py` | Chạy retrieval cho Config A và B |
| `phase2_score.py` | Sinh câu trả lời và chấm 4 metric |
| `recompute_context.py` | Tính lại context recall/precision |
| `rotation.py` | Xoay vòng (API key, model) để vượt giới hạn quota |

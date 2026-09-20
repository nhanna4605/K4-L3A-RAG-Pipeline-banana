# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 20/09/2026 |
| Framework and version              | Bộ đánh giá tự viết (`phase1_retrieve.py` + `phase2_score.py`); context metric tính xác định bằng độ phủ chuỗi, faithfulness/answer relevance chấm bằng LLM judge. Không dùng ragas — lý do ở mục Ghi chú phương pháp. |
| Evaluator model                    | Gemini, xoay vòng `gemini-3.1-flash-lite`, `gemini-2.5-flash-lite`, `gemini-3.5-flash-lite`, `gemini-flash-lite-latest`, temperature 0.0 |
| Generator model                    | Gemini (cùng nhóm model xoay vòng), temperature 0.3, top_p 0.9 |
| Embedding model                    | `BAAI/bge-m3`, chạy local, 1024 chiều |
| Corpus version/commit              | `6cd7236` — 12 document (3 văn bản pháp luật + 9 bài VnExpress) → 734 chunk |
| Golden dataset size                | 15 câu, toàn bộ có `expected_context` trích nguyên văn từ corpus |
| `top_k`                            | 5 |
| Fallback threshold and calibration | **0.51**. Đo trên chính index này: 15 câu in-domain đạt 0,6402–0,8025 (TB 0,7222); 6 câu ngoài domain đạt 0,3766–0,4190 (TB 0,3979). Hai cụm tách rời, khoảng cách 0,2212; điểm giữa là 0,53. Chọn 0,51 nghiêng về phía an toàn. |

## Configurations

- **Config A — dense-only:** `retrieve(query, top_k=5, use_reranking=False)`. Chỉ dùng dense search trên ChromaDB, bỏ BM25 và RRF.
- **Config B — hybrid + RRF:** `retrieve(query, top_k=5, use_reranking=True)`. Dense + BM25, gộp bằng RRF `sum(1/(60+rank))` đúng một lần.

Hai config dùng cùng golden dataset, cùng generator, cùng prompt, cùng `top_k=5` và cùng index. Chỉ thay retrieval strategy.

Không câu nào trong 15 câu kích hoạt fallback PageIndex: dense score thấp nhất là 0,6402, vẫn trên ngưỡng 0,51.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |   1.0000 |   1.0000 |   +0.0000 |
| Answer relevance  |   1.0000 |   0.8667 |   −0.1333 |
| Context recall    |   0.8674 |   0.8469 |   −0.0205 |
| Context precision |   0.8000 |   0.7889 |   −0.0111 |
| **Average**       | **0.9169** | **0.8756** | **−0.0412** |

## A/B comparison

- **Cấu hình tốt hơn theo số đo: Config A (dense-only).** Nhưng chênh lệch này gây hiểu nhầm, xem phần dưới.

- **Evidence:** Config B thua toàn bộ ở cả ba metric có chênh lệch. Phần lớn khoảng cách đến từ đúng hai câu G04 và G07, nơi Config B trả lời từ chối còn Config A đưa ra câu trả lời. Bỏ hai câu đó ra thì hai config gần như bằng nhau.

- **Chênh lệch không phản ánh đúng chất lượng.** Ở G04, cả hai config đều **không lấy được đoạn văn đúng** (context recall = 0). Config A vẫn trả lời *"Tổng điểm cộng tối đa với một thí sinh là 3/30"* — con số này lấy từ `news_02.md` nói về bỏ cộng điểm IELTS, không phải quy định 10% trong Thông tư 06/2026. Câu trả lời **sai về nội dung nhưng trung thành với ngữ cảnh đã lấy**, nên judge vẫn chấm faithfulness 1,0 và answer relevance 1,0. Config B từ chối trả lời và bị chấm relevance 0,0 — tức là **bị phạt vì hành xử đúng**.

  Đây là hạn chế của metric, không phải của Config B: faithfulness đo tính trung thành với ngữ cảnh đã lấy, nên nó không phát hiện được trường hợp retrieval lấy nhầm tài liệu.

- **Chỉ có G07 là Config B thua thật.** Cả hai config đều lấy 5 chunk từ đúng văn bản Thông tư 06/2026, nhưng RRF đẩy chunk chứa Điều 8 khoản 1 ra khỏi top-5 (recall A = 0,31 → B = 0,00). BM25 kéo lên các chunk khác cùng văn bản có mật độ từ khoá "xét tuyển", "đối tượng" cao hơn nhưng không chứa danh sách đối tượng tuyển thẳng.

- **Trade-off latency/cost:** Config B chạy thêm một lượt BM25 trên 734 chunk cộng một lượt fusion, tốn thêm vài chục mili-giây mỗi query và không tốn thêm request LLM. Chi phí không đáng kể; vấn đề là chất lượng xếp hạng trên corpus này.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------- | ---------- |
|   1 | G04 — Tổng điểm cộng bị giới hạn ở mức nào? | A | 1.00 | 1.00 | 0.00 | 0.00 | retrieval | Không lấy được Điều 6 khoản 2 điểm c. Model trả lời bằng con số 3/30 từ `news_02.md` (bài về bỏ cộng điểm IELTS) — đúng với ngữ cảnh đã lấy nhưng sai so với quy định. Metric không bắt được vì faithfulness chỉ đối chiếu với ngữ cảnh. |
|   2 | G04 — như trên | B | 1.00 | 0.00 | 0.00 | 0.00 | retrieval | Cùng lỗi retrieval, nhưng model từ chối trả lời. Bị phạt relevance dù đây là hành vi đúng khi thiếu bằng chứng. |
|   3 | G07 — Đối tượng nào được xét tuyển thẳng? | B | 1.00 | 0.00 | 0.00 | 0.00 | retrieval | RRF đẩy chunk chứa Điều 8 khoản 1 ra khỏi top-5. Config A giữ được chunk này (recall 0,31) và trả lời đúng. BM25 ưu tiên chunk có mật độ từ khoá cao hơn nhưng không chứa danh sách đối tượng. |
|   4 | G03 — Xét tuyển sớm có thay đổi gì? | A và B | 1.00 | 1.00 | 0.70 | 1.00 | retrieval | Đoạn ground truth bị chunking cắt qua hai chunk, chỉ lấy được 70% độ phủ. Câu trả lời vẫn đúng nhờ phần lấy được. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Chunk theo cấu trúc Điều/Khoản thay vì cắt cứng 500 ký tự | G03 mất 30% độ phủ do ground truth bị cắt qua hai chunk; G04 và G07 đều là lỗi ranh giới chunk trong cùng một văn bản | Context recall tăng, đặc biệt với văn bản pháp luật có ranh giới ngữ nghĩa rõ | Chạy lại đúng 15 câu golden, so recall trước/sau |
|        2 | Thêm metric "answer correctness" đối chiếu với `expected_answer` | G04 cho thấy faithfulness 1,0 vẫn có thể đi kèm câu trả lời sai nội dung, vì nó chỉ đối chiếu với ngữ cảnh đã lấy | Phát hiện được lỗi retrieval lấy nhầm tài liệu mà bộ metric hiện tại bỏ sót | So điểm correctness của G04 với các câu khác |
|        3 | Cân lại tỷ trọng corpus giữa các văn bản | `vbhn-02-2026` dài 184.260 ký tự, chiếm phần lớn trong 734 chunk, lấn át Thông tư 06/2025 chỉ 18.724 ký tự | Giảm thiên lệch retrieval về tài liệu dài | Đếm phân bố nguồn trong top-5 của 15 câu golden |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Không thực hiện | — | — | — | Nhóm không làm HyDE, query expansion, reranker nâng cao hay conversation memory. Không có số liệu nào để công bố ở mục này. |

## Ghi chú phương pháp

**Vì sao không dùng ragas.** Free tier Gemini giới hạn **20 request/ngày cho mỗi cặp (API key, model)** — `quotaId: GenerateRequestsPerDayPerProjectPerModel`. Ragas với 4 metric gọi khoảng 9–10 request cho mỗi mẫu, tức khoảng 300 request cho 30 mẫu của hai config, vượt xa hạn mức. Bộ đánh giá tự viết gộp faithfulness và answer relevance vào một request judge, và tính hai metric context bằng thuật toán xác định không cần LLM, nên tổng chỉ tốn **60 request**. Số liệu chạy thật: 60/60 request thành công, phân bổ qua 4 model nhờ cơ chế xoay vòng.

**Cách tính context metric.** Cắt `expected_context` thành các cửa sổ 30 ký tự, bước nhảy 10, sau khi chuẩn hoá NFC, hạ chữ thường và gộp khoảng trắng.
- *Context recall* = tỷ lệ cửa sổ tìm thấy trong **hợp nhất** của cả top-5. Tính hợp nhất vì chunking có thể cắt đôi đoạn ground truth.
- *Context precision* = Average Precision@5, một chunk được coi là liên quan khi độ phủ riêng của nó đạt từ 0,30 trở lên.

Cách này xác định và tái lập được, không phụ thuộc phán đoán của LLM.

**Hạn chế đã biết.**
1. Faithfulness đạt 1,0 tuyệt đối ở cả 30 mẫu. Điều này cho thấy judge quá dễ dãi hoặc tiêu chí chưa đủ phân biệt — không nên đọc nó như bằng chứng hệ thống không bịa đặt. G04 là phản ví dụ trực tiếp.
2. Answer relevance phạt câu trả lời từ chối bằng 0,0, nên một hệ thống thận trọng đúng cách sẽ bị chấm thấp hơn một hệ thống trả lời liều.
3. Golden dataset 15 câu là mức tối thiểu; chênh lệch 0,0205 ở context recall tương đương chưa tới một câu, nằm trong khoảng nhiễu.
4. Chỉ chạy một lượt, không lặp lại nhiều lần nên không có khoảng tin cậy.

**Kết luận thận trọng.** Với corpus và bộ 15 câu hỏi này, hybrid + RRF **không cho thấy cải thiện** so với dense-only, và thua ở đúng một trường hợp có căn cứ (G07). Không đủ dữ liệu để kết luận dense-only tốt hơn nói chung — cỡ mẫu quá nhỏ và phần lớn khoảng cách đến từ một khiếm khuyết của metric chứ không phải của retrieval.

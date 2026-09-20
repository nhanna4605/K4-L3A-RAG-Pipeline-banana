"""Pha 2: sinh cau tra loi + cham 4 metric. Khong can bge-m3 nen nhe RAM.

context recall / precision : tinh xac dinh tu expected_context, khong goi LLM
faithfulness / answer relevance : Gemini lam judge, 1 request cho ca hai tieu chi
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "scratchpad"))
REPO = Path("D:/Moitruongaocuaclaude/Lab8/K4-L3A-2A202602770-LV3")
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO / ".env")

from rotation import Rotator  # noqa: E402
from src.task10_generation import SYSTEM_PROMPT, format_context, reorder_for_llm  # noqa: E402

IN = REPO / "group_project" / "evaluation" / "retrieval_ab.json"
OUT = REPO / "group_project" / "evaluation" / "eval_raw.json"
SHINGLE = 30
METRICS = ["faithfulness", "answer_relevance", "context_recall", "context_precision"]


def norm(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip().lower()


def shingles(text, size=SHINGLE):
    t = norm(text)
    return {t[i : i + size] for i in range(0, max(1, len(t) - size + 1), 5)}


def context_metrics(contexts, expected):
    """recall = co lay duoc ground truth khong; precision = Average Precision@k."""
    if not contexts:
        return 0.0, 0.0
    gt = shingles(expected)
    flags = [bool(shingles(c) & gt) for c in contexts]
    hits, precs = 0, []
    for i, flag in enumerate(flags, 1):
        if flag:
            hits += 1
            precs.append(hits / i)
    return (1.0 if any(flags) else 0.0), (sum(precs) / len(precs) if precs else 0.0)


JUDGE = """Bạn là giám khảo đánh giá hệ thống hỏi đáp. Chấm hai tiêu chí, mỗi tiêu chí từ 0.0 đến 1.0.

faithfulness: tỷ lệ khẳng định trong CÂU TRẢ LỜI được NGỮ CẢNH hỗ trợ trực tiếp.
  1.0 = mọi khẳng định đều có trong ngữ cảnh. 0.0 = bịa đặt.
  Nếu câu trả lời là lời từ chối vì thiếu dữ liệu thì chấm 1.0 (không bịa gì).

answer_relevance: mức độ câu trả lời giải quyết đúng CÂU HỎI.
  1.0 = trả lời trực tiếp và đầy đủ. 0.0 = lạc đề hoặc từ chối trả lời.

Chỉ trả JSON, không giải thích: {"faithfulness": <số>, "answer_relevance": <số>}"""


def judge(rot, question, answer, contexts):
    if not answer.strip():
        return {"faithfulness": None, "answer_relevance": None}
    payload = (f"NGỮ CẢNH:\n{chr(10).join(contexts)[:9000]}\n\n"
               f"CÂU HỎI: {question}\n\nCÂU TRẢ LỜI: {answer}")
    raw = rot.generate(JUDGE, payload, temperature=0.0)
    m = re.search(r"\{.*?\}", raw, re.DOTALL)
    if not m:
        return {"faithfulness": None, "answer_relevance": None}
    try:
        d = json.loads(m.group(0))
        return {"faithfulness": float(d["faithfulness"]),
                "answer_relevance": float(d["answer_relevance"])}
    except Exception:
        return {"faithfulness": None, "answer_relevance": None}


data = json.loads(IN.read_text(encoding="utf-8"))
rot = Rotator()
print(f"Capacity: {rot.capacity()}", flush=True)

result = {"top_k": data["top_k"], "score_threshold": data["score_threshold"],
          "n_cases": len(data["A"])}
stopped = None

for key, label in (("A", "dense-only"), ("B", "hybrid + RRF")):
    print(f"\n--- Config {key}: {label} ---", flush=True)
    rows = []
    for item in data[key]:
        recall, precision = context_metrics(item["contexts"], item["expected_context"])
        answer, scores = "", {"faithfulness": None, "answer_relevance": None}
        if item["contexts"] and stopped is None:
            chunks = [
                {"id": i, "content": c, "citation_index": n,
                 "metadata": {"title": t, "source": s}}
                for n, (i, c, t, s) in enumerate(
                    zip(item["ids"], item["contexts"], item["titles"], item["sources"]), 1)
            ]
            ctx = format_context(reorder_for_llm(chunks))
            try:
                answer = rot.generate(
                    SYSTEM_PROMPT, f"Context:\n{ctx}\n\nQuestion: {item['question']}")
                scores = judge(rot, item["question"], answer, item["contexts"])
            except RuntimeError as error:
                stopped = str(error)
                print(f"  DUNG: {error}", flush=True)

        rows.append({
            "id": item["id"], "question": item["question"], "answer": answer,
            "expected_source": item["expected_source"],
            "retrieved_sources": item["sources"], "top_score": item["scores"][0] if item["scores"] else 0.0,
            "context_recall": recall, "context_precision": precision, **scores,
        })
        f, r = scores["faithfulness"], scores["answer_relevance"]
        print(f"  {item['id']}  faith={'n/a' if f is None else f'{f:.2f}'}  "
              f"rel={'n/a' if r is None else f'{r:.2f}'}  "
              f"recall={recall:.0f}  prec={precision:.2f}  ({len(answer)} ky tu)", flush=True)

    def mean(m):
        v = [x[m] for x in rows if x.get(m) is not None]
        return sum(v) / len(v) if v else None

    result[key] = {"rows": rows, "overall": {m: mean(m) for m in METRICS}}

result["stopped"] = stopped
result["quota_used"] = rot.calls
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{'metric':<20}{'Config A':>12}{'Config B':>12}{'delta B-A':>12}")
print("-" * 56)
for m in METRICS:
    a, b = result["A"]["overall"][m], result["B"]["overall"][m]
    if a is None or b is None:
        print(f"{m:<20}{'n/a':>12}{'n/a':>12}{'n/a':>12}")
    else:
        print(f"{m:<20}{a:>12.4f}{b:>12.4f}{b - a:>+12.4f}")
print("\nQuota:")
print(rot.report())
print(f"\nDa luu {OUT}", flush=True)

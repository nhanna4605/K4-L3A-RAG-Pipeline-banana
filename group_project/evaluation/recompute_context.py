"""Tinh lai context recall / precision bang do phu, khong goi LLM.

Bug cu: shingle lay mau cach 5 ky tu nen hai doan chua cung mot cau nhung lech
offset thi tap shingle khong giao nhau -> recall bi bao sai la 0.

Cach dung: voi moi cua so 30 ky tu cua expected_context, kiem tra no co xuat hien
trong chunk khong (dung `in`, khong lay mau). Ty le cua so tim thay = do phu.
  - context recall    = do phu HOP NHAT cua ca top-k (ground truth co the bi
                        chunking cat doi nen phai gop lai)
  - context precision = Average Precision@k, chunk duoc coi la lien quan khi
                        do phu rieng cua no >= 0.3
"""

import json
import re
import unicodedata
from pathlib import Path

REPO = Path("D:/Moitruongaocuaclaude/Lab8/K4-L3A-2A202602770-LV3")
RETRIEVAL = REPO / "group_project" / "evaluation" / "retrieval_ab.json"
RAW = REPO / "group_project" / "evaluation" / "eval_raw.json"

WINDOW = 30
STEP = 10
RELEVANT_AT = 0.30
METRICS = ["faithfulness", "answer_relevance", "context_recall", "context_precision"]


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip().lower()


def windows(expected: str) -> list[str]:
    e = norm(expected)
    if len(e) <= WINDOW:
        return [e]
    return [e[i : i + WINDOW] for i in range(0, len(e) - WINDOW + 1, STEP)]


def coverage(chunk: str, wins: list[str]) -> float:
    c = norm(chunk)
    return sum(w in c for w in wins) / len(wins)


def union_coverage(chunks: list[str], wins: list[str]) -> float:
    """Ground truth co the bi cat doi giua hai chunk nen tinh hop nhat."""
    normed = [norm(c) for c in chunks]
    return sum(any(w in c for c in normed) for w in wins) / len(wins)


def context_metrics(chunks: list[str], expected: str) -> tuple[float, float]:
    if not chunks:
        return 0.0, 0.0
    wins = windows(expected)
    recall = union_coverage(chunks, wins)
    hits, precs = 0, []
    for i, chunk in enumerate(chunks, 1):
        if coverage(chunk, wins) >= RELEVANT_AT:
            hits += 1
            precs.append(hits / i)
    precision = sum(precs) / len(precs) if precs else 0.0
    return recall, precision


retrieval = json.loads(RETRIEVAL.read_text(encoding="utf-8"))
raw = json.loads(RAW.read_text(encoding="utf-8"))

for key in ("A", "B"):
    by_id = {x["id"]: x for x in retrieval[key]}
    for row in raw[key]["rows"]:
        item = by_id[row["id"]]
        recall, precision = context_metrics(item["contexts"], item["expected_context"])
        row["context_recall"] = round(recall, 4)
        row["context_precision"] = round(precision, 4)

    rows = raw[key]["rows"]
    raw[key]["overall"] = {
        m: (lambda v: sum(v) / len(v) if v else None)(
            [r[m] for r in rows if r.get(m) is not None]
        )
        for m in METRICS
    }

raw["context_metric_method"] = {
    "window_chars": WINDOW,
    "step_chars": STEP,
    "relevant_threshold": RELEVANT_AT,
    "recall": "do phu hop nhat cua top-k voi expected_context",
    "precision": "Average Precision@k, chunk lien quan khi do phu rieng >= 0.30",
}
RAW.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"{'metric':<20}{'Config A':>12}{'Config B':>12}{'delta B-A':>12}")
print("-" * 56)
for m in METRICS:
    a, b = raw["A"]["overall"][m], raw["B"]["overall"][m]
    print(f"{m:<20}{a:>12.4f}{b:>12.4f}{b - a:>+12.4f}")

print("\nChi tiet tung cau (recall / precision):")
print(f"{'ID':<6}{'A rec':>8}{'A prec':>9}{'B rec':>8}{'B prec':>9}   nguon mong doi")
amap = {r['id']: r for r in raw['A']['rows']}
bmap = {r['id']: r for r in raw['B']['rows']}
for cid in [r['id'] for r in raw['A']['rows']]:
    a, b = amap[cid], bmap[cid]
    print(f"{cid:<6}{a['context_recall']:>8.2f}{a['context_precision']:>9.2f}"
          f"{b['context_recall']:>8.2f}{b['context_precision']:>9.2f}   {a['expected_source'][:38]}")

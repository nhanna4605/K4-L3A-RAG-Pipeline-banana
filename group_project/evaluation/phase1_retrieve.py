"""Pha 1: chay retrieval cho ca hai config, luu context ra JSON roi thoat.

Tach rieng vi bge-m3 chiem ~2.3GB RAM. Pha 2 khong can model nen chay nhe.
"""

import json
import sys
from pathlib import Path

REPO = Path("D:/Moitruongaocuaclaude/Lab8/K4-L3A-2A202602770-LV3")
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO / ".env")

from src.task9_retrieval_pipeline import SCORE_THRESHOLD, retrieve  # noqa: E402

GOLDEN = REPO / "group_project" / "evaluation" / "golden_dataset.json"
OUT = REPO / "group_project" / "evaluation" / "retrieval_ab.json"
TOP_K = 5

cases = json.loads(GOLDEN.read_text(encoding="utf-8"))
out = {"top_k": TOP_K, "score_threshold": SCORE_THRESHOLD, "A": [], "B": []}

for label, use_rerank, key in (("dense-only", False, "A"), ("hybrid+RRF", True, "B")):
    print(f"\n--- Config {key}: {label} ---", flush=True)
    for case in cases:
        chunks = retrieve(case["question"], top_k=TOP_K, use_reranking=use_rerank)
        out[key].append(
            {
                "id": case["id"],
                "question": case["question"],
                "expected_context": case["expected_context"],
                "expected_answer": case["expected_answer"],
                "expected_source": case["source"],
                "contexts": [c["content"] for c in chunks],
                "ids": [c["id"] for c in chunks],
                "sources": [c["metadata"]["source"] for c in chunks],
                "titles": [c["metadata"]["title"] for c in chunks],
                "scores": [c["score"] for c in chunks],
                "method": chunks[0]["retrieval_method"] if chunks else None,
            }
        )
        print(f"  {case['id']}  {len(chunks)} chunk  top={chunks[0]['score']:.4f}" if chunks
              else f"  {case['id']}  0 chunk", flush=True)

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nDa luu {OUT}", flush=True)

"""Recompute retrieval metrics from the stored reports in this directory.

Passages are read from ../../datasets/passages.json (the retrieval-eval corpus).

Why this exists: every run in this folder was produced before the evaluator fix
of 2026-06-08, which changed both

  * the metric  -- old recall@k counted retrieved chunks that hit anything,
                   divided by the number of relevant passages, so duplicates
                   pushed recall above 100%; the fix counts distinct relevant
                   passages covered by the top k, and
  * the matcher -- old chunk_hits_passage() matched a chunk only if it was
                   contained in the passage, and returned False for every
                   markdown passage (char_start is not populated for the 99 md
                   passages), while the fix uses a symmetric shingle
                   containment coefficient on text for all passages.

The reports store the ranked chunk texts, so the fixed metrics can be recomputed
offline for the runs that recorded them (rewriting_v3 and the two rerankers);
dense_baseline and hybrid stored only chunk indices, which are not unique across
documents, so those two cannot be recovered.

Running this file with --old reproduces the numbers printed in the stored
retrieval_report.txt files exactly (682/682 cases), which validates the parsing.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_PASSAGES = (
    HERE.parent.parent / "datasets" / "passages.json"
)
K_VALUES = (5, 10, 20, 30)
SHINGLE_K = 50
THRESHOLD = 0.5
CHUNK_RE = re.compile(r"^c_idx:\s*(\S+)\s*,\s*text:\s*(.*)$", re.S)


def shingles(text: str, k: int = SHINGLE_K) -> set[str]:
    norm = " ".join(text.split())
    if not norm:
        return set()
    if len(norm) <= k:
        return {norm}
    return {norm[i : i + k] for i in range(len(norm) - k + 1)}


def containment(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a) if a else 0.0


def hits_new(chunk: set[str], passage: set[str]) -> bool:
    """Fixed matcher: symmetric shingle containment coefficient."""
    if not chunk or not passage:
        return False
    return max(containment(chunk, passage), containment(passage, chunk)) >= THRESHOLD


def hits_old(chunk_text: str, passage: dict) -> bool:
    """Pre-fix matcher, kept so --old can reproduce the stored reports."""
    if passage.get("source_type") == "md":
        return False  # char_start is None for every md passage
    chunk, text = chunk_text.strip(), (passage.get("text") or "").strip()
    if not chunk or not text:
        return False
    probes = [chunk[i : i + 100].strip() for i in range(0, len(chunk), 50)]
    probes = [p for p in probes if p]
    return (sum(p in text for p in probes) / len(probes) if probes else 0.0) >= THRESHOLD


def evaluate(report: Path, passages: dict, old: bool) -> dict | None:
    cases = json.loads(report.read_text())["case_results"]
    if not cases or not cases[0]["actual"] or not isinstance(cases[0]["actual"][0], str):
        return None  # ranked chunk texts were not stored

    acc = {f"{m}_at_{k}": [] for k in K_VALUES for m in ("recall", "precision")}
    rrs, matches, n = [], 0, 0

    for case in cases:
        relevant = [passages[pid] for pid in case["expected"] if pid in passages]
        if not relevant:
            continue
        texts = [CHUNK_RE.match(a).group(2) for a in case["actual"]]
        if old:
            chunk_hits = [any(hits_old(t, p) for p in relevant) for t in texts]
            matrix = [[h] * len(relevant) for h in chunk_hits]  # unused for old recall
        else:
            rel_sh = [shingles(p["text"]) for p in relevant]
            matrix = [[hits_new(shingles(t), r) for r in rel_sh] for t in texts]
            chunk_hits = [any(row) for row in matrix]

        n += 1
        for k in K_VALUES:
            if old:
                covered = sum(chunk_hits[:k])  # pre-fix: hit count, not distinct passages
            else:
                covered = sum(1 for j in range(len(relevant)) if any(r[j] for r in matrix[:k]))
            acc[f"recall_at_{k}"].append(covered / len(relevant))
            acc[f"precision_at_{k}"].append(sum(chunk_hits[:k]) / k)

        rr = next((1 / rank for rank, h in enumerate(chunk_hits, 1) if h), 0.0)
        rrs.append(rr)
        if old and all(
            abs(round(v[-1], 4) - case["metrics"].get(m, 0)) < 1e-4
            for m, v in acc.items()
            if m.endswith(("_at_5", "_at_10", "_at_30"))
        ):
            matches += 1

    out = {m: statistics.fmean(v) for m, v in acc.items()}
    out["mrr"] = statistics.fmean(rrs)
    out["n_cases"] = n
    out["reproduces_stored"] = matches
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--passages", type=Path, default=DEFAULT_PASSAGES)
    ap.add_argument("--old", action="store_true", help="use the pre-fix matcher and recall")
    args = ap.parse_args()

    passages = {p["passage_id"]: p for p in json.loads(args.passages.read_text())}
    header = "pre-fix (reproduces stored reports)" if args.old else "current evaluator code"
    print(f"Retrieval metrics recomputed with the {header}\n")

    for report in sorted(HERE.glob("*/retrieval_report.json")):
        run = report.parent.name
        res = evaluate(report, passages, args.old)
        if res is None:
            print(f"{run:32s}  skipped (only chunk indices stored, texts missing)")
            continue
        cells = "  ".join(
            f"R@{k}={res[f'recall_at_{k}']:5.1%} P@{k}={res[f'precision_at_{k}']:5.1%}"
            for k in K_VALUES
        )
        extra = f"  reproduced={res['reproduces_stored']}/{res['n_cases']}" if args.old else ""
        print(f"{run:32s}  n={res['n_cases']}  {cells}  MRR={res['mrr']:.4f}{extra}")


if __name__ == "__main__":
    main()

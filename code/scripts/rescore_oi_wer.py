"""Re-score cached EXP-A baseline results with project OI-WER (see code/metrics/oi_wer.py).

Reads the cached per-sample baseline results + manifest (for reference_variants),
does not call the model, writes an oi_-prefixed summary next to the original.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from metrics.oi_wer import oi_wer


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-results", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    results = load_jsonl(args.baseline_results)
    manifest_by_id = {row["sample_id"]: row for row in load_jsonl(args.manifest)}

    rows = []
    for row in results:
        sample_id = row["sample_id"]
        manifest_row = manifest_by_id.get(sample_id, {})
        variants = manifest_row.get("reference_variants") or []
        hypothesis = row.get("explicit", {}).get("transcript", "")
        reference = row.get("reference", "")
        whitespace_wer = row.get("wer")  # may be absent; recomputed below if needed
        score = oi_wer(reference, hypothesis, reference_variants=variants)
        rows.append(
            {
                "sample_id": sample_id,
                "language": row["language"],
                "condition": row.get("conditions", {}).get("audio", row.get("condition")),
                "oi_wer": score,
                "used_variant": len(variants) > 0,
            }
        )

    by_language: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        lang = row["language"]
        key = lang[0] if isinstance(lang, list) else lang
        by_language[key].append(row["oi_wer"])

    summary = {
        "sample_count": len(rows),
        "metric": "project_oi_wer (normalization-tolerant, multi-reference; NOT the vendor's OI-WER definition)",
        "mean_oi_wer": sum(row["oi_wer"] for row in rows) / max(len(rows), 1),
        "mean_oi_wer_by_language": {lang: sum(values) / len(values) for lang, values in sorted(by_language.items())},
        "rows_with_variant_used": sum(row["used_variant"] for row in rows),
        "note": (
            "Computed by code/metrics/oi_wer.py against cached EXP-A explicit-language "
            "transcripts. Multi-reference scoring only helps where reference_variants "
            "differ meaningfully after normalization; most current variants are "
            "punctuated restatements of the primary reference (see REPORT.md Sec 5.7)."
        ),
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

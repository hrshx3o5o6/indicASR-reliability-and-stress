"""Compute small-sample EXP-A transcript and LID summaries."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


def tokens(text: str) -> list[str]:
    return re.findall(r"\S+", text.strip())


def edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for ref_index, ref_token in enumerate(reference, 1):
        current = [ref_index]
        for hyp_index, hyp_token in enumerate(hypothesis, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[hyp_index] + 1,
                    previous[hyp_index - 1] + (ref_token != hyp_token),
                )
            )
        previous = current
    return previous[-1]


def sample_metrics(row: dict) -> dict:
    reference = tokens(row.get("reference", ""))
    hypothesis = tokens(row.get("explicit", {}).get("transcript", ""))
    lid = row.get("auto", {}).get("lid", {})
    lid_language = lid.get("lang") if isinstance(lid, dict) else None
    explicit_lid = row.get("explicit", {}).get("lid", {})
    explicit_language = explicit_lid.get("lang") if isinstance(explicit_lid, dict) else None
    return {
        "id": row["id"],
        "language": row["language"],
        "status": row["status"],
        "wer": edit_distance(reference, hypothesis) / max(len(reference), 1),
        "reference_words": len(reference),
        "hypothesis_words": len(hypothesis),
        "exact_match": " ".join(reference) == " ".join(hypothesis),
        "auto_lid": lid_language,
        "explicit_lid": explicit_language,
        "auto_lid_correct": lid_language == row["language"],
        "explicit_auto_lid_agree": lid_language == explicit_language,
        "warnings": len(row.get("warnings", [])),
        "duration_seconds": row.get("duration_seconds"),
    }


def summarize(rows: list[dict]) -> dict:
    by_language = defaultdict(list)
    for row in rows:
        by_language[row["language"]].append(row)
    summary = {
        "sample_count": len(rows),
        "successful_count": sum(row["status"] == "ok" for row in rows),
        "mean_wer": sum(row["wer"] for row in rows) / max(len(rows), 1),
        "exact_match_rate": sum(row["exact_match"] for row in rows) / max(len(rows), 1),
        "auto_lid_accuracy": sum(row["auto_lid_correct"] for row in rows) / max(len(rows), 1),
        "explicit_auto_lid_agreement": sum(row["explicit_auto_lid_agree"] for row in rows)
        / max(len(rows), 1),
        "warning_sample_rate": sum(row["warnings"] > 0 for row in rows) / max(len(rows), 1),
        "by_language": {},
    }
    for language, language_rows in sorted(by_language.items()):
        summary["by_language"][language] = {
            "sample_count": len(language_rows),
            "mean_wer": sum(row["wer"] for row in language_rows) / len(language_rows),
            "exact_match_rate": sum(row["exact_match"] for row in language_rows)
            / len(language_rows),
            "auto_lid_accuracy": sum(row["auto_lid_correct"] for row in language_rows)
            / len(language_rows),
            "explicit_auto_lid_agreement": sum(row["explicit_auto_lid_agree"] for row in language_rows)
            / len(language_rows),
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw_rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines()]
    sample_rows = [sample_metrics(row) for row in raw_rows]
    result = {"summary": summarize(sample_rows), "samples": sample_rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Create conservative EXP-D annotation candidates from reference text."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = []
    for line in args.manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        sample = json.loads(line)
        reference = sample.get("reference", "")
        explicit_numbers = [
            {"surface": value, "value": int(value.replace(",", "").replace("،", "")), "type": "number"}
            for value in re.findall(r"(?<!\w)\d[\d,،]*(?!\w)", reference)
        ]
        latin_candidates = [
            {"surface": value.strip(), "type": "entity", "review_required": True}
            for value in re.findall(r"\b[A-Za-z][A-Za-z.-]*(?:\s+[A-Za-z][A-Za-z.-]*)*\b", reference)
        ]
        output.append(
            {
                "sample_id": sample["sample_id"],
                "language": sample["language"],
                "reference": reference,
                "verified_slots": {"numbers": explicit_numbers, "dates": [], "currency": []},
                "entity_candidates": latin_candidates,
                "annotation_status": "machine_candidate_manual_review_required",
                "annotation_note": "Only explicit Arabic-digit numbers are scored automatically; spoken numbers and entities require human review.",
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in output) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"sample_count": len(output), "explicit_number_rows": sum(bool(row["verified_slots"]["numbers"]) for row in output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

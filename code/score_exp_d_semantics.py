"""Score conservative explicit-number slots for EXP-D outputs."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path


def number_values(text: str) -> set[int]:
    return {int(value.replace(",", "").replace("،", "")) for value in re.findall(r"(?<!\w)\d[\d,،]*(?!\w)", text)}


def normalized_surface(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)


def number_surface_recall(numbers: list[dict], text: str) -> float:
    normalized_text = normalized_surface(text)
    digit_values = number_values(text)
    hits = 0
    for item in numbers:
        surface = normalized_surface(item["surface"])
        value = item.get("normalized_value", item.get("value"))
        if (surface and surface in normalized_text) or value in digit_values:
            hits += 1
    return hits / max(len(numbers), 1)


def item_surface_recall(items: list[dict], text: str, alternate_key: str = "canonical") -> float:
    normalized_text = normalized_surface(text)
    hits = 0
    for item in items:
        surface = normalized_surface(item.get("surface", ""))
        alternate = normalized_surface(str(item.get(alternate_key, "")))
        if (surface and surface in normalized_text) or (alternate and alternate in normalized_text):
            hits += 1
    return hits / max(len(items), 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    annotations = {}
    for line in args.annotations.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            annotations[row["sample_id"]] = row
    scored = []
    for line in args.results.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        annotation = annotations[row["sample_id"]]
        expected_items = annotation["verified_slots"]["numbers"]
        expected_dates = annotation["verified_slots"].get("dates", [])
        expected_currency = annotation["verified_slots"].get("currency", [])
        expected_entities = annotation.get("verified_entities", [])
        expected = {item.get("normalized_value", item.get("value")) for item in expected_items}
        if not (expected_items or expected_dates or expected_currency or expected_entities):
            continue
        candidates = {
            "core_native": number_values(row["core_native"]),
            "flex_native": number_values(row["flex_native"]),
            "flex_mixed": number_values(row["flex_mixed"]),
        }
        scored.append(
            {
                "sample_id": row["sample_id"],
                "has_numbers": bool(expected_items),
                "has_dates": bool(expected_dates),
                "has_currency": bool(expected_currency),
                "has_entities": bool(expected_entities),
                "expected_numbers": sorted(expected),
                "found_numbers": {name: sorted(values) for name, values in candidates.items()},
                "slot_recall": {name: len(expected & values) / max(len(expected), 1) for name, values in candidates.items()},
                "surface_recall": {
                    name: number_surface_recall(expected_items, row[transcript_field])
                    for name, transcript_field in {
                        "core_native": "core_native",
                        "flex_native": "flex_native",
                        "flex_mixed": "flex_mixed",
                    }.items()
                },
                "date_recall": {
                    name: item_surface_recall(expected_dates, row[transcript_field], "normalized_value")
                    for name, transcript_field in {
                        "core_native": "core_native",
                        "flex_native": "flex_native",
                        "flex_mixed": "flex_mixed",
                    }.items()
                },
                "currency_recall": {
                    name: item_surface_recall(expected_currency, row[transcript_field], "currency")
                    for name, transcript_field in {
                        "core_native": "core_native",
                        "flex_native": "flex_native",
                        "flex_mixed": "flex_mixed",
                    }.items()
                },
                "entity_recall": {
                    name: item_surface_recall(expected_entities, row[transcript_field])
                    for name, transcript_field in {
                        "core_native": "core_native",
                        "flex_native": "flex_native",
                        "flex_mixed": "flex_mixed",
                    }.items()
                },
            }
        )
    summary = {
        "annotated_rows_scored": len(scored),
        "annotation_scope": "curated number, date, currency, and entity slots scored by conservative exact-surface matching",
        "mean_slot_recall": {
            name: sum(row["slot_recall"][name] for row in scored if row["has_numbers"])
            / max(sum(row["has_numbers"] for row in scored), 1)
            for name in ("core_native", "flex_native", "flex_mixed")
        },
        "mean_surface_recall": {
            name: sum(row["surface_recall"][name] for row in scored if row["has_numbers"])
            / max(sum(row["has_numbers"] for row in scored), 1)
            for name in ("core_native", "flex_native", "flex_mixed")
        },
        "mean_date_recall": {
            name: sum(row["date_recall"][name] for row in scored if row["has_dates"])
            / max(sum(row["has_dates"] for row in scored), 1)
            for name in ("core_native", "flex_native", "flex_mixed")
        },
        "mean_currency_recall": {
            name: sum(row["currency_recall"][name] for row in scored if row["has_currency"])
            / max(sum(row["has_currency"] for row in scored), 1)
            for name in ("core_native", "flex_native", "flex_mixed")
        },
        "mean_entity_recall": {
            name: sum(row["entity_recall"][name] for row in scored if row["has_entities"])
            / max(sum(row["has_entities"] for row in scored), 1)
            for name in ("core_native", "flex_native", "flex_mixed")
        },
        "warning": "Surface recall accepts exact spoken phrases or digit values; it is not a full semantic evaluation and does not handle transliteration or compositional number variants.",
        "rows": scored,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "rows"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

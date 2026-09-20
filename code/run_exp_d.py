"""Compare Core native output with Flex native and mixed-mode output."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any


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


def wer(reference: str, hypothesis: str) -> float:
    return edit_distance(tokens(reference), tokens(hypothesis)) / max(len(tokens(reference)), 1)


def latin_token_count(text: str) -> int:
    return sum(any("LATIN" in unicodedata_name(char, "") for char in token) for token in tokens(text))


def unicodedata_name(char: str, default: str) -> str:
    import unicodedata

    return unicodedata.name(char, default)


def number_like_count(text: str) -> int:
    return sum(bool(re.search(r"\d", token)) for token in tokens(text))


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--core-results", type=Path, required=True)
    parser.add_argument("--flex-model-dir", type=Path, required=True)
    parser.add_argument("--audio-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--max-new-tokens", type=int, default=128)
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parent / "vendored" / "core"))
    from indic_transcribe import IndicTranscribe

    manifest = load_rows(args.manifest)
    core_rows = {row.get("sample_id", row.get("id")): row for row in load_rows(args.core_results)}
    asr = IndicTranscribe.from_pretrained(str(args.flex_model_dir), device=args.device)
    output_path = args.output_dir / "exp-d-flex-results.jsonl"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text("", encoding="utf-8")
    started = time.perf_counter()

    for index, sample in enumerate(manifest, 1):
        sample_id = sample["sample_id"]
        audio_path = Path(sample["audio"]["path"])
        if not audio_path.is_absolute():
            audio_path = args.audio_root / audio_path
        record = {
            "sample_id": sample_id,
            "language": sample["language"],
            "conditions": sample.get("conditions", {}),
            "reference": sample.get("reference", ""),
        }
        try:
            native, native_lid = asr.transcribe(
                str(audio_path),
                lang=sample["language"],
                mode="native",
                return_lid=True,
                max_new_tokens=args.max_new_tokens,
            )
            mixed, mixed_lid = asr.transcribe(
                str(audio_path),
                lang=sample["language"],
                mode="mixed",
                return_lid=True,
                max_new_tokens=args.max_new_tokens,
            )
            core = core_rows.get(sample_id, {})
            core_native = core.get("explicit", {}).get("transcript", "")
            record.update(
                {
                    "status": "ok",
                    "core_native": core_native,
                    "flex_native": native,
                    "flex_mixed": mixed,
                    "flex_native_lid": native_lid,
                    "flex_mixed_lid": mixed_lid,
                    "wer_core_native": wer(record["reference"], core_native),
                    "wer_flex_native": wer(record["reference"], native),
                    "wer_flex_mixed": wer(record["reference"], mixed),
                    "mixed_number_like_tokens": number_like_count(mixed),
                    "mixed_latin_tokens": latin_token_count(mixed),
                }
            )
        except Exception as error:
            record.update({"status": "error", "error": {"type": type(error).__name__, "message": str(error)}})
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"[{index}/{len(manifest)}] {sample_id}: {record['status']}", flush=True)

    rows = [row for row in load_rows(output_path) if row["status"] == "ok"]
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        conditions = row.get("conditions", {}).get("audio", ["unknown"])
        by_condition[conditions[0] if conditions else "unknown"].append(row)
    average = lambda items, key: sum(item[key] for item in items) / max(len(items), 1)
    summary = {
        "sample_count": len(load_rows(output_path)),
        "successful_count": len(rows),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "mean_wer": {
            "core_native": average(rows, "wer_core_native"),
            "flex_native": average(rows, "wer_flex_native"),
            "flex_mixed": average(rows, "wer_flex_mixed"),
        },
        "by_condition": {
            condition: {
                "sample_count": len(items),
                "core_native": average(items, "wer_core_native"),
                "flex_native": average(items, "wer_flex_native"),
                "flex_mixed": average(items, "wer_flex_mixed"),
            }
            for condition, items in sorted(by_condition.items())
        },
        "semantic_annotation_status": "missing; semantic-slot and entity scores not computed",
    }
    (args.output_dir / "exp-d-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

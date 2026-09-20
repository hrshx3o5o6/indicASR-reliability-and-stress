"""Run the EXP-A Core baseline over a JSONL challenge manifest."""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ("id", "audio_path", "language")


def _normalize_sample(sample: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(sample)
    normalized.setdefault("id", normalized.get("sample_id"))

    audio = normalized.get("audio")
    if isinstance(audio, dict):
        normalized["audio_path"] = audio.get("path")
    else:
        normalized["audio_path"] = audio

    conditions = normalized.get("conditions")
    if isinstance(conditions, dict):
        normalized["condition"] = list(conditions.get("audio", []))
        normalized["condition"].extend(conditions.get("content", []))
    else:
        normalized.setdefault("condition", [])
    return normalized


def load_manifest(path: Path) -> list[dict[str, Any]]:
    """Load and validate one JSON object per non-blank line."""
    samples = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            sample = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {error.msg}") from error
        if not isinstance(sample, dict):
            raise ValueError(f"{path}:{line_number}: sample must be a JSON object")
        sample = _normalize_sample(sample)
        missing = [field for field in REQUIRED_FIELDS if not sample.get(field)]
        if missing:
            raise ValueError(
                f"{path}:{line_number}: missing required field(s): {', '.join(missing)}"
            )
        samples.append(sample)
    if not samples:
        raise ValueError(f"{path}: manifest has no samples")
    return samples


def json_safe_lid(value: Any) -> Any:
    """Convert tuple-based LID output into JSON-compatible arrays."""
    if isinstance(value, (tuple, list)):
        return [json_safe_lid(item) for item in value]
    if isinstance(value, dict):
        return {key: json_safe_lid(item) for key, item in value.items()}
    return value


def write_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_asr(model_dir: Path, device: str):
    sys.path.insert(0, str(Path(__file__).parent / "vendored" / "core"))
    from indic_transcribe import IndicTranscribe

    return IndicTranscribe.from_pretrained(str(model_dir), device=device)


def _run_sample(asr: Any, sample: dict[str, Any], audio_root: Path, max_new_tokens: int):
    started = time.perf_counter()
    audio_path = Path(sample["audio_path"])
    if not audio_path.is_absolute():
        audio_path = audio_root / audio_path

    record: dict[str, Any] = {
        "schema_version": "exp-a.v0",
        "id": sample["id"],
        "audio": sample.get("audio", sample["audio_path"]),
        "language": sample["language"],
        "condition": sample.get("condition", []),
    }
    if "sample_id" in sample:
        record["sample_id"] = sample["sample_id"]
    if "conditions" in sample:
        record["conditions"] = sample["conditions"]
    if "provenance" in sample:
        record["provenance"] = sample["provenance"]
    for field in ("reference", "entities", "numbers", "dates", "currency", "speaker_id"):
        if field in sample:
            record[field] = sample[field]

    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            explicit_text, explicit_lid = asr.transcribe(
                str(audio_path),
                lang=sample["language"],
                return_lid=True,
                max_new_tokens=max_new_tokens,
            )
            auto_text, auto_lid = asr.transcribe(
                str(audio_path),
                return_lid=True,
                max_new_tokens=max_new_tokens,
            )
            identify = asr.identify(str(audio_path))

        record.update(
            {
                "status": "ok",
                "explicit": {
                    "transcript": explicit_text,
                    "lid": json_safe_lid(explicit_lid),
                },
                "auto": {
                    "transcript": auto_text,
                    "lid": json_safe_lid(auto_lid),
                },
                "identify": json_safe_lid(identify),
                "warnings": [str(item.message) for item in captured],
            }
        )
    except Exception as error:  # keep the failed sample in the run artifact
        record.update(
            {
                "status": "error",
                "error": {"type": type(error).__name__, "message": str(error)},
            }
        )
    record["duration_seconds"] = round(time.perf_counter() - started, 3)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, default=Path("data/model"))
    parser.add_argument("--output", type=Path, default=Path("results/exp-a/results.jsonl"))
    parser.add_argument("--audio-root", type=Path, default=Path.cwd())
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()

    samples = load_manifest(args.manifest)
    asr = _load_asr(args.model_dir, args.device)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("", encoding="utf-8")
    for index, sample in enumerate(samples, 1):
        record = _run_sample(asr, sample, args.audio_root, args.max_new_tokens)
        write_record(args.output, record)
        print(f"[{index}/{len(samples)}] {sample['id']}: {record['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Materialize small Bhojpuri and Maithili slices from parquet audio rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow.parquet as parquet
import soundfile


SOURCES = {
    "bho": {
        "filename": "bhojpuri-benchmark.parquet",
        "audio_column": "audio",
        "text_column": "text",
        "variant_column": None,
        "source": "rural-women-bhojpuri",
        "license": "CC-BY-SA-4.0",
    },
    "mai": {
        "filename": "maithili-train-00000.parquet",
        "audio_column": "audio_filepath",
        "text_column": "text",
        "variant_column": "normalized",
        "source": "indicvoices",
        "license": "CC-BY-4.0",
    },
}


def materialize(raw_dir: Path, output_root: Path, samples_per_language: int) -> Path:
    manifest_path = output_root / "manifests" / "exp-a-regional-seed.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for language, source in SOURCES.items():
        shard = raw_dir / source["filename"]
        parquet_file = parquet.ParquetFile(shard)
        selected = 0
        for batch in parquet_file.iter_batches(batch_size=32):
            for row in batch.to_pylist():
                audio = row[source["audio_column"]]
                audio_bytes = audio["bytes"]
                if not audio_bytes:
                    continue
                sample_id = f"regional-{language}-{selected + 1:03d}"
                suffix = Path(audio["path"] or "audio.wav").suffix or ".audio"
                relative_audio = Path("audio") / "regional" / language / f"{sample_id}{suffix}"
                audio_path = output_root / relative_audio
                audio_path.parent.mkdir(parents=True, exist_ok=True)
                audio_path.write_bytes(audio_bytes)
                info = soundfile.info(str(audio_path))
                reference = row[source["text_column"]]
                variant_column = source["variant_column"]
                variant = row[variant_column] if variant_column else None
                speaker_id = row.get("speaker_id") or "unknown"
                if speaker_id == "None":
                    speaker_id = "unknown"
                records.append(
                    {
                        "sample_id": sample_id,
                        "suite_version": "0.1",
                        "audio": {
                            "path": relative_audio.as_posix(),
                            "sr_hz": info.samplerate,
                            "channels": info.channels,
                            "duration_s": round(info.duration, 3),
                        },
                        "language": language,
                        "conditions": {
                            "audio": ["clean"],
                            "content": ["normal"],
                            "pair_id": None,
                            "degradation_chain": None,
                            "clean_twin": None,
                        },
                        "provenance": {
                            "source": source["source"],
                            "source_id": audio.get("path") or sample_id,
                            "synthetic": False,
                            "contamination_risk": "unknown",
                            "speaker_id": speaker_id,
                            "license": source["license"],
                            "recorded_env": row.get("area") or row.get("scenario") or "unknown",
                        },
                        "reference": reference,
                        "reference_variants": [variant] if variant and variant != reference else [],
                        "entities": [],
                        "numbers": [],
                        "dates": [],
                        "currency": [],
                        "notes": "Regional seed materialization; entity/value annotations pending.",
                    }
                )
                selected += 1
                if selected >= samples_per_language:
                    break
            if selected >= samples_per_language:
                break
    with manifest_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"wrote {len(records)} samples to {manifest_path}")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--samples-per-language", type=int, default=2)
    args = parser.parse_args()
    materialize(args.raw_dir, args.output_root, args.samples_per_language)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Extract a small canonical EXP-A seed from FLEURS parquet shards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow.parquet as parquet
import soundfile
from pyarrow.lib import ArrowInvalid


CONFIG_TO_LANGUAGE = {
    "hi_in": "hi",
    "ta_in": "ta",
    "te_in": "te",
    "ml_in": "ml",
    "kn_in": "kn",
    "ur_pk": "ur",
}


def materialize(raw_dir: Path, output_root: Path, samples_per_language: int) -> Path:
    audio_root = output_root / "audio" / "fleurs"
    manifest_path = output_root / "manifests" / "exp-a-fleurs-seed.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    for config, language in CONFIG_TO_LANGUAGE.items():
        shard = raw_dir / f"{config}-validation.parquet"
        if not shard.exists():
            continue
        try:
            parquet_file = parquet.ParquetFile(shard)
        except ArrowInvalid:
            print(f"skipping incomplete shard {shard}")
            continue
        selected = 0
        for batch in parquet_file.iter_batches(
            columns=["id", "audio", "transcription", "raw_transcription"],
            batch_size=32,
        ):
            for row in batch.to_pylist():
                audio = row["audio"]
                audio_bytes = audio["bytes"]
                if not audio_bytes:
                    continue
                sample_id = f"fleurs-{language}-{row['id']}"
                relative_audio = Path("audio") / "fleurs" / config / f"{sample_id}.wav"
                audio_path = output_root / relative_audio
                audio_path.parent.mkdir(parents=True, exist_ok=True)
                audio_path.write_bytes(audio_bytes)
                audio_info = soundfile.info(str(audio_path))
                duration_s = round(audio_info.duration, 3)
                channels = audio_info.channels
                sample_rate = audio_info.samplerate
                reference = row["transcription"]
                raw_reference = row["raw_transcription"]
                record = {
                    "sample_id": sample_id,
                    "suite_version": "0.1",
                    "audio": {
                        "path": relative_audio.as_posix(),
                        "sr_hz": sample_rate,
                        "channels": channels,
                        "duration_s": duration_s,
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
                        "source": "fleurs",
                        "source_id": f"{config}:{row['id']}",
                        "synthetic": False,
                        "contamination_risk": "unknown",
                        "speaker_id": "unknown",
                        "license": "CC-BY-4.0",
                        "recorded_env": "studio/read",
                    },
                    "reference": reference,
                    "reference_variants": [raw_reference] if raw_reference != reference else [],
                    "entities": [],
                    "numbers": [],
                    "dates": [],
                    "currency": [],
                    "notes": "FLEURS materialization; source row exposes no speaker_id",
                }
                records.append(record)
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

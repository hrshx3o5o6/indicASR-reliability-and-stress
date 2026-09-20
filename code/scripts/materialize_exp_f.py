"""Materialize EXP-F real-noise manifest from local IndicVoices parquet shards.

Real-world data has no synthetic "noise/telephone" condition labels, so this
uses IndicVoices' own `scenario` field as the real-condition proxy:
  - Conversation / Extempore -> spontaneous, naturally noisy/crowdsourced field
    recordings ("real-noise" condition per EXP-F-real-noise.md's design).
  - Read -> closer to clean/studio anchor.
No synthetic degradation is applied to either -- both are real recordings.
"""

from __future__ import annotations

import argparse
import io
import json
import random
from pathlib import Path

import pyarrow.parquet as pq
import soundfile as sf


NOISY_SCENARIOS = {"Conversation", "Extempore"}
CLEAN_SCENARIOS = {"Read"}
MAX_SECONDS = 30.0
SEED = 20260920


def normalize_lang(code: str) -> str:
    # IndicVoices uses ISO codes matching our project convention already.
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shards", type=Path, nargs="+", required=True, help="local parquet shard paths")
    parser.add_argument("--per-language-per-condition", type=int, default=4)
    parser.add_argument("--audio-out", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path, required=True)
    args = parser.parse_args()

    rng = random.Random(SEED)
    rows_out = []
    args.audio_out.mkdir(parents=True, exist_ok=True)

    for shard_path in args.shards:
        table = pq.read_table(
            shard_path,
            columns=["audio_filepath", "normalized", "duration", "lang", "scenario", "speaker_id"],
        )
        rows = table.to_pylist()
        language = normalize_lang(rows[0]["lang"]) if rows else shard_path.stem.split("-")[0]

        for condition_name, scenario_set in (("real_noise", NOISY_SCENARIOS), ("real_clean", CLEAN_SCENARIOS)):
            candidates = [
                r for r in rows
                if r["scenario"] in scenario_set
                and r["duration"] <= MAX_SECONDS
                and r["normalized"] and r["normalized"].strip()
            ]
            rng.shuffle(candidates)
            picked = candidates[: args.per_language_per_condition]
            for index, row in enumerate(picked):
                sample_id = f"indicvoices-{language}-{condition_name}-{index:02d}"
                wav_path = args.audio_out / language / f"{sample_id}.wav"
                wav_path.parent.mkdir(parents=True, exist_ok=True)
                audio, sample_rate = sf.read(io.BytesIO(row["audio_filepath"]["bytes"]), dtype="float32")
                sf.write(wav_path, audio, sample_rate, subtype="PCM_16")
                rows_out.append(
                    {
                        "sample_id": sample_id,
                        "language": language,
                        "conditions": {"audio": [condition_name], "content": ["normal"]},
                        "reference": row["normalized"],
                        "audio": {"path": str(wav_path.relative_to(args.audio_out.parent.parent))},
                        "duration_seconds": row["duration"],
                        "provenance": {
                            "source": "ai4bharat/IndicVoices",
                            "scenario": row["scenario"],
                            "speaker_id": row["speaker_id"],
                        },
                    }
                )
        print(f"{language}: picked {len([r for r in rows_out if r['language'] == language])} rows")

    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows_out) + "\n", encoding="utf-8"
    )
    print(f"TOTAL {len(rows_out)} rows -> {args.manifest_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build the 80-sample EXP-A v1 stratified manifest."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfiltfilt


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def relative_audio(record: dict, root: Path) -> Path:
    path = Path(record["audio"]["path"])
    return path if path.is_absolute() else root / path


def base_variant(record: dict, root: Path, output_root: Path, condition: str, index: int) -> dict:
    source_path = relative_audio(record, root)
    samples, sample_rate = sf.read(source_path, dtype="float32", always_2d=False)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    if sample_rate != 16000:
        samples = resample_poly(samples, 16000, sample_rate)
        sample_rate = 16000
    if condition == "background_noise":
        rng = np.random.default_rng(1000 + index)
        signal_rms = float(np.sqrt(np.mean(samples * samples)))
        noise_rms = max(signal_rms / (10 ** (10 / 20)), 1e-5)
        samples = samples + rng.normal(0.0, noise_rms, size=len(samples)).astype("float32")
        chain = "resample 16000hz + deterministic white noise snr=10db"
    else:
        sos = butter(4, [300, 3400], btype="bandpass", fs=16000, output="sos")
        samples = sosfiltfilt(sos, samples).astype("float32")
        chain = "resample 16000hz + butterworth bandpass 300-3400hz"
    peak = float(np.max(np.abs(samples))) if len(samples) else 0.0
    if peak > 0.99:
        samples = samples * (0.99 / peak)
    sample_id = f"{record['sample_id']}-{condition}"
    relative_path = Path("audio") / "exp-a-v1" / condition / f"{sample_id}.wav"
    output_path = output_root / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, samples, sample_rate, subtype="PCM_16")
    info = sf.info(output_path)
    variant = json.loads(json.dumps(record))
    variant["sample_id"] = sample_id
    variant["audio"] = {
        "path": relative_path.as_posix(),
        "sr_hz": info.samplerate,
        "channels": info.channels,
        "duration_s": round(info.duration, 3),
    }
    variant["conditions"] = {
        "audio": [condition],
        "content": list(record["conditions"].get("content", ["normal"])),
        "pair_id": record["sample_id"],
        "degradation_chain": chain,
        "clean_twin": record["sample_id"],
    }
    variant["provenance"]["synthetic"] = True
    variant["provenance"]["source_id"] = f"{record['provenance']['source_id']}::{condition}"
    variant["notes"] = "Deterministic paired degradation generated for EXP-A v1."
    return variant


def build(clean_records: list[dict], root: Path, output_root: Path) -> list[dict]:
    by_language: dict[str, list[dict]] = defaultdict(list)
    for record in clean_records:
        by_language[record["language"]].append(record)
    if set(by_language) != {"hi", "ta", "te", "ml", "kn", "ur", "bho", "mai"}:
        raise ValueError(f"expected 8 languages, got {sorted(by_language)}")
    if any(len(records) != 4 for records in by_language.values()):
        raise ValueError({language: len(records) for language, records in by_language.items()})
    output = []
    variant_index = 0
    for language in sorted(by_language):
        records = by_language[language]
        output.extend(records)
        for condition in ("background_noise", "telephone"):
            for record in records[:3]:
                variant_index += 1
                output.append(base_variant(record, root, output_root, condition, variant_index))
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-manifest", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = build(load_records(args.clean_manifest), args.root, args.output_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(records)} samples to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

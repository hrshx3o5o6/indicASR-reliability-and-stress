"""Run a CPU-feasible real-data EXP-E diarization pilot."""

from __future__ import annotations

import argparse
import io
import json
import math
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import soundfile as sf
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans


def tokens(text: str) -> list[str]:
    return text.split()


def edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for i, ref_token in enumerate(reference, 1):
        current = [i]
        for j, hyp_token in enumerate(hypothesis, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (ref_token != hyp_token)))
        previous = current
    return previous[-1]


def wer(reference: str, hypothesis: str) -> float:
    return edit_distance(tokens(reference), tokens(hypothesis)) / max(len(tokens(reference)), 1)


def read_audio(audio: dict) -> tuple[np.ndarray, int]:
    data, sample_rate = sf.read(io.BytesIO(audio["bytes"]), dtype="float32")
    if data.ndim == 2:
        data = data.mean(axis=1)
    return data, sample_rate


def write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    sf.write(path, audio, sample_rate, subtype="PCM_16")


def ground_truth_segments(row: dict) -> list[dict]:
    return sorted(row["annotated_transcript"], key=lambda item: item["start_time"])


def active_segments(audio: np.ndarray, sample_rate: int) -> list[tuple[float, float]]:
    frame = max(int(sample_rate * 0.5), 1)
    rms = np.array([np.sqrt(np.mean(audio[start : start + frame] ** 2) + 1e-12) for start in range(0, len(audio), frame)])
    threshold = max(float(np.percentile(rms, 20) * 2.0), 0.002)
    active = rms >= threshold
    segments = []
    start = None
    gap_limit = 1
    gap = 0
    for index, value in enumerate(active):
        if value and start is None:
            start = index
            gap = 0
        elif value and start is not None:
            gap = 0
        elif start is not None:
            gap += 1
            if gap > gap_limit:
                end = index - gap + 1
                if end - start >= 1:
                    segments.append((start * 0.5, end * 0.5))
                start = None
    if start is not None:
        segments.append((start * 0.5, len(active) * 0.5))
    return segments


def segment_features(audio: np.ndarray, sample_rate: int, segments: list[tuple[float, float]]) -> np.ndarray:
    features = []
    for start, end in segments:
        clip = audio[int(start * sample_rate) : int(end * sample_rate)]
        spectrum = np.abs(np.fft.rfft(clip)) + 1e-8
        frequencies = np.fft.rfftfreq(len(clip), 1 / sample_rate)
        centroid = float((spectrum * frequencies).sum() / spectrum.sum())
        zcr = float(np.mean(clip[:-1] * clip[1:] < 0)) if len(clip) > 1 else 0.0
        features.append([float(np.log(np.mean(clip**2) + 1e-8)), centroid / sample_rate, zcr])
    return np.asarray(features)


def diarize(audio: np.ndarray, sample_rate: int, speaker_count: int) -> list[dict]:
    segments = active_segments(audio, sample_rate)
    if not segments:
        return []
    labels = KMeans(n_clusters=speaker_count, random_state=0, n_init=10).fit_predict(segment_features(audio, sample_rate, segments))
    return [{"start_time": start, "end_time": end, "speaker_id": f"PRED_{label:02d}"} for (start, end), label in zip(segments, labels)]


def der(reference: list[dict], predicted: list[dict], duration: float) -> float:
    ref_speakers = sorted({item["speaker_id"] for item in reference})
    pred_speakers = sorted({item["speaker_id"] for item in predicted})
    grid = np.arange(0, duration, 0.1)
    overlap = np.zeros((len(ref_speakers), len(pred_speakers)), dtype=int)
    ref_index = {speaker: index for index, speaker in enumerate(ref_speakers)}
    pred_index = {speaker: index for index, speaker in enumerate(pred_speakers)}
    misses = false_alarms = 0
    for time_point in grid:
        refs = [item["speaker_id"] for item in reference if item["start_time"] <= time_point < item["end_time"]]
        preds = [item["speaker_id"] for item in predicted if item["start_time"] <= time_point < item["end_time"]]
        if not refs and preds:
            false_alarms += 1
        if refs and not preds:
            misses += 1
        for ref_speaker in refs:
            for pred_speaker in preds:
                overlap[ref_index[ref_speaker], pred_index[pred_speaker]] += 1
    mapping = {}
    if overlap.size:
        rows, columns = linear_sum_assignment(-overlap)
        mapping = {pred_speakers[column]: ref_speakers[row] for row, column in zip(rows, columns)}
    confusions = 0
    for time_point in grid:
        refs = {item["speaker_id"] for item in reference if item["start_time"] <= time_point < item["end_time"]}
        preds = {mapping.get(item["speaker_id"], item["speaker_id"]) for item in predicted if item["start_time"] <= time_point < item["end_time"]}
        if refs and preds and not refs.intersection(preds):
            confusions += 1
    speech_time = max(int(grid.size), 1)
    return (misses + false_alarms + confusions) / speech_time


def transcribe_clip(asr, audio: np.ndarray, sample_rate: int, start: float, end: float, root: Path, name: str, language: str) -> str:
    path = root / f"{name}.wav"
    write_wav(path, audio[int(start * sample_rate) : int(end * sample_rate)], sample_rate)
    return asr.transcribe(str(path), lang=language, mode="native", max_new_tokens=128)[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hindi", type=Path, required=True)
    parser.add_argument("--tamil", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).parent / "vendored" / "core"))
    from indic_transcribe import IndicTranscribe

    candidates = []
    for path in (args.hindi, args.tamil):
        table = pq.read_table(path, columns=["audio", "language", "sample_id", "annotated_transcript", "num_speakers", "duration_seconds", "dataset_type"])
        for row in table.to_pylist():
            if row["num_speakers"] == 2 and row["duration_seconds"] <= 90:
                candidates.append(row)
    selected = []
    for language in ("Hindi", "Tamil"):
        for dataset_type in ("Near field", "Far field"):
            matching = [row for row in candidates if row["language"] == language and row["dataset_type"] == dataset_type]
            if matching:
                selected.append(min(matching, key=lambda row: row["duration_seconds"]))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.output_dir) as temporary:
        temp_root = Path(temporary)
        asr = IndicTranscribe.from_pretrained(str(args.model_dir), device=args.device)
        records = []
        for index, row in enumerate(selected, 1):
            audio, sample_rate = read_audio(row["audio"])
            reference_segments = ground_truth_segments(row)
            reference_text = " ".join(item["transcript"] for item in reference_segments if item["transcript"] != "<noise>")
            chunks = []
            for start in np.arange(0, row["duration_seconds"], 40):
                end = min(float(start + 40), row["duration_seconds"])
                chunks.append(transcribe_clip(asr, audio, sample_rate, float(start), end, temp_root, f"{row['sample_id']}-full-{start:.0f}", row["language"][0:2].lower()))
            full_transcript = " ".join(chunks)
            oracle_transcripts = []
            for turn_index, segment in enumerate(reference_segments):
                if segment["transcript"] == "<noise>":
                    continue
                oracle_transcripts.append(transcribe_clip(asr, audio, sample_rate, segment["start_time"], segment["end_time"], temp_root, f"{row['sample_id']}-oracle-{turn_index}", row["language"][0:2].lower()))
            predicted_segments = diarize(audio, sample_rate, row["num_speakers"])
            predicted_transcripts = []
            for turn_index, segment in enumerate(predicted_segments):
                predicted_transcripts.append(transcribe_clip(asr, audio, sample_rate, segment["start_time"], segment["end_time"], temp_root, f"{row['sample_id']}-pred-{turn_index}", row["language"][0:2].lower()))
            records.append({
                "sample_id": row["sample_id"],
                "language": row["language"],
                "dataset_type": row["dataset_type"],
                "duration_seconds": row["duration_seconds"],
                "num_speakers": row["num_speakers"],
                "num_reference_segments": len(reference_segments),
                "num_predicted_segments": len(predicted_segments),
                "reference_text": reference_text,
                "no_diarization_transcript": full_transcript,
                "oracle_turn_transcript": " ".join(oracle_transcripts),
                "automatic_vad_cluster_transcript": " ".join(predicted_transcripts),
                "no_diarization_wer": wer(reference_text, full_transcript),
                "oracle_turn_wer": wer(reference_text, " ".join(oracle_transcripts)),
                "automatic_vad_cluster_wer": wer(reference_text, " ".join(predicted_transcripts)),
                "automatic_der": der(reference_segments, predicted_segments, row["duration_seconds"]),
                "predicted_segments": predicted_segments,
            })
            print(f"[{index}/{len(selected)}] {row['sample_id']}", flush=True)
    output = args.output_dir / "exp-e-pilot-results.jsonl"
    output.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n", encoding="utf-8")
    summary = {
        "sample_count": len(records),
        "scope": "4 two-speaker Hindi/Tamil recordings, near-field and far-field",
        "mean_wer": {name: sum(record[name] for record in records) / max(len(records), 1) for name in ("no_diarization_wer", "oracle_turn_wer", "automatic_vad_cluster_wer")},
        "mean_automatic_der": sum(record["automatic_der"] for record in records) / max(len(records), 1),
        "note": "Pilot only: automatic system is energy VAD plus spectral-feature KMeans, not a neural diarizer.",
    }
    (args.output_dir / "exp-e-pilot-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

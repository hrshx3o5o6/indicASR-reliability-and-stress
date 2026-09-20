"""Run the interpretable EXP-B reliability and abstention pilot."""

from __future__ import annotations

import argparse
import json
import math
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import LeaveOneOut
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


SCRIPT_RANGES = {
    "hi": "DEVANAGARI",
    "bho": "DEVANAGARI",
    "mai": "DEVANAGARI",
    "ta": "TAMIL",
    "te": "TELUGU",
    "ml": "MALAYALAM",
    "kn": "KANNADA",
    "ur": "ARABIC",
}

FEATURE_NAMES = [
    "lid_top1_probability",
    "lid_top2_probability",
    "lid_margin",
    "lid_entropy",
    "lid_plausible_count",
    "explicit_auto_lid_agreement",
    "warning_count",
    "audio_duration_seconds",
    "audio_rms",
    "audio_clipping_ratio",
    "audio_silence_ratio",
    "transcript_word_count",
    "transcript_char_count",
    "transcript_repetition_ratio",
    "transcript_script_consistency",
]


def tokens(text: str) -> list[str]:
    return text.split()


def script_name(character: str) -> str:
    return unicodedata.name(character, "UNKNOWN").split()[0]


def script_consistency(text: str, language: str) -> float:
    expected = SCRIPT_RANGES.get(language, "")
    letters = [char for char in text if char.isalpha()]
    if not letters or not expected:
        return 0.0
    return sum(expected in unicodedata.name(char, "") for char in letters) / len(letters)


def entropy(probabilities: list[float]) -> float:
    return -sum(prob * math.log(prob) for prob in probabilities if prob > 0)


def audio_features(path: Path) -> tuple[float, float, float, float]:
    audio, sample_rate = sf.read(path, always_2d=False)
    values = np.asarray(audio, dtype=np.float64)
    if values.ndim > 1:
        values = values.mean(axis=1)
    absolute = np.abs(values)
    return (
        len(values) / sample_rate,
        float(np.sqrt(np.mean(values * values))),
        float(np.mean(absolute >= 0.999)),
        float(np.mean(absolute < 0.005)),
    )


def word_error_rate(reference: str, hypothesis: str) -> float:
    reference_tokens = tokens(reference)
    hypothesis_tokens = tokens(hypothesis)
    previous = list(range(len(hypothesis_tokens) + 1))
    for ref_index, ref_token in enumerate(reference_tokens, 1):
        current = [ref_index]
        for hyp_index, hyp_token in enumerate(hypothesis_tokens, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[hyp_index] + 1,
                    previous[hyp_index - 1] + (ref_token != hyp_token),
                )
            )
        previous = current
    return previous[-1] / max(len(reference_tokens), 1)


def build_features(row: dict[str, Any], audio_root: Path) -> tuple[dict[str, float], dict[str, Any]]:
    explicit_lid = row["explicit"]["lid"]
    auto_lid = row["auto"]["lid"]
    probabilities = [float(item[1]) for item in auto_lid.get("topk", [])]
    top1 = probabilities[0] if probabilities else 0.0
    top2 = probabilities[1] if len(probabilities) > 1 else 0.0
    transcript = row["explicit"]["transcript"]
    audio_metadata = row.get("audio", {})
    audio_path = audio_metadata.get("path") if isinstance(audio_metadata, dict) else audio_metadata
    path = Path(audio_path)
    if not path.is_absolute():
        path = audio_root / path
    duration, rms, clipping, silence = audio_features(path)
    words = tokens(transcript)
    repeated = len(words) - len(set(words))
    features = {
        "lid_top1_probability": top1,
        "lid_top2_probability": top2,
        "lid_margin": top1 - top2,
        "lid_entropy": entropy(probabilities),
        "lid_plausible_count": float(sum(probability >= 0.01 for probability in probabilities)),
        "explicit_auto_lid_agreement": float(
            explicit_lid.get("lang") == auto_lid.get("lang")
        ),
        "warning_count": float(len(row.get("warnings", []))),
        "audio_duration_seconds": duration,
        "audio_rms": rms,
        "audio_clipping_ratio": clipping,
        "audio_silence_ratio": silence,
        "transcript_word_count": float(len(words)),
        "transcript_char_count": float(len(transcript)),
        "transcript_repetition_ratio": repeated / max(len(words), 1),
        "transcript_script_consistency": script_consistency(transcript, row["language"]),
    }
    metadata = {
        "id": row["id"],
        "language": row["language"],
        "reference": row.get("reference", ""),
        "transcript": transcript,
        "wer": word_error_rate(row.get("reference", ""), transcript),
        "auto_lid": auto_lid.get("lang"),
        "lid_topk": auto_lid.get("topk", []),
    }
    return features, metadata


def model() -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced", max_iter=2000, random_state=0, solver="liblinear"
                ),
            ),
        ]
    )


def risk_coverage(scores: np.ndarray, errors: np.ndarray) -> dict[str, Any]:
    order = np.argsort(-scores)
    ordered_errors = errors[order]
    cumulative = np.cumsum(ordered_errors)
    points = []
    for fraction in (0.25, 0.5, 0.75, 1.0):
        count = max(1, math.ceil(len(scores) * fraction))
        points.append(
            {
                "coverage": count / len(scores),
                "risk": float(cumulative[count - 1] / count),
            }
        )
    return {"points": points, "aurc": float(np.mean(cumulative / np.arange(1, len(scores) + 1)))}


def threshold_for_target(scores: np.ndarray, errors: np.ndarray, target_risk: float, minimum_coverage: float) -> float:
    candidates = sorted(set(float(score) for score in scores), reverse=True)
    valid = []
    for threshold in candidates:
        selected = scores >= threshold
        coverage = float(np.mean(selected))
        risk = float(np.mean(errors[selected])) if selected.any() else 1.0
        if coverage >= minimum_coverage and risk <= target_risk:
            valid.append(threshold)
    return float(min(valid)) if valid else 1.0


def reasons(row: dict[str, Any], features: dict[str, float], threshold_warn: float, score: float) -> list[str]:
    result = []
    if features["lid_margin"] < 0.5:
        result.append("low LID margin")
    if not features["explicit_auto_lid_agreement"]:
        result.append("explicit/auto LID disagreement")
    if features["warning_count"]:
        result.append("Core warning")
    if features["transcript_script_consistency"] < 0.5:
        result.append("script inconsistency")
    if score < threshold_warn:
        result.append("low reliability score")
    return result or ["no reliability warning"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--audio-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--acceptable-wer", type=float, default=0.2)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    feature_rows = []
    metadata_rows = []
    for row in rows:
        features, metadata = build_features(row, args.audio_root)
        feature_rows.append(features)
        metadata_rows.append(metadata)
    matrix = np.array([[features[name] for name in FEATURE_NAMES] for features in feature_rows])
    active_feature_names = [
        name for index, name in enumerate(FEATURE_NAMES) if not np.all(matrix[:, index] == matrix[0, index])
    ]
    active_indices = [FEATURE_NAMES.index(name) for name in active_feature_names]
    matrix = matrix[:, active_indices]
    labels = np.array([metadata["wer"] <= args.acceptable_wer for metadata in metadata_rows], dtype=int)
    if len(set(labels)) < 2:
        raise ValueError("EXP-B requires both acceptable and unacceptable samples")

    oof_scores = np.zeros(len(rows), dtype=float)
    for train_indices, test_indices in LeaveOneOut().split(matrix):
        fitted = model().fit(matrix[train_indices], labels[train_indices])
        oof_scores[test_indices[0]] = fitted.predict_proba(matrix[test_indices])[0, 1]
    errors = 1 - labels
    threshold_accept = threshold_for_target(oof_scores, errors, target_risk=0.10, minimum_coverage=0.25)
    threshold_warn = threshold_for_target(oof_scores, errors, target_risk=0.25, minimum_coverage=0.50)
    if threshold_warn > threshold_accept:
        threshold_warn = threshold_accept
    fitted = model().fit(matrix, labels)
    full_scores = fitted.predict_proba(matrix)[:, 1]

    decisions = []
    for index, (row, features, metadata) in enumerate(zip(rows, feature_rows, metadata_rows)):
        score = float(oof_scores[index])
        status = "accept" if score >= threshold_accept else "warn" if score >= threshold_warn else "abstain"
        reason_list = reasons(row, features, threshold_warn, score)
        decisions.append(
            {
                "status": status,
                "language": row["language"],
                "language_confidence": row["auto"]["lid"].get("topk", [[None, 0.0]])[0][1],
                "lid_topk": row["auto"]["lid"].get("topk", []),
                "reliability": score,
                "transcript": row["explicit"]["transcript"],
                "audio": row.get("audio", {}),
                "uncertain_spans": [],
                "reasons": reason_list,
                "sample_id": row["id"],
                "features": features,
                "label_acceptable": bool(labels[index]),
                "wer": metadata["wer"],
            }
        )

    classifier = fitted.named_steps["classifier"]
    sensitivity = []
    for target_risk in (0.10, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50):
        for minimum_coverage in (0.25, 0.50):
            threshold = threshold_for_target(oof_scores, errors, target_risk, minimum_coverage)
            selected = oof_scores >= threshold
            sensitivity.append(
                {
                    "target_risk": target_risk,
                    "minimum_coverage": minimum_coverage,
                    "threshold": threshold,
                    "coverage": float(np.mean(selected)),
                    "observed_risk": float(np.mean(errors[selected])) if selected.any() else None,
                }
            )
    summary = {
        "sample_count": len(rows),
        "acceptable_wer_threshold": args.acceptable_wer,
        "acceptable_count": int(labels.sum()),
        "unacceptable_count": int((1 - labels).sum()),
        "threshold_accept": threshold_accept,
        "threshold_warn": threshold_warn,
        "threshold_sensitivity": sensitivity,
        "oof_risk_coverage": risk_coverage(oof_scores, errors),
        "oof_roc_auc": float(roc_auc_score(labels, oof_scores)),
        "oof_average_precision": float(average_precision_score(labels, oof_scores)),
        "oof_brier_score": float(brier_score_loss(labels, oof_scores)),
        "decision_counts": {
            status: sum(decision["status"] == status for decision in decisions)
            for status in ("accept", "warn", "abstain")
        },
        "feature_names": active_feature_names,
        "removed_constant_features": [name for name in FEATURE_NAMES if name not in active_feature_names],
        "full_fit_coefficients": {
            name: float(coefficient)
            for name, coefficient in zip(active_feature_names, classifier.coef_[0])
        },
        "note": "OOF metrics are pilot estimates; thresholds are policy targets, not learned ground truth.",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "exp-b-features.jsonl").write_text(
        "\n".join(json.dumps({**metadata, **features}, ensure_ascii=False) for metadata, features in zip(metadata_rows, feature_rows))
        + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "exp-b-decisions.jsonl").write_text(
        "\n".join(json.dumps(decision, ensure_ascii=False) for decision in decisions) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "exp-b-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

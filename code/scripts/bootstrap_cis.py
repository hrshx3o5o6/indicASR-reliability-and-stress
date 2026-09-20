"""Bootstrap 95% CIs and paired significance tests on cached per-sample results.

No model calls -- reads per-sample JSONL already produced by EXP-A/B/C/D and
writes code/results/stats/bootstrap.json. See REPORT.md Sec 5 for context.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

RNG_SEED = 20260920
N_BOOT = 10000


def _wer_tokens(text: str) -> list[str]:
    return re.findall(r"\S+", text.strip())


def _edit_distance(reference: list[str], hypothesis: list[str]) -> int:
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
    """Whitespace-token WER, matching code/analyze_exp_a.py's definition exactly."""
    ref_tokens = _wer_tokens(reference)
    hyp_tokens = _wer_tokens(hypothesis)
    return _edit_distance(ref_tokens, hyp_tokens) / max(len(ref_tokens), 1)


def bootstrap_mean_ci(values: np.ndarray, n_boot: int = N_BOOT, seed: int = RNG_SEED) -> dict:
    rng = np.random.default_rng(seed)
    n = len(values)
    boot_means = np.array([values[rng.integers(0, n, n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    return {"n": n, "mean": float(values.mean()), "ci95": [float(lo), float(hi)]}


def bootstrap_paired_diff_ci(a: np.ndarray, b: np.ndarray, n_boot: int = N_BOOT, seed: int = RNG_SEED) -> dict:
    """CI on mean(a - b) using the paired bootstrap (same resampled indices for both)."""
    rng = np.random.default_rng(seed)
    n = len(a)
    assert len(b) == n
    diffs = a - b
    boot_means = np.array([diffs[rng.integers(0, n, n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    # two-sided bootstrap p-value: fraction of bootstrap diffs crossing zero, doubled
    p_ge = (boot_means <= 0).mean() if diffs.mean() > 0 else (boot_means >= 0).mean()
    p_value = float(min(1.0, 2 * p_ge))
    return {
        "n": n,
        "mean_a": float(a.mean()),
        "mean_b": float(b.mean()),
        "mean_diff": float(diffs.mean()),
        "diff_ci95": [float(lo), float(hi)],
        "excludes_zero": bool(lo > 0 or hi < 0),
        "bootstrap_p_two_sided": p_value,
    }


def bootstrap_unpaired_diff_ci(a: np.ndarray, b: np.ndarray, n_boot: int = N_BOOT, seed: int = RNG_SEED) -> dict:
    """CI on mean(a) - mean(b) via independent resampling -- for two groups with
    no natural per-item pairing (different samples, e.g. EXP-F real-noise vs
    real-clean clips drawn from different speakers/utterances)."""
    rng = np.random.default_rng(seed)
    na, nb = len(a), len(b)
    boot_diffs = np.array(
        [a[rng.integers(0, na, na)].mean() - b[rng.integers(0, nb, nb)].mean() for _ in range(n_boot)]
    )
    lo, hi = np.percentile(boot_diffs, [2.5, 97.5])
    mean_diff = float(a.mean() - b.mean())
    p_ge = (boot_diffs <= 0).mean() if mean_diff > 0 else (boot_diffs >= 0).mean()
    p_value = float(min(1.0, 2 * p_ge))
    return {
        "n_a": na,
        "n_b": nb,
        "mean_a": float(a.mean()),
        "mean_b": float(b.mean()),
        "mean_diff": mean_diff,
        "diff_ci95": [float(lo), float(hi)],
        "excludes_zero": bool(lo > 0 or hi < 0),
        "bootstrap_p_two_sided": p_value,
    }


def bootstrap_auc_ci(labels: np.ndarray, scores: np.ndarray, n_boot: int = N_BOOT, seed: int = RNG_SEED) -> dict:
    rng = np.random.default_rng(seed)
    n = len(labels)
    point = float(roc_auc_score(labels, scores))
    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        y, s = labels[idx], scores[idx]
        if len(set(y.tolist())) < 2:
            continue  # skip resamples with a single class -- AUC undefined
        boots.append(roc_auc_score(y, s))
    boots = np.array(boots)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"n": n, "auc": point, "ci95": [float(lo), float(hi)], "valid_resamples": int(len(boots))}


def wilson_ci(successes: int, n: int, z: float = 1.96) -> dict:
    """Wilson score interval -- appropriate for small-n binomial proportions (n=10 here)."""
    if n == 0:
        return {"n": 0, "phat": None, "ci95": [None, None]}
    phat = successes / n
    denom = 1 + z**2 / n
    center = (phat + z**2 / (2 * n)) / denom
    half = (z * math.sqrt((phat * (1 - phat) + z**2 / (4 * n)) / n)) / denom
    return {"n": n, "successes": successes, "phat": phat, "ci95": [max(0.0, center - half), min(1.0, center + half)]}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exp-c-hypotheses", type=Path, required=True)
    parser.add_argument("--exp-d-flex-results", type=Path, required=True)
    parser.add_argument("--exp-b-decisions", type=Path, required=True)
    parser.add_argument("--exp-a-core-baseline", type=Path, default=None)
    parser.add_argument("--exp-a-flex-baseline", type=Path, default=None)
    parser.add_argument("--exp-f-baseline", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result: dict = {"seed": RNG_SEED, "n_boot": N_BOOT}

    # EXP-C: baseline auto WER vs oracle top-k WER (paired, same 80 samples)
    exp_c_rows = load_jsonl(args.exp_c_hypotheses)
    baseline = np.array([r["baseline_auto_wer"] for r in exp_c_rows])
    oracle = np.array([r["oracle_best_wer"] for r in exp_c_rows])
    result["exp_c"] = {
        "baseline_auto_wer": bootstrap_mean_ci(baseline),
        "oracle_topk_wer": bootstrap_mean_ci(oracle),
        "paired_diff_baseline_minus_oracle": bootstrap_paired_diff_ci(baseline, oracle),
    }

    # EXP-D: Core native vs Flex mixed WER (paired, same 80 samples)
    exp_d_rows = load_jsonl(args.exp_d_flex_results)
    core_native = np.array([r["wer_core_native"] for r in exp_d_rows])
    flex_mixed = np.array([r["wer_flex_mixed"] for r in exp_d_rows])
    result["exp_d"] = {
        "core_native_wer": bootstrap_mean_ci(core_native),
        "flex_mixed_wer": bootstrap_mean_ci(flex_mixed),
        "paired_diff_flex_mixed_minus_core_native": bootstrap_paired_diff_ci(flex_mixed, core_native),
    }

    # EXP-B: OOF reliability score vs label_acceptable -> AUC CI
    exp_b_rows = load_jsonl(args.exp_b_decisions)
    labels = np.array([1 if r["label_acceptable"] else 0 for r in exp_b_rows])
    scores = np.array([r["reliability"] for r in exp_b_rows])
    result["exp_b"] = {"oof_roc_auc": bootstrap_auc_ci(labels, scores)}

    # Second-baseline comparison: Core vs Flex explicit-language-condition WER
    # (matches code/analyze_exp_a.py's own WER definition: explicit.transcript
    # vs reference), same 80 samples. Flex run 2026-09-20, F-005 empirical
    # test / previously-blocked "second-baseline" task.
    if args.exp_a_core_baseline and args.exp_a_flex_baseline:
        core_rows = {r["id"]: r for r in load_jsonl(args.exp_a_core_baseline)}
        flex_rows = {r["id"]: r for r in load_jsonl(args.exp_a_flex_baseline)}
        shared_ids = sorted(set(core_rows) & set(flex_rows))
        core_wer = np.array([wer(core_rows[i]["reference"], core_rows[i]["explicit"]["transcript"]) for i in shared_ids])
        flex_wer = np.array([wer(flex_rows[i]["reference"], flex_rows[i]["explicit"]["transcript"]) for i in shared_ids])
        result["exp_a_core_vs_flex"] = {
            "n_matched": len(shared_ids),
            "core_explicit_wer": bootstrap_mean_ci(core_wer),
            "flex_explicit_wer": bootstrap_mean_ci(flex_wer),
            "paired_diff_flex_minus_core": bootstrap_paired_diff_ci(flex_wer, core_wer),
        }
        bho_ids = [i for i in shared_ids if flex_rows[i]["language"] == "bho"]
        flex_bho_correct = sum(
            1 for i in bho_ids if flex_rows[i]["auto"]["lid"].get("lang") == "bho"
        )
        result["exp_a_flex_bho_lid"] = {"auto_lid_correct": wilson_ci(flex_bho_correct, len(bho_ids))}

    # EXP-F: real-noise vs real-clean WER (unpaired -- different clips/speakers),
    # plus the matched-language delta vs EXP-A's synthetic noise/clean conditions.
    if args.exp_f_baseline and args.exp_a_core_baseline:
        exp_f_rows = load_jsonl(args.exp_f_baseline)
        real_noise = np.array(
            [wer(r["reference"], r["explicit"]["transcript"]) for r in exp_f_rows if r["conditions"]["audio"][0] == "real_noise"]
        )
        real_clean = np.array(
            [wer(r["reference"], r["explicit"]["transcript"]) for r in exp_f_rows if r["conditions"]["audio"][0] == "real_clean"]
        )
        result["exp_f"] = {
            "real_noise_wer": bootstrap_mean_ci(real_noise),
            "real_clean_wer": bootstrap_mean_ci(real_clean),
            "unpaired_diff_real_noise_minus_real_clean": bootstrap_unpaired_diff_ci(real_noise, real_clean),
        }
        core_rows_all = load_jsonl(args.exp_a_core_baseline)
        synth_noise = np.array(
            [wer(r["reference"], r["explicit"]["transcript"]) for r in core_rows_all if r["conditions"]["audio"] == ["background_noise"]]
        )
        synth_clean = np.array(
            [wer(r["reference"], r["explicit"]["transcript"]) for r in core_rows_all if r["conditions"]["audio"] == ["clean"]]
        )
        result["exp_a_synthetic_noise_vs_clean"] = {
            "synthetic_noise_wer": bootstrap_mean_ci(synth_noise),
            "synthetic_clean_wer": bootstrap_mean_ci(synth_clean),
            "unpaired_diff_noise_minus_clean": bootstrap_unpaired_diff_ci(synth_noise, synth_clean),
        }

    # C1: Bhojpuri auto-LID absorption, n=10, 0 successes -> Wilson CI (bootstrap
    # is degenerate at n=10 with a 0/10 point estimate; Wilson is the standard
    # small-n choice and avoids a resampling method producing an uninformative
    # point mass at zero).
    result["exp_a_bho_lid"] = {"auto_lid_correct": wilson_ci(0, 10)}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

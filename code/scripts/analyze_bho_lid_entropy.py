"""F-007: LID entropy analysis, Core vs Flex, from already-committed EXP-A baselines.

compute: none -- reads code/results/summaries/exp-a-v1-{baseline,flex-baseline}.jsonl,
no model calls.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

SEED = 20260920
N_BOOT = 10000


def entropy(topk: list[list]) -> float:
    return -sum(p * math.log(p + 1e-12) for _, p in topk if p > 0)


def load(path: Path) -> dict:
    return {json.loads(line)["id"]: json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-baseline", type=Path, required=True)
    parser.add_argument("--flex-baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    core = load(args.core_baseline)
    flex = load(args.flex_baseline)

    by_language: dict[str, dict] = {}
    for language in sorted({row["language"] for row in core.values()}):
        ids = [i for i, r in core.items() if r["language"] == language]
        core_h = [entropy(core[i]["auto"]["lid"]["topk"]) for i in ids]
        flex_h = [entropy(flex[i]["auto"]["lid"]["topk"]) for i in ids if i in flex]
        by_language[language] = {
            "n": len(ids),
            "core_mean_entropy": sum(core_h) / len(core_h),
            "flex_mean_entropy": sum(flex_h) / len(flex_h) if flex_h else None,
        }

    bho_ids = [i for i, r in core.items() if r["language"] == "bho"]
    core_bho = np.array([entropy(core[i]["auto"]["lid"]["topk"]) for i in bho_ids])
    flex_bho = np.array([entropy(flex[i]["auto"]["lid"]["topk"]) for i in bho_ids])
    rng = np.random.default_rng(SEED)
    diffs = flex_bho - core_bho
    n = len(diffs)
    boots = np.array([diffs[rng.integers(0, n, n)].mean() for _ in range(N_BOOT)])
    lo, hi = np.percentile(boots, [2.5, 97.5])

    result = {
        "seed": SEED,
        "n_boot": N_BOOT,
        "by_language": by_language,
        "bho_paired_entropy_diff_flex_minus_core": {
            "n": n,
            "mean_core": float(core_bho.mean()),
            "mean_flex": float(flex_bho.mean()),
            "mean_diff": float(diffs.mean()),
            "diff_ci95": [float(lo), float(hi)],
            "excludes_zero": bool(lo > 0 or hi < 0),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

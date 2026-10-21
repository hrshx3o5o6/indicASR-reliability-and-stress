"""Evaluate the critical-value guard on Flex native/mixed decodes.

Truth:   verify(reference, mixed)  -- is the mixed output's numeric content
         consistent with what was actually said (and currency kept)?
Guard:   verify(native, mixed)     -- the same check against the model's own
         native decode, which is all the guard has at inference time.

Caveat: truth and guard share the spoken-number parser, so a parser blind spot
is invisible to both. Disagreements are printed for manual spot-checking.

Usage: python eval_guard.py <guard_flex.jsonl> [--out summary.json]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # code/
from guard.verify import digit_groups, verify  # noqa: E402


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    a = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - a) / d, (c + a) / d)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("results", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    rows = [json.loads(line) for line in args.results.open() if line.strip()]
    rows = [r for r in rows if "mixed" in r and "native" in r]

    cells = {"safe_accept": 0, "safe_reject": 0, "unsafe_accept": 0, "unsafe_reject": 0}
    reasons_truth: dict[str, int] = {}
    examples = {"unsafe_accept": [], "safe_reject": [], "unsafe_reject": []}
    with_digits = 0
    for r in rows:
        truth = verify(r["reference"], r["mixed"])
        guard = verify(r["native"], r["mixed"])
        with_digits += bool(digit_groups(r["mixed"]))
        safe = truth["accept_mixed"]
        for reason in truth["reasons"]:
            key = reason.split(":")[0]
            reasons_truth[key] = reasons_truth.get(key, 0) + 1
        cell = ("safe_" if safe else "unsafe_") + ("accept" if guard["accept_mixed"] else "reject")
        cells[cell] += 1
        if cell in examples and len(examples[cell]) < 6:
            examples[cell].append(
                {"id": r["id"], "ref": r["reference"], "native": r["native"], "mixed": r["mixed"],
                 "truth": truth["reasons"], "guard": guard["reasons"]}
            )

    n = len(rows)
    unsafe = cells["unsafe_accept"] + cells["unsafe_reject"]
    safe = cells["safe_accept"] + cells["safe_reject"]
    lo, hi = wilson(cells["unsafe_accept"], n)
    summary = {
        "clips": n,
        "mixed_with_digits": with_digits,
        "raw_mixed_unsafe": unsafe,
        "raw_mixed_unsafe_rate": unsafe / n if n else None,
        "raw_mixed_unsafe_reasons": reasons_truth,
        "cells": cells,
        "guarded_unsafe_rate": cells["unsafe_accept"] / n if n else None,
        "guarded_unsafe_rate_wilson95": [lo, hi],
        "guard_catch_rate": cells["unsafe_reject"] / unsafe if unsafe else None,
        "safe_kept_rate": cells["safe_accept"] / safe if safe else None,
        "examples": examples,
    }
    text = json.dumps(summary, ensure_ascii=False, indent=1)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

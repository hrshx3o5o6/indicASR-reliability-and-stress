"""Round-trip verification of mixed-mode (ITN) output against the native decode.

Accept the mixed transcript only if every digit string in it can be explained
by a spoken-number run in the native transcript (full-run match, same order),
and no spoken currency word has vanished. Otherwise the caller falls back to the
native text. Conservative by construction: anything unverifiable is rejected.
"""

from __future__ import annotations

import re
import unicodedata

from .devanagari_numbers import CURRENCY_MARKERS_LATIN, has_currency_word, number_runs

# a digit group: digits (any script) possibly joined by thousands separators
_DIGITS = r"\d"
_GROUP = re.compile(rf"{_DIGITS}+(?:[,٬،]{_DIGITS}+)*(?:\.{_DIGITS}+)?")


def to_ascii_digits(s: str) -> str:
    return "".join(str(unicodedata.decimal(c)) if c.isdecimal() else c for c in s)


def digit_groups(text: str) -> list[str]:
    return [m.group(0) for m in _GROUP.finditer(text)]


def _canonical(group: str) -> str | None:
    g = to_ascii_digits(group)
    if "." in g:  # decimals are never produced by the spoken-form parser
        return None
    return re.sub(r"[,٬،]", "", g)


def _mixed_has_currency(text: str) -> bool:
    low = text.lower()
    return has_currency_word(text) or any(m in low for m in CURRENCY_MARKERS_LATIN)


def verify(native: str, mixed: str) -> dict:
    """Return {"accept_mixed": bool, "reasons": [...], "groups": [...]}."""
    reasons: list[str] = []
    runs = [r for r in number_runs(native)]
    cursor = 0
    groups = digit_groups(mixed)
    detail = []
    for g in groups:
        canon = _canonical(g)
        if canon is None:
            reasons.append(f"unverifiable:{g}")
            detail.append({"group": g, "status": "unverifiable"})
            continue
        for k in range(cursor, len(runs)):
            if canon in runs[k]["candidates"]:
                cursor = k + 1
                detail.append({"group": g, "status": "verified", "run": " ".join(runs[k]["tokens"])})
                break
        else:
            reasons.append(f"mismatch:{g}")
            detail.append({"group": g, "status": "mismatch"})
    if has_currency_word(native) and not _mixed_has_currency(mixed):
        reasons.append("currency_dropped")
    return {"accept_mixed": not reasons, "reasons": reasons, "groups": detail}


def guarded(native: str, mixed: str) -> tuple[str, dict]:
    """Return (text_to_use, verdict): the mixed text if it verifies, else native."""
    verdict = verify(native, mixed)
    return (mixed if verdict["accept_mixed"] else native), verdict

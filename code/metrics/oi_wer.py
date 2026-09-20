"""Orthographically-informed WER (OI-WER) -- project definition.

See 30-metrics/oi-wer.md for the metric registry entry and its open pitfall:
there is no public reference implementation of the vendor's own OI-WER, and no
curated documented-spelling-variant table exists for this project's suite (the
`reference_variants` field in the manifest currently holds punctuated restatements
of the reference, not curated orthographic alternatives -- see the 2026-09-20
reconciliation note in REPORT.md Sec 5.7).

Per the registry's documented fallback, this module implements:
  1. Unicode NFKC normalization (composes combining marks consistently).
  2. Casefold (affects Latin-script code-switched tokens; no-op for most Indic
     scripts, which do not carry a case distinction).
  3. Cross-script digit normalization: Devanagari/Bengali/Tamil/Telugu/Kannada
     /Malayalam/Perso-Arabic digit forms are mapped to ASCII 0-9, so "9" and
     "٩" and "९" score as the same token.
  4. Punctuation/symbol stripping (Unicode category P* and the S* currency-ish
     leftovers), whitespace collapse.
  5. Multi-reference scoring: if `reference_variants` are supplied, OI-WER is
     the minimum whitespace-token WER across {reference} union variants, each
     put through steps 1-4.

This is explicitly NOT a reproduction of the vendor's own OI-WER (that
definition is not public) -- it is a normalization-tolerant WER, which is
what 30-metrics/oi-wer.md prescribes as the fallback when no public reference
implementation exists. Do not describe results from this module as "the
vendor's OI-WER" in the report; describe them as "project OI-WER (normalization
-tolerant, multi-reference)".
"""

from __future__ import annotations

import re
import unicodedata

_DIGIT_TABLES = [
    "0123456789",  # ASCII (identity, listed for clarity)
    "٠١٢٣٤٥٦٧٨٩",  # Arabic-Indic (Urdu uses these or Extended Arabic-Indic below)
    "۰۱۲۳۴۵۶۷۸۹",  # Extended Arabic-Indic (Urdu/Persian)
    "০১২৩৪৫৬৭৮৯",  # Bengali/Assamese/Maithili (Devanagari script family)
    "०१२३४५६७८९",  # Devanagari (Hindi, Bhojpuri, Maithili)
    "௦௧௨௩௪௫௬௭௮௯",  # Tamil
    "౦౧౨౩౪౫౬౭౮౯",  # Telugu
    "೦೧೨೩೪೫೬೭೮೯",  # Kannada
    "൦൧൨൩൪൫൬൭൮൯",  # Malayalam
]
_DIGIT_MAP = {ch: str(i) for table in _DIGIT_TABLES for i, ch in enumerate(table)}


def normalize_oi(text: str) -> str:
    """Apply the documented OI-WER normalization pipeline to one string."""
    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()
    text = "".join(_DIGIT_MAP.get(ch, ch) for ch in text)
    text = "".join(ch for ch in text if not unicodedata.category(ch).startswith("P"))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokens(text: str) -> list[str]:
    return re.findall(r"\S+", text)


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


def _single_ref_wer(reference: str, hypothesis: str) -> float:
    ref_tokens = _tokens(normalize_oi(reference))
    hyp_tokens = _tokens(normalize_oi(hypothesis))
    return _edit_distance(ref_tokens, hyp_tokens) / max(len(ref_tokens), 1)


def oi_wer(reference: str, hypothesis: str, reference_variants: list[str] | None = None) -> float:
    """Multi-reference, normalization-tolerant WER. Lower is better.

    Returns the minimum WER between `hypothesis` and `reference` or any of
    `reference_variants`, each independently normalized. With no variants
    this degrades to a normalization-tolerant single-reference WER.
    """
    candidates = [reference, *(reference_variants or [])]
    return min(_single_ref_wer(ref, hypothesis) for ref in candidates)

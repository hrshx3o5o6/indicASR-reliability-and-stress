import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from metrics.oi_wer import normalize_oi, oi_wer


def test_normalize_strips_punctuation_and_casefolds():
    assert normalize_oi("Hello, World!") == "hello world"


def test_normalize_maps_devanagari_digits_to_ascii():
    assert normalize_oi("मूल्य ९५०") == "मूल्य 950"


def test_normalize_maps_arabic_indic_digits_to_ascii():
    assert normalize_oi("١٩٥٠٠") == "19500"


def test_normalize_collapses_whitespace():
    assert normalize_oi("a   b\tc") == "a b c"


def test_oi_wer_identical_strings_is_zero():
    assert oi_wer("यह एक वाक्य है", "यह एक वाक्य है") == 0.0


def test_oi_wer_ignores_punctuation_difference():
    assert oi_wer("यह एक वाक्य है।", "यह एक वाक्य है") == 0.0


def test_oi_wer_ignores_digit_script_difference():
    assert oi_wer("मूल्य ९५० रुपये", "मूल्य 950 रुपये") == 0.0


def test_oi_wer_still_penalizes_real_errors():
    # one substitution out of four reference tokens
    assert oi_wer("एक दो तीन चार", "एक दो पांच चार") == 0.25


def test_oi_wer_uses_best_of_multi_reference():
    hypothesis = "chennai station"
    exact_match_variant = "chennai station"
    worse_primary = "madras junction"
    assert oi_wer(worse_primary, hypothesis, reference_variants=[exact_match_variant]) == 0.0


def test_oi_wer_falls_back_to_primary_when_no_variant_helps():
    assert oi_wer("एक दो तीन", "एक दो तीन", reference_variants=["पूरी तरह अलग वाक्य"]) == 0.0

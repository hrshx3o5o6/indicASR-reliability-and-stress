"""Spoken-number parsing for Devanagari-script Hindi, Bhojpuri and Maithili.

Purpose: given a *native* (spoken-form) transcript, recover every number it
contains as the set of digit strings it could legitimately be rendered as, so
that a mixed-mode (ITN) transcript can be checked against it. Parsing is
deliberately conservative: anything not understood is left out, which makes the
verifier reject (fall back to native) rather than accept an unchecked value.

Two renderings are considered for a run of adjacent number words:
  * "readout": digits concatenated token by token ("तीन तीन पाँच" -> "335",
    "डबल जीरो छह" -> "006", "चार छब्बीस" -> "426"). Used for account/card/phone
    numbers.
  * "magnitude": ordinary quantity with hundred/thousand/lakh/crore
    ("दो हजार अट्ठाईस" -> "2028"). Only produced when the run has a multiplier.
"""

from __future__ import annotations

import re
import unicodedata

# value -> spelling variants (Hindi plus common Bhojpuri/Maithili spellings).
# Keys are normalized below, so nukta / chandrabindu variants need not be listed.
_WORDS: dict[int, str] = {
    0: "शून्य जीरो सुन्न",
    1: "एक",
    2: "दो दू दुई",
    3: "तीन",
    4: "चार चारि",
    5: "पांच पाच",
    6: "छह छः छ छे छौ छओ",
    7: "सात",
    8: "आठ",
    9: "नौ नओ",
    10: "दस",
    11: "ग्यारह",
    12: "बारह",
    13: "तेरह",
    14: "चौदह",
    15: "पंद्रह पन्द्रह पंदरह",
    16: "सोलह",
    17: "सत्रह",
    18: "अठारह",
    19: "उन्नीस उनीस",
    20: "बीस",
    21: "इक्कीस",
    22: "बाईस बाइस",
    23: "तेईस तेइस",
    24: "चौबीस",
    25: "पच्चीस",
    26: "छब्बीस",
    27: "सत्ताईस सत्ताइस",
    28: "अट्ठाईस अठाईस अठाइस अट्ठाइस",
    29: "उनतीस उन्तीस",
    30: "तीस",
    31: "इकतीस इकत्तीस",
    32: "बत्तीस",
    33: "तैंतीस तेंतीस तैतीस",
    34: "चौंतीस चौतीस",
    35: "पैंतीस पैतीस",
    36: "छत्तीस",
    37: "सैंतीस सैतीस",
    38: "अड़तीस",
    39: "उनतालीस उन्तालीस उनचालीस",
    40: "चालीस",
    41: "इकतालीस",
    42: "बयालीस",
    43: "तैंतालीस तेतालीस तिरतालीस",
    44: "चौवालीस चवालीस चौंवालीस",
    45: "पैंतालीस पैतालीस",
    46: "छियालीस",
    47: "सैंतालीस सैतालीस",
    48: "अड़तालीस",
    49: "उनचास",
    50: "पचास",
    51: "इक्यावन",
    52: "बावन",
    53: "तिरपन तिरेपन",
    54: "चौवन",
    55: "पचपन",
    56: "छप्पन",
    57: "सत्तावन",
    58: "अट्ठावन अठावन",
    59: "उनसठ",
    60: "साठ",
    61: "इकसठ",
    62: "बासठ",
    63: "तिरसठ तिरेसठ",
    64: "चौंसठ",
    65: "पैंसठ",
    66: "छियासठ",
    67: "सड़सठ",
    68: "अड़सठ",
    69: "उनहत्तर उनहतर",
    70: "सत्तर",
    71: "इकहत्तर",
    72: "बहत्तर",
    73: "तिहत्तर",
    74: "चौहत्तर",
    75: "पचहत्तर",
    76: "छिहत्तर",
    77: "सतहत्तर",
    78: "अठहत्तर",
    79: "उनासी उन्यासी",
    80: "अस्सी",
    81: "इक्यासी",
    82: "बयासी",
    83: "तिरासी",
    84: "चौरासी",
    85: "पचासी",
    86: "छियासी",
    87: "सत्तासी",
    88: "अट्ठासी अठासी",
    89: "नवासी",
    90: "नब्बे",
    91: "इक्यानवे इक्यानबे",
    92: "बानवे बानबे",
    93: "तिरानवे तिरानबे",
    94: "चौरानवे चौरानबे",
    95: "पंचानवे पंचानबे",
    96: "छियानवे छियानबे",
    97: "सत्तानवे सत्तानबे",
    98: "अट्ठानवे अट्ठानबे अठानवे",
    99: "निन्यानवे निन्यानबे",
}

# Words that are numbers only in context (e.g. "नव" is 9 in a digit readout but also
# "new"): a run made solely of these is not treated as a number.
_WEAK = {"नव": 9}

_MULTIPLIERS = {"सौ": 100, "सै": 100, "हजार": 1000, "लाख": 100000, "करोड": 10_000_000}
_REPEAT = {"डबल": 2, "ट्रिपल": 3}

CURRENCY_WORDS = {"रुपिया", "रुपया", "रुपये", "रुपए", "रूपये", "रुपैया", "रुपइया", "रुपैये", "रु", "₹"}
CURRENCY_MARKERS_LATIN = ("₹", "rs", "inr", "rupee")

_PUNCT = re.compile(r"[\s।,.?!:;\"'()\[\]{}\-–—]+")


def normalize_token(token: str) -> str:
    """NFC, drop nukta, fold chandrabindu to anusvara."""
    token = unicodedata.normalize("NFC", token)
    token = token.replace("़", "").replace("ँ", "ं")
    # NFC recomposes nukta letters (ड़ -> U+095C) only for some; decompose then strip.
    token = unicodedata.normalize("NFD", token).replace("़", "")
    return unicodedata.normalize("NFC", token)


_VALUE_OF: dict[str, int] = {}
for _value, _spellings in _WORDS.items():
    for _spelling in _spellings.split():
        _VALUE_OF[normalize_token(_spelling)] = _value
_WEAK_OF = {normalize_token(k): v for k, v in _WEAK.items()}
for _k, _v in _WEAK_OF.items():
    _VALUE_OF.setdefault(_k, _v)
_MULT_OF = {normalize_token(k): v for k, v in _MULTIPLIERS.items()}
_REPEAT_OF = {normalize_token(k): v for k, v in _REPEAT.items()}
_CURRENCY = {normalize_token(w) for w in CURRENCY_WORDS}


def tokenize(text: str) -> list[str]:
    return [normalize_token(t) for t in _PUNCT.split(text) if t]


def _is_number_token(token: str) -> bool:
    return token in _VALUE_OF or token in _MULT_OF or token in _REPEAT_OF


def _readout(tokens: list[str]) -> str | None:
    out: list[str] = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in _REPEAT_OF:
            if i + 1 >= len(tokens) or tokens[i + 1] not in _VALUE_OF or _VALUE_OF[tokens[i + 1]] > 9:
                return None
            out.append(str(_VALUE_OF[tokens[i + 1]]) * _REPEAT_OF[t])
            i += 2
        elif t in _VALUE_OF:
            out.append(str(_VALUE_OF[t]))
            i += 1
        else:
            return None
    return "".join(out)


def _magnitude(tokens: list[str]) -> str | None:
    total, chunk = 0, 0
    for t in tokens:
        if t in _VALUE_OF:
            chunk += _VALUE_OF[t]
        elif t in _MULT_OF:
            m = _MULT_OF[t]
            if m == 100:
                chunk = (chunk or 1) * 100
            else:
                total += (chunk or 1) * m
                chunk = 0
        else:
            return None
    return str(total + chunk)


def number_runs(text: str) -> list[dict]:
    """Maximal runs of adjacent number words, each with its candidate renderings."""
    tokens = tokenize(text)
    runs: list[dict] = []
    i = 0
    while i < len(tokens):
        if not _is_number_token(tokens[i]):
            i += 1
            continue
        j = i
        while j < len(tokens) and _is_number_token(tokens[j]):
            j += 1
        run = tokens[i:j]
        if all(t in _WEAK_OF for t in run):
            i = j
            continue
        candidates = set()
        has_mult = any(t in _MULT_OF for t in run)
        if not has_mult:
            r = _readout(run)
            if r is not None:
                candidates.add(r)
        else:
            m = _magnitude(run)
            if m is not None:
                candidates.add(m)
        if candidates:
            runs.append({"tokens": run, "candidates": candidates, "start": i})
        else:
            runs.append({"tokens": run, "candidates": set(), "start": i, "unparsed": True})
        i = j
    return runs


def has_currency_word(text: str) -> bool:
    return any(t in _CURRENCY for t in tokenize(text))

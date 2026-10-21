import pytest

from guard.devanagari_numbers import number_runs
from guard.verify import guarded, verify


def cands(text):
    runs = number_runs(text)
    assert len(runs) == 1, runs
    return runs[0]["candidates"]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("तिरानबे हजार", "93000"),
        ("तिरानवे", "93"),
        ("दू हजार अठाईस", "2028"),
        ("एक लाख पचास हजार", "150000"),
        ("दो सौ पचास", "250"),
        ("तीन हजार दो सौ", "3200"),
        ("पैंतीस", "35"),
        ("पैतीस", "35"),
        ("डबल जीरो छह", "006"),
        ("तीन तीन पाँच", "335"),
        ("तीन तीन पाच", "335"),
        ("नौ नौ तीन", "993"),
        ("चार छब्बीस", "426"),
        ("ज़ीरो", "0"),
        ("ट्रिपल नौ", "999"),
        ("दुई हजार पच्चीस", "2025"),
        ("नव जीरो आठ एक", "9081"),
        ("दुई जीरो दुई तीन", "2023"),
        ("छऽ", "6"),
        ("शुन्न जिरो", "00"),
        ("चौउवन", "54"),
    ],
)
def test_candidates(text, expected):
    assert expected in cands(text)


def test_weak_word_alone_is_not_a_number():
    assert number_runs("नव नवीनतम कृषि सलाह") == []


def test_non_number_words_break_runs():
    runs = number_runs("तीन बजे पांच लोग")
    assert [r["candidates"] for r in runs] == [{"3"}, {"5"}]


# Real EXP-D rows (Flex native vs Flex mixed, cached in code/results/summaries).
NATIVE_001 = "कृपा करके हमरा डेबिट कार्ड से तिरानबे हजार रुपिया भेज दीही कार्ड नंबर"
MIXED_001 = "कृपा करके हमरा debit card से  93,000 भेज दीही card number."
NATIVE_002 = "तीन तीन पाँच सात नौ छह पाँच जीरो छह पाँच छह आठ पाँच चार पाँच पाँच हऽ ई अक्टूबर दू हजार अट्ठाईस ले खतम होई आ सी वी वी नौ नौ तीन हऽ"
MIXED_002 = "3357965065685455 हऽ ई October 2028 ले खतम होई आ सी वी वी 993 हऽ"
NATIVE_004 = "रउआ बैंक के खाता संख्या डबल जीरो छह डबल जीरो पैंतीस डबल जीरो डबल जीरो चार छब्बीस"
MIXED_004 = "रउआ बैंक के खाता संख्या 0060035000426"


def test_currency_word_dropped_is_rejected():
    v = verify(NATIVE_001, MIXED_001)
    assert not v["accept_mixed"] and "currency_dropped" in v["reasons"]
    assert v["groups"][0]["status"] == "verified"  # the value 93,000 itself was right


def test_correct_long_readout_and_year_accepted():
    assert verify(NATIVE_002, MIXED_002)["accept_mixed"]


def test_dropped_zero_in_account_number_rejected():
    v = verify(NATIVE_004, MIXED_004)
    assert not v["accept_mixed"] and v["reasons"] == ["mismatch:0060035000426"]


def test_guarded_falls_back_to_native():
    text, v = guarded(NATIVE_004, MIXED_004)
    assert text == NATIVE_004 and not v["accept_mixed"]
    text, v = guarded(NATIVE_002, MIXED_002)
    assert text == MIXED_002


def test_truncated_prefix_is_not_accepted():
    # mixed renders only part of a spoken readout -> must not verify
    assert not verify("तीन तीन पाँच सात", "335")["accept_mixed"]


def test_decimal_is_unverifiable():
    assert not verify("आधे घंटे", "0.5 hr")["accept_mixed"]


def test_indic_digits_normalized():
    assert verify("पैंतीस", "३५")["accept_mixed"]


def test_no_digits_means_nothing_to_check():
    assert verify("तीन बजे", "तीन बजे")["accept_mixed"]

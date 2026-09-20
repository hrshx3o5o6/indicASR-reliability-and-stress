"""Run EXP-C top-K language routing with shared-encoder decoding."""

from __future__ import annotations

import argparse
import json
import math
import unicodedata
from pathlib import Path
from typing import Any

import torch


SCRIPT_NAMES = {
    "hi": "DEVANAGARI", "bho": "DEVANAGARI", "mai": "DEVANAGARI",
    "ta": "TAMIL", "te": "TELUGU", "ml": "MALAYALAM", "kn": "KANNADA", "ur": "ARABIC",
}


def word_error_rate(reference: str, hypothesis: str) -> float:
    reference_tokens, hypothesis_tokens = reference.split(), hypothesis.split()
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


def script_consistency(text: str, language: str) -> float:
    expected = SCRIPT_NAMES.get(language, "")
    letters = [char for char in text if char.isalpha()]
    if not letters or not expected:
        return 0.0
    return sum(expected in unicodedata.name(char, "") for char in letters) / len(letters)


def decode_candidate(asr: Any, feats: torch.Tensor, mask: torch.Tensor, enc: Any, language: str, max_new_tokens: int) -> dict:
    prompt = asr.tokenizer.encode_prompt(language, itn=False, romanized=False)
    decoder_input_ids = torch.tensor([prompt], device=asr.device)
    with torch.inference_mode():
        output = asr.model.generate(
            input_features=feats,
            encoder_outputs=enc,
            attention_mask=mask,
            decoder_input_ids=decoder_input_ids,
            max_new_tokens=max_new_tokens,
            output_scores=True,
            return_dict_in_generate=True,
        )
    sequence = output.sequences[0].tolist()
    generated_ids = asr.tokenizer.strip_prompt_and_trim(sequence, prompt)
    text = asr.tokenizer.decode(generated_ids)
    mean_logprob = 0.0
    if output.scores and generated_ids:
        token_count = min(len(output.scores), len(generated_ids))
        scores = output.scores[-token_count:]
        token_ids = generated_ids[-token_count:]
        values = []
        for logits, token_id in zip(scores, token_ids):
            values.append(float(torch.log_softmax(logits[0], dim=-1)[token_id]))
        mean_logprob = sum(values) / len(values)
    return {
        "language": language,
        "transcript": text,
        "mean_token_logprob": mean_logprob,
        "script_consistency": script_consistency(text, language),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--audio-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    import sys

    sys.path.insert(0, str(Path(__file__).parent / "vendored" / "core"))
    from indic_transcribe import IndicTranscribe
    from lid import lid_from_encoder_states

    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    asr = IndicTranscribe.from_pretrained(str(args.model_dir), device=args.device)
    output_rows = []
    for index, row in enumerate(rows, 1):
        audio = row["audio"]
        audio_path = Path(audio["path"])
        if not audio_path.is_absolute():
            audio_path = args.audio_root / audio_path
        wav = asr._load(str(audio_path))
        feats, mask = asr._features(wav)
        with torch.inference_mode():
            enc = asr.model.model.encoder(feats, attention_mask=mask)
            topk = lid_from_encoder_states(
                asr.model, enc.last_hidden_state, enc.lengths, tokenizer=asr.tokenizer, topk=args.top_k
            )[0]
        candidates = []
        for language, prior in topk:
            candidate = decode_candidate(asr, feats, mask, enc, language, args.max_new_tokens)
            candidate["lid_prior"] = float(prior)
            candidate["combined_score"] = candidate["mean_token_logprob"] + math.log(float(prior) + 1e-8)
            candidate["wer"] = word_error_rate(row.get("reference", ""), candidate["transcript"])
            candidates.append(candidate)
        selected = max(candidates, key=lambda item: item["combined_score"])
        baseline_auto = row["auto"]["transcript"]
        truth_in_topk = row["language"] in [item["language"] for item in candidates]
        output_rows.append(
            {
                "sample_id": row["id"],
                "language": row["language"],
                "condition": row.get("conditions", {}).get("audio", []),
                "truth_in_topk": truth_in_topk,
                "topk_languages": [item["language"] for item in candidates],
                "baseline_auto_language": row["auto"]["lid"]["lang"],
                "baseline_auto_transcript": baseline_auto,
                "baseline_auto_wer": word_error_rate(row.get("reference", ""), baseline_auto),
                "selected": selected,
                "oracle_best_wer": min(item["wer"] for item in candidates),
                "candidates": candidates,
            }
        )
        print(f"[{index}/{len(rows)}] {row['id']}: selected={selected['language']} truth={row['language']}")
    baseline_wers = [row["baseline_auto_wer"] for row in output_rows]
    selected_wers = [row["selected"]["wer"] for row in output_rows]
    oracle_wers = [row["oracle_best_wer"] for row in output_rows]
    summary = {
        "sample_count": len(output_rows),
        "top_k": args.top_k,
        "truth_in_topk": sum(row["truth_in_topk"] for row in output_rows),
        "baseline_auto_wer": sum(baseline_wers) / len(baseline_wers),
        "adaptive_selected_wer": sum(selected_wers) / len(selected_wers),
        "oracle_topk_wer": sum(oracle_wers) / len(oracle_wers),
        "adaptive_selected_lid_accuracy": sum(row["selected"]["language"] == row["language"] for row in output_rows) / len(output_rows),
        "note": "Oracle WER is diagnostic only; adaptive selection uses LID prior plus mean decoder token log-probability.",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "exp-c-hypotheses.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in output_rows) + "\n", encoding="utf-8"
    )
    (args.output_dir / "exp-c-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

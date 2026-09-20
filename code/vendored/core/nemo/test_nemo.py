#!/usr/bin/env python3
"""Check that this .nemo loads and transcribes on a stock NeMo install.

    pip install "nemo_toolkit[asr]"
    python nemo/test_nemo.py <audio.wav> [lang]

With no arguments it only loads the model.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from load_nemo import find_checkpoint, load_nemo_model  # noqa: E402


def main() -> int:
    audio = sys.argv[1] if len(sys.argv) > 1 else None
    lang = sys.argv[2] if len(sys.argv) > 2 else "hi"

    model = load_nemo_model()
    import nemo
    from nemo.collections.common.tokenizers.canary_tokenizer import CanaryTokenizer

    ok = isinstance(model.tokenizer, CanaryTokenizer)
    print(f"NeMo {nemo.__version__}")
    print(f"loaded {os.path.basename(find_checkpoint())}: tokenizer {type(model.tokenizer).__name__}, "
          f"sub-tokenizers {model.tokenizer.langs}, prompt-compatible: {ok}")
    if not ok:
        print("FAIL: the prompt formatter will not accept this tokenizer")
        return 1

    if audio is None:
        print("no audio given; pass a file: python nemo/test_nemo.py audio.wav hi")
        return 0

    out = model.transcribe([audio], batch_size=1, source_lang=lang, target_lang=lang, pnc="yes")[0]
    text = getattr(out, "text", out)
    print(f"\n{os.path.basename(audio)} [{lang}]: {text}")
    return 0 if text else 1


if __name__ == "__main__":
    raise SystemExit(main())

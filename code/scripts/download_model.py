"""Download bodhan-ai/indic-transcribe-core weights (run once, ~4.6 GB).

Usage: .venv/bin/python scripts/download_model.py
"""
import sys
from pathlib import Path

REPO = "bodhan-ai/indic-transcribe-core"


def main() -> int:
    from huggingface_hub import snapshot_download

    env = {}
    for line in (Path(__file__).resolve().parent.parent / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()

    path = snapshot_download(
        REPO,
        token=env.get("HF_TOKEN"),
        allow_patterns=["*.json", "*.py", "*.model", "*.md", "*.safetensors"],
    )
    print(f"SNAPSHOT_READY {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

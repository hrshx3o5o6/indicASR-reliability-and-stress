"""Verify HF token + gated repo access for EXP-A (resolves dossier to-verify items).

Usage: .venv/bin/python scripts/verify_access.py
"""
import json
import os
import sys
from pathlib import Path

REPOS = ["bodhan-ai/indic-transcribe-core", "bodhan-ai/indic-transcribe-flex"]


def load_env(path: Path) -> dict:
    env = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def main() -> int:
    from huggingface_hub import HfApi

    env = load_env(Path(__file__).resolve().parent.parent / ".env")
    token = env.get("HF_TOKEN") or os.environ.get("HF_TOKEN")
    if not token:
        print("FAIL: no HF_TOKEN found in code/.env or environment")
        return 1

    api = HfApi(token=token)
    who = api.whoami()
    name = who.get("name") or who.get("fullname") or str(who)[:80]
    print(f"OK: authenticated as {name}")

    for repo in REPOS:
        print(f"\n=== {repo} ===")
        try:
            info = api.model_info(repo, files_metadata=False)
        except Exception as e:  # noqa: BLE001 - report and continue
            print(f"  ACCESS FAIL: {type(e).__name__}: {e}")
            continue
        print(f"  access OK (gated gate passed) · private={info.private} · sha={info.sha[:12] if info.sha else '?'}")
        sibs = [s.rfilename for s in (info.siblings or [])]
        interesting = [f for f in sibs if not f.endswith((".safetensors", ".bin", ".pt", ".msgpack", ".h5"))]
        print(f"  files ({len(sibs)} total), non-weight files:")
        for f in sorted(interesting):
            print(f"    {f}")

        cfg = getattr(info, "config", None) or {}
        if cfg:
            print("  config metadata keys:", sorted(cfg.keys()))
        card_data = getattr(info, "card_data", None)
        if card_data is not None:
            d = card_data.to_dict() if hasattr(card_data, "to_dict") else {}
            print("  card tags:", d.get("tags", []))

        # dump raw info.json if present (repo-level config often hides here)
        try:
            p = api.hf_hub_download(repo, "info.json")
            print("  info.json:")
            print("  " + json.dumps(json.loads(Path(p).read_text()), indent=2)[:2000])
        except Exception:
            print("  (no info.json)")

    print("\nDONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())

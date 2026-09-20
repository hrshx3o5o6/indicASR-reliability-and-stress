"""Thin client for the pinned Indic ASR service (Pattern 1, D-003).

Sandbox-safe: no weights, no HF token, no model library. Talks HTTP only.

    from asr_client import AsrClient
    client = AsrClient("https://<tunnel-host>")
    print(client.transcribe("clip.wav", lang="hi"))

CLI smoke test:

    .venv/bin/python asr_client.py --url https://<host> --audio clip.wav --lang hi
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Any, Optional

import httpx


class AsrClient:
    def __init__(self, base_url: str, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "AsrClient":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    @staticmethod
    def encode_audio(path: str | Path) -> str:
        return base64.b64encode(Path(path).read_bytes()).decode("ascii")

    def health(self) -> dict[str, Any]:
        return self._get("/health")

    def transcribe(
        self,
        audio: str | Path,
        lang: Optional[str] = None,
        mode: str = "native",
        return_lid: bool = True,
        max_new_tokens: int = 256,
        allowed_langs: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        return self._post(
            "/transcribe",
            {
                "audio_b64": self.encode_audio(audio),
                "lang": lang,
                "mode": mode,
                "return_lid": return_lid,
                "max_new_tokens": max_new_tokens,
                "allowed_langs": allowed_langs,
            },
        )

    def identify(
        self,
        audio: str | Path,
        topk: int = 5,
        allowed_langs: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        return self._post(
            "/identify",
            {"audio_b64": self.encode_audio(audio), "topk": topk, "allowed_langs": allowed_langs},
        )

    def topk_decode(
        self, audio: str | Path, k: int = 3, mode: str = "native", max_new_tokens: int = 256
    ) -> dict[str, Any]:
        return self._post(
            "/topk_decode",
            {
                "audio_b64": self.encode_audio(audio),
                "k": k,
                "mode": mode,
                "max_new_tokens": max_new_tokens,
            },
        )

    def _get(self, path: str) -> dict[str, Any]:
        response = self._client.get(path)
        return self._unwrap(response)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post(path, json=payload)
        return self._unwrap(response)

    @staticmethod
    def _unwrap(response: httpx.Response) -> dict[str, Any]:
        if response.status_code >= 400:
            raise RuntimeError(f"ASR service {response.status_code}: {response.text[:500]}")
        return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--lang")
    parser.add_argument("--mode", default="native")
    parser.add_argument("--topk", type=int, default=0, help=">0 runs /topk_decode instead")
    args = parser.parse_args()

    with AsrClient(args.url) as client:
        print(json.dumps(client.health(), indent=2, ensure_ascii=False))
        if args.audio:
            if args.topk > 0:
                out = client.topk_decode(args.audio, k=args.topk, mode=args.mode)
            else:
                out = client.transcribe(args.audio, lang=args.lang, mode=args.mode)
            print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

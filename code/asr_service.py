"""Pinned Indic ASR inference service (Pattern 1, D-003).

Weights live in this process. Sandboxes and remote runners are thin clients
(`asr_client.py`); weights and HF_TOKEN never enter a sandbox.

Run on the machine that holds the checkpoint:

    .venv/bin/python asr_service.py --model-dir data/model --device mps --port 8100

Expose it publicly (reqly blocks loopback/private ranges) with e.g.

    cloudflared tunnel --url http://localhost:8100

Every response echoes {revision, dtype, decoding} so a caller can prove which
model and settings produced a transcript.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import tempfile
import threading
import warnings
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DEFAULT_REVISION = "4d29eeb7a099"
MODES = ("native", "mixed", "romanised", "romanized", "itn")


# --------------------------------------------------------------------------- #
# request / response models
# --------------------------------------------------------------------------- #
class TranscribeRequest(BaseModel):
    audio_b64: str
    lang: Optional[str] = None
    mode: str = "native"
    return_lid: bool = True
    max_new_tokens: int = 256
    allowed_langs: Optional[list[str]] = None


class IdentifyRequest(BaseModel):
    audio_b64: str
    topk: int = 5
    allowed_langs: Optional[list[str]] = None


class TopKDecodeRequest(BaseModel):
    audio_b64: str
    k: int = 3
    mode: str = "native"
    max_new_tokens: int = 256


# --------------------------------------------------------------------------- #
# model holder
# --------------------------------------------------------------------------- #
class ModelHolder:
    def __init__(self) -> None:
        self.asr: Any = None
        self.lock = threading.Lock()
        self.revision = DEFAULT_REVISION
        self.device = "cpu"
        self.dtype = "float32"
        self.model_dir = ""

    def load(self, model_dir: Path, device: str) -> None:
        sys.path.insert(0, str(Path(__file__).parent / "vendored" / "core"))
        from indic_transcribe import IndicTranscribe

        self.asr = IndicTranscribe.from_pretrained(str(model_dir), device=device)
        self.device = self.asr.device
        self.dtype = str(next(self.asr.model.parameters()).dtype).replace("torch.", "")
        self.model_dir = str(model_dir)
        self.revision = __import__("os").environ.get("ASR_REVISION", DEFAULT_REVISION)

    def info(self) -> dict[str, Any]:
        return {
            "revision": self.revision,
            "device": self.device,
            "dtype": self.dtype,
            "model_dir": self.model_dir,
            "modes": sorted(set(MODES)),
            "weak_lid_langs": sorted(__import__("indic_transcribe").WEAK_LID_LANGS),
        }


HOLDER = ModelHolder()
app = FastAPI(title="Indic ASR inference service", version="0.1.0")


def _decode_audio(audio_b64: str) -> str:
    """base64 WAV -> decoded tensor path. Temp file lets the wrapper resample."""
    try:
        raw = base64.b64decode(audio_b64, validate=True)
    except Exception as error:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"audio_b64 not valid base64: {error}")
    handle = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    handle.write(raw)
    handle.close()
    return handle.name


def _guard() -> ModelHolder:
    if HOLDER.asr is None:
        raise HTTPException(status_code=503, detail="model not loaded")
    return HOLDER


def _run(fn):
    """Serialize model access and capture warnings; drop the temp file."""
    path = None
    try:
        with HOLDER.lock:
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                result = fn()
        return result, [str(w.message) for w in captured]
    finally:
        if path:
            Path(path).unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# routes
# --------------------------------------------------------------------------- #
@app.get("/health")
def health() -> dict[str, Any]:
    info = HOLDER.info()
    info["status"] = "ok" if HOLDER.asr is not None else "loading"
    return info


@app.post("/transcribe")
def transcribe(req: TranscribeRequest) -> dict[str, Any]:
    holder = _guard()
    path = _decode_audio(req.audio_b64)
    try:
        with holder.lock:
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                text, lid = holder.asr.transcribe(
                    path,
                    lang=req.lang,
                    mode=req.mode,
                    max_new_tokens=req.max_new_tokens,
                    return_lid=req.return_lid,
                    allowed_langs=req.allowed_langs,
                )
        return {
            "text": text,
            "lid": _json_safe(lid),
            "warnings": [str(w.message) for w in captured],
            "revision": holder.revision,
            "dtype": holder.dtype,
            "decoding": {"mode": req.mode, "max_new_tokens": req.max_new_tokens, "greedy": True},
        }
    finally:
        Path(path).unlink(missing_ok=True)


@app.post("/identify")
def identify(req: IdentifyRequest) -> dict[str, Any]:
    holder = _guard()
    path = _decode_audio(req.audio_b64)
    try:
        with holder.lock:
            topk = holder.asr.identify(path, topk=req.topk, allowed_langs=req.allowed_langs)
        return {
            "topk": _json_safe(topk),
            "revision": holder.revision,
            "dtype": holder.dtype,
        }
    finally:
        Path(path).unlink(missing_ok=True)


@app.post("/topk_decode")
def topk_decode(req: TopKDecodeRequest) -> dict[str, Any]:
    """Identify top-k then decode each candidate language (EXP-C primitive)."""
    holder = _guard()
    path = _decode_audio(req.audio_b64)
    try:
        with holder.lock:
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                candidates = holder.asr.identify(path, topk=req.k)
                hypotheses = []
                for lang, prob in candidates:
                    hypotheses.append(
                        {
                            "lang": lang,
                            "prob": float(prob),
                            "text": holder.asr.transcribe(
                                path, lang=lang, mode=req.mode,
                                max_new_tokens=req.max_new_tokens,
                            ),
                        }
                    )
        return {
            "hypotheses": hypotheses,
            "warnings": [str(w.message) for w in captured],
            "revision": holder.revision,
            "dtype": holder.dtype,
            "decoding": {"mode": req.mode, "k": req.k, "greedy": True},
        }
    finally:
        Path(path).unlink(missing_ok=True)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=Path("data/model"))
    parser.add_argument("--device", default="mps")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8100)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    args = parser.parse_args()

    import os

    os.environ.setdefault("ASR_REVISION", args.revision)
    HOLDER.load(args.model_dir, args.device)
    info = HOLDER.info()
    print(json.dumps({"event": "model_loaded", **info}, indent=2))

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

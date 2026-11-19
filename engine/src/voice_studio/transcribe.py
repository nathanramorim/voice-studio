"""Transcrição local com whisper.cpp (`whisper-cli`). Nada sai da máquina."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

from . import audio
from .errors import VoiceError

MODEL_ENV = "VOICE_STUDIO_WHISPER_MODEL"


def resolve_model(model: Path | None) -> Path:
    chosen = model or (Path(os.environ[MODEL_ENV]) if os.environ.get(MODEL_ENV) else None)
    if chosen is None or not chosen.is_file():
        raise VoiceError(
            f"Informe --model (ou defina {MODEL_ENV}) com um modelo ggml do whisper.cpp, "
            "ex.: ggml-small.bin. Para instalar: uv run scripts/requisitos.py instalar whisper-cli modelo-whisper."
        )
    return chosen


def transcribe(video: Path, model: Path | None, lang: str = "pt") -> list[dict]:
    """Segmentos `{start, end, source}` em segundos."""
    if not video.is_file():
        raise VoiceError(f"Arquivo não encontrado: {video}")
    weights = resolve_model(model)
    with tempfile.TemporaryDirectory() as tmp:
        wav, base = Path(tmp) / "in.wav", Path(tmp) / "out"
        audio.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1",
                   "-ar", "16000", str(wav)])
        audio.run(["whisper-cli", "-m", str(weights), "-l", lang, "-f", str(wav),
                   "-ocsv", "-of", str(base), "-np"])
        rows = list(csv.DictReader((base.with_suffix(".csv")).open(encoding="utf-8")))
    return [{"start": round(int(r["start"]) / 1000, 2), "end": round(int(r["end"]) / 1000, 2),
             "source": r["text"].strip()} for r in rows if r["text"].strip()]

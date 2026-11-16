"""Geração de voz. O motor entra por import tardio e por injeção: os testes nunca baixam modelo."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from . import audio, languages
from .errors import VoiceError
from .guard import Take, pick
from .vocab import apply_spoken

# texto, referência, idioma, arquivo de saída, temperatura
Synth = Callable[[str, Path, str, Path, float], None]

XTTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"


def xtts_synth(speed: float = 1.08) -> Synth:
    """XTTS-v2 local (CPU). Exige o extra `xtts` e o aceite da licença feito antes (consent)."""
    os.environ["COQUI_TOS_AGREED"] = "1"  # só chamado depois de consent.require_license
    try:
        from TTS.api import TTS
    except ImportError as exc:
        raise VoiceError(
            "Motor XTTS ausente. Instale com `uv sync --extra xtts` em engine/."
        ) from exc
    model = TTS(XTTS_MODEL).to("cpu")

    def synth(text: str, ref: Path, lang: str, out: Path, temperature: float) -> None:
        model.tts_to_file(text=text, speaker_wav=str(ref), language=lang, file_path=str(out),
                          speed=speed, temperature=temperature)

    return synth


@dataclass(frozen=True)
class Line:
    index: int
    text: str
    spoken: str
    path: Path
    seconds: float
    ok: bool  # False: todas as variações ficaram fora da duração esperada


def speak(lines: list[str], ref: Path, lang: str, outdir: Path, synth: Synth,
          mapping: dict[str, str] | None = None, takes: int = 3, speed: float = 1.08,
          base_temperature: float = 0.6, first_index: int = 1) -> list[Line]:
    """Uma fala por linha: aplica o vocabulário, gera N variações e fica com a melhor."""
    languages.require(lang)
    if takes < 1:
        raise VoiceError("--takes deve ser pelo menos 1.")
    outdir.mkdir(parents=True, exist_ok=True)
    result: list[Line] = []
    for number, text in enumerate(lines, start=first_index):
        text = text.strip()
        if not text:
            raise VoiceError(f"Linha {number} vazia.")
        spoken = apply_spoken(text, mapping or {})
        candidates: list[Take] = []
        for k in range(takes):
            raw = outdir / f".take-{number:02d}-{k}.wav"
            synth(spoken, ref, lang, raw, base_temperature + 0.05 * k)
            candidates.append(Take(raw, audio.wav_seconds(raw)))
        best, ok = pick(candidates, spoken, lang, speed)
        final = outdir / f"line-{number:02d}.wav"
        audio.trim_edges(best.path, final)
        for take in candidates:
            take.path.unlink(missing_ok=True)
        result.append(Line(number, text, spoken, final, round(audio.wav_seconds(final), 3), ok))
    return result

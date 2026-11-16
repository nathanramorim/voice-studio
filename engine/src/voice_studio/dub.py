"""Dublagem: segmentos com tempo + texto já traduzido -> voz clonada encaixada no vídeo."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import audio
from .errors import VoiceError
from .synth import Synth, speak

TOLERANCE = 0.15


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


def load_segments(path: Path) -> list[Segment]:
    """`[{"start": s, "end": s, "text": "..."}]`, em ordem e sem sobreposição."""
    if not path.is_file():
        raise VoiceError(f"Segmentos não encontrados: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VoiceError(f"Segmentos com JSON inválido: {exc}") from exc
    if not isinstance(raw, list) or not raw:
        raise VoiceError("Os segmentos devem ser uma lista não vazia.")
    segments, last_end = [], 0.0
    for i, item in enumerate(raw, start=1):
        try:
            start, end, text = float(item["start"]), float(item["end"]), str(item["text"]).strip()
        except (KeyError, TypeError, ValueError) as exc:
            raise VoiceError(f"Segmento {i}: precisa de start, end e text.") from exc
        if not text:
            raise VoiceError(f"Segmento {i} sem `text` (falta traduzir?).")
        if not 0 <= start < end:
            raise VoiceError(f"Segmento {i}: tempos inválidos ({start} -> {end}).")
        if start < last_end - 1e-6:
            raise VoiceError(f"Segmento {i} começa antes do fim do anterior.")
        segments.append(Segment(start, end, text))
        last_end = end
    return segments


def dub(video: Path, segments: list[Segment], ref: Path, lang: str, out: Path, synth: Synth,
        workdir: Path, mapping: dict[str, str] | None = None, takes: int = 3,
        keep_original: float = 0.0, max_up: float = 1.25) -> dict:
    """Gera cada fala, acelera (no máximo `max_up`) para caber e mixa no vídeo ou no áudio."""
    audio.check_output(audio.has_video(video), out)  # falha cedo, antes de gastar tempo no motor
    workdir.mkdir(parents=True, exist_ok=True)
    parts: list[tuple[Path, float]] = []
    report: list[dict] = []
    for i, seg in enumerate(segments, start=1):
        line = speak([seg.text], ref, lang, workdir / f"seg-{i:02d}", synth, mapping, takes,
                     first_index=1)[0]
        slot = seg.end - seg.start
        factor = audio.fit_factor(line.seconds, slot, max_up)
        path, seconds = line.path, line.seconds
        if factor > 1.0:
            fitted = line.path.with_name(f"fit-{i:02d}.wav")
            audio.speed_up(line.path, fitted, factor)
            path, seconds = fitted, round(line.seconds / factor, 3)
        room = (segments[i].start if i < len(segments) else seg.end + 1.0) - seg.start
        parts.append((path, seg.start))
        report.append({"segment": i, "slot": round(slot, 3), "seconds": seconds,
                       "speedup": round(factor, 3), "overflow": seconds > room + TOLERANCE,
                       "take_ok": line.ok})
    audio.mix_dub(video, parts, out, keep_original)
    return {"output": str(out), "segments": report,
            "overflow": [r["segment"] for r in report if r["overflow"]],
            "suspect_takes": [r["segment"] for r in report if not r["take_ok"]]}

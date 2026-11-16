"""Guarda de duração: o modelo às vezes alucina (fala de 3 s que sai com 10 s)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import languages

LOW, HIGH = 0.5, 1.6


def expected_seconds(text: str, lang: str, speed: float = 1.0) -> float:
    cps = languages.require(lang).cps * max(speed, 0.1)
    return max(len(text.strip()), 1) / cps


def is_suspect(duration: float, text: str, lang: str, speed: float = 1.0) -> bool:
    ratio = duration / expected_seconds(text, lang, speed)
    return not (LOW <= ratio <= HIGH)


@dataclass(frozen=True)
class Take:
    path: Path
    seconds: float


def pick(takes: list[Take], text: str, lang: str, speed: float = 1.0) -> tuple[Take, bool]:
    """Escolhe a variação mais próxima da duração esperada; `False` se todas são suspeitas."""
    if not takes:
        raise ValueError("sem variações para escolher")
    want = expected_seconds(text, lang, speed)
    good = [t for t in takes if not is_suspect(t.seconds, text, lang, speed)]
    pool = good or takes
    best = min(pool, key=lambda t: abs(t.seconds - want))
    return best, bool(good)

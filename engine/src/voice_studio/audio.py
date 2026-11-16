"""Áudio com ffmpeg (sempre lista de argumentos, nunca shell) e wave."""

from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path

from .errors import VoiceError

TRIM = (
    "silenceremove=start_periods=1:start_threshold=-42dB,areverse,"
    "silenceremove=start_periods=1:start_threshold=-42dB,areverse,apad=pad_dur=0.1"
)


def run(cmd: list[str]) -> None:
    if shutil.which(cmd[0]) is None:
        raise VoiceError(f"`{cmd[0]}` não encontrado. Instale (ex.: brew install ffmpeg).")
    done = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise VoiceError(f"{cmd[0]} falhou: {done.stderr.strip()[-400:]}")


def wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / wav.getframerate()


def trim_edges(src: Path, dst: Path) -> None:
    """Corta o silêncio só das pontas (o corte no meio come palavras)."""
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", TRIM, "-ac", "1", str(dst)])


def extract_sample(video: Path, out: Path, start: float = 0.0, duration: float = 28.0) -> None:
    """Amostra de referência: mono 22,05 kHz, sem graves de ruído e com volume nivelado."""
    if not video.is_file():
        raise VoiceError(f"Arquivo não encontrado: {video}")
    if not 6.0 <= duration <= 30.0:
        raise VoiceError("A amostra deve ter de 6 a 30 s.")
    run([
        "ffmpeg", "-v", "error", "-y", "-ss", f"{start}", "-t", f"{duration}", "-i", str(video),
        "-vn", "-ac", "1", "-ar", "22050",
        "-af", "highpass=f=70,afftdn=nf=-28,loudnorm=I=-20", str(out),
    ])


def fit_factor(actual: float, target: float, max_up: float = 1.25) -> float:
    """Fator de aceleração para caber no tempo: nunca desacelera, nunca passa de `max_up`."""
    if target <= 0:
        raise ValueError("duração-alvo inválida")
    if actual <= target:
        return 1.0
    return min(actual / target, max_up)


def speed_up(src: Path, dst: Path, factor: float) -> None:
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-filter:a", f"atempo={factor:.4f}",
         str(dst)])


def mix_dub(video: Path, parts: list[tuple[Path, float]], out: Path,
            keep_original: float = 0.0) -> None:
    """Põe cada trecho na sua posição e troca (ou abaixa) o áudio original do vídeo."""
    if not parts:
        raise VoiceError("Nada para mixar.")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video)]
    for path, _ in parts:
        cmd += ["-i", str(path)]
    filters, labels = [], []
    for i, (_, start) in enumerate(parts, start=1):
        ms = round(start * 1000)
        filters.append(f"[{i}:a]adelay={ms}|{ms}[d{i}]")
        labels.append(f"[d{i}]")
    if keep_original > 0:
        filters.append(f"[0:a]volume={keep_original}[o]")
        labels.append("[o]")
    filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,alimiter=limit=0.95[m]")
    cmd += ["-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[m]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)]
    run(cmd)

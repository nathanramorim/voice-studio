import math
import struct
import wave
from pathlib import Path

import pytest


def write_wav(path: Path, seconds: float, rate: int = 24000) -> Path:
    """Seno de `seconds` segundos, mono 16 bits (sem depender de ffmpeg)."""
    frames = int(seconds * rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"".join(
            struct.pack("<h", int(8000 * math.sin(2 * math.pi * 220 * i / rate)))
            for i in range(frames)))
    return path


@pytest.fixture
def ref(tmp_path):
    return write_wav(tmp_path / "ref.wav", 1.0)


@pytest.fixture(autouse=True)
def no_trim(monkeypatch):
    """Os testes de domínio não precisam de ffmpeg: o corte de pontas vira cópia."""
    import shutil

    from voice_studio import audio

    monkeypatch.setattr(audio, "trim_edges", lambda src, dst: shutil.copyfile(src, dst))

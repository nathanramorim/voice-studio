"""Dublagem de entrada só áudio ou com vídeo (ffmpeg real; ignorado se não existir)."""

import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import write_wav
from typer.testing import CliRunner

from voice_studio import audio, cli, dub
from voice_studio import synth as synth_mod
from voice_studio.errors import VoiceError

needs_ffmpeg = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe ausentes")

SEGS = [dub.Segment(0.0, 2.0, "Hello there my friend"), dub.Segment(2.2, 4.0, "See you soon")]


def fake_synth(text, ref, lang, out, temperature):
    write_wav(out, 1.2)


def make_video(path):
    """Vídeo sintético de 4 s (imagem preta + seno), sem arquivo de mídia no repositório."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=4",
                    "-f", "lavfi", "-i", "sine=frequency=220:duration=4", "-c:v", "mpeg4",
                    "-c:a", "aac", "-shortest", str(path)], check=True)
    return path


def probe(path, kind):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", kind[0], "-show_entries",
                          "stream=codec_type", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def run_dub(src, out, tmp_path, keep=0.0):
    return dub.dub(src, SEGS, src, "en", out, fake_synth, tmp_path / "w", takes=1,
                   keep_original=keep)


@needs_ffmpeg
@pytest.mark.parametrize("saida", ["dublado.m4a", "dublado.wav"])
def test_audio_entrada_wav_gera_saida_de_audio(tmp_path, saida):
    src = write_wav(tmp_path / "in.wav", 4.0)
    assert audio.has_video(src) is False
    out = tmp_path / saida
    report = run_dub(src, out, tmp_path)
    assert out.is_file() and probe(out, "a") == "audio" and probe(out, "v") == ""
    assert set(report) == {"output", "segments", "overflow", "suspect_takes"}


@needs_ffmpeg
def test_audio_mantem_original_baixo(tmp_path):
    src = write_wav(tmp_path / "in.wav", 4.0)
    run_dub(src, tmp_path / "d.m4a", tmp_path, keep=0.2)
    assert (tmp_path / "d.m4a").is_file()


@needs_ffmpeg
def test_video_mantem_saida_em_video(tmp_path):
    src = make_video(tmp_path / "in.mp4")
    assert audio.has_video(src) is True
    out = tmp_path / "dublado.mp4"
    report = run_dub(src, out, tmp_path)
    assert probe(out, "v") == "video" and probe(out, "a") == "audio"
    assert set(report) == {"output", "segments", "overflow", "suspect_takes"}


@needs_ffmpeg
def test_extensao_mp4_para_entrada_so_audio_falha_cedo(tmp_path):
    src = write_wav(tmp_path / "in.wav", 4.0)
    calls = []

    def spy(*args):
        calls.append(args)

    with pytest.raises(VoiceError, match="só áudio.*\\.m4a ou \\.wav"):
        dub.dub(src, SEGS, src, "en", tmp_path / "o.mp4", spy, tmp_path / "w", takes=1)
    assert calls == [] and not (tmp_path / "o.mp4").exists()


@needs_ffmpeg
def test_extensao_de_audio_para_entrada_com_video_falha(tmp_path):
    src = make_video(tmp_path / "in.mp4")
    with pytest.raises(VoiceError, match="tem vídeo"):
        run_dub(src, tmp_path / "o.m4a", tmp_path)


def test_extensao_regras_sem_ffmpeg():
    audio.check_output(False, Path("a.m4a"))
    audio.check_output(False, Path("a.WAV"))
    audio.check_output(True, Path("a.mp4"))
    with pytest.raises(VoiceError, match="só áudio"):
        audio.check_output(False, Path("a.mp4"))
    with pytest.raises(VoiceError, match="tem vídeo"):
        audio.check_output(True, Path("a.wav"))


def test_audio_entrada_inexistente_e_erro_claro(tmp_path):
    with pytest.raises(VoiceError, match="não encontrado"):
        audio.has_video(tmp_path / "nada.wav")


@needs_ffmpeg
def test_audio_cli_dub_aceita_entrada_de_audio(tmp_path, monkeypatch):
    src = write_wav(tmp_path / "in.wav", 4.0)
    segs = tmp_path / "s.json"
    segs.write_text('[{"start":0,"end":2,"text":"Hello there my friend"}]', encoding="utf-8")
    monkeypatch.setattr(synth_mod, "xtts_synth", lambda speed=1.08: fake_synth)
    out = tmp_path / "d.m4a"
    res = CliRunner().invoke(cli.app, ["dub", str(src), str(segs), "--ref", str(src),
                                       "--confirm-own-voice", "--accept-cpml", "--out", str(out),
                                       "--takes", "1"])
    assert res.exit_code == 0, res.output
    assert out.is_file()
    bad = CliRunner().invoke(cli.app, ["dub", str(src), str(segs), "--ref", str(src),
                                       "--confirm-own-voice", "--accept-cpml",
                                       "--out", str(tmp_path / "d.mp4")])
    assert bad.exit_code == 1 and "só áudio" in bad.output

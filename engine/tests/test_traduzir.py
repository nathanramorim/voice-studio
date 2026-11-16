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


# ---- feat-01-06: comando `traduzir` em duas fases -------------------------------------------

import json

from test_falar import Recorder, make_profile

from voice_studio import falar, traduzir

FAKE_TRANSCRIPT = [{"start": 0.0, "end": 2.0, "source": "Olá meu amigo"},
                   {"start": 2.2, "end": 4.0, "source": "Até logo"}]


def fake_transcriber(entrada, model, lang):
    return [dict(s) for s in FAKE_TRANSCRIPT]


def translated(tmp_path, texts=("Hello there my friend", "See you soon")):
    path = tmp_path / "seg.json"
    path.write_text(json.dumps([dict(s, text=t) for s, t in zip(FAKE_TRANSCRIPT, texts)]),
                    encoding="utf-8")
    return path


def mock_audio(monkeypatch):
    """Dublagem sem ffmpeg: o mix vira um arquivo vazio e a entrada conta como só áudio."""
    monkeypatch.setattr(audio, "has_video", lambda p: False)
    monkeypatch.setattr(audio, "mix_dub", lambda v, parts, out, keep: out.write_bytes(b"x"))
    monkeypatch.setattr(audio, "speed_up", lambda s, d, f: d.write_bytes(s.read_bytes()))


def test_fases_prepare_grava_segmentos_com_text_vazio(tmp_path, ref):
    _, perfil = make_profile(tmp_path, ref)
    destino = tmp_path / "seg.json"
    traduzir.prepare(ref, perfil, "pt", "en", None, destino, fake_transcriber)
    rows = json.loads(destino.read_text(encoding="utf-8"))
    assert [r["source"] for r in rows] == ["Olá meu amigo", "Até logo"]
    assert all(r["text"] == "" for r in rows)
    with pytest.raises(VoiceError, match="já existe"):
        traduzir.prepare(ref, perfil, "pt", "en", None, destino, fake_transcriber)


def test_fases_render_gera_audio_dublado_com_vocabulario_do_destino(tmp_path, ref, monkeypatch):
    mock_audio(monkeypatch)
    _, perfil = make_profile(tmp_path, ref, {"en": {"IA": "AI"}, "pt": {"IA": "IÁ"}})
    seg = translated(tmp_path, ("Hello IA friend", "See you soon"))
    synth = Recorder()
    out = tmp_path / "d.m4a"
    report = traduzir.render(ref, seg, perfil, "en", out, synth, takes=1)
    assert out.is_file() and report["validated"] is True
    assert synth.calls[0] == ("Hello AI friend", perfil["amostra_path"], "en")
    assert set(report) >= {"overflow", "suspect_takes", "validated"}


def test_fases_cli_ponta_a_ponta(tmp_path, ref, monkeypatch):
    mock_audio(monkeypatch)
    base, _ = make_profile(tmp_path, ref)
    monkeypatch.setattr(traduzir.transcribe, "transcribe", fake_transcriber)
    seg = tmp_path / "seg.json"
    args = ["traduzir", str(ref), "--perfil", "nathan", "--para", "en", "--perfis-dir", str(base)]
    res = CliRunner().invoke(cli.app, [*args, "--out", str(seg)])
    assert res.exit_code == 0 and "--segmentos" in res.output, res.output
    rows = json.loads(seg.read_text(encoding="utf-8"))
    for r, t in zip(rows, ("Hello there my friend", "See you soon")):
        r["text"] = t
    seg.write_text(json.dumps(rows), encoding="utf-8")
    monkeypatch.delenv("VOICE_STUDIO_ACCEPT_CPML", raising=False)
    monkeypatch.setattr(synth_mod, "xtts_synth", lambda speed=1.08: Recorder())
    out = tmp_path / "d.m4a"
    res = CliRunner().invoke(cli.app, [*args, "--segmentos", str(seg), "--accept-cpml",
                                       "--out", str(out), "--takes", "1"])
    assert res.exit_code == 0, res.output
    assert out.is_file() and (tmp_path / "report.json").is_file()


def test_perfil_ausente_ou_sem_consentimento_falha_antes_do_motor(tmp_path, ref, monkeypatch):
    base, _ = make_profile(tmp_path, ref)
    touched = []
    monkeypatch.setattr(synth_mod, "xtts_synth", lambda speed=1.08: touched.append(1))
    seg = translated(tmp_path)
    args = ["--para", "en", "--perfis-dir", str(base), "--segmentos", str(seg), "--accept-cpml"]
    res = CliRunner().invoke(cli.app, ["traduzir", str(ref), "--perfil", "ninguem", *args])
    assert res.exit_code == 1 and not touched
    pfile = base / "nathan" / "perfil.json"
    data = json.loads(pfile.read_text(encoding="utf-8"))
    data["consentimento"] = False
    data.pop("consent", None)
    pfile.write_text(json.dumps(data), encoding="utf-8")
    res = CliRunner().invoke(cli.app, ["traduzir", str(ref), "--perfil", "nathan", *args])
    assert res.exit_code == 1 and not touched
    res = CliRunner().invoke(cli.app, ["traduzir", str(ref), "--para", "en"])
    assert res.exit_code == 2  # --perfil obrigatório (erro de uso do Typer)


@pytest.mark.parametrize("caso", ["traducao-faltando"])
def test_segmento_sem_text_aponta_o_numero_antes_do_motor(tmp_path, ref, monkeypatch, caso):
    base, perfil = make_profile(tmp_path, ref)
    seg = translated(tmp_path, ("Hello there", "  "))
    synth = Recorder()
    with pytest.raises(VoiceError, match="Segmento 2"):
        traduzir.render(ref, seg, perfil, "en", tmp_path / "d.m4a", synth, takes=1)
    assert synth.calls == []
    touched = []
    monkeypatch.setattr(synth_mod, "xtts_synth", lambda speed=1.08: touched.append(1))
    res = CliRunner().invoke(cli.app, ["traduzir", str(ref), "--perfil", "nathan", "--para", "en",
                                       "--perfis-dir", str(base), "--segmentos", str(seg),
                                       "--accept-cpml"])
    assert res.exit_code == 1 and "Segmento 2" in res.output and not touched


def test_idioma_fora_do_catalogo_falha_antes_do_motor(tmp_path, ref, monkeypatch):
    base, perfil = make_profile(tmp_path, ref)
    with pytest.raises(VoiceError, match="não suportado"):
        traduzir.prepare(ref, perfil, "pt", "xx", None, tmp_path / "s.json", fake_transcriber)
    touched = []
    monkeypatch.setattr(synth_mod, "xtts_synth", lambda speed=1.08: touched.append(1))
    res = CliRunner().invoke(cli.app, ["traduzir", str(ref), "--perfil", "nathan", "--para", "xx",
                                       "--perfis-dir", str(base), "--segmentos",
                                       str(translated(tmp_path)), "--accept-cpml"])
    assert res.exit_code == 1 and "não suportado" in res.output and not touched


def test_idioma_nao_validado_marca_relatorio_e_avisa(tmp_path, ref, monkeypatch):
    mock_audio(monkeypatch)
    _, perfil = make_profile(tmp_path, ref)
    report = traduzir.render(ref, translated(tmp_path, ("Hola amigo mío", "Hasta luego")),
                             perfil, "es", tmp_path / "d.m4a", Recorder(), takes=1)
    assert report["validated"] is False
    assert any("não teve a qualidade verificada" in a for a in traduzir.avisos("es", report))
    assert traduzir.avisos("en", {"overflow": [], "suspect_takes": []}) == []


def test_idioma_cli_es_avisa_e_overflow_e_suspeita_continuam(tmp_path, ref, monkeypatch):
    mock_audio(monkeypatch)
    base, _ = make_profile(tmp_path, ref)
    monkeypatch.setattr(synth_mod, "xtts_synth", lambda speed=1.08: Recorder(seconds=30.0))
    res = CliRunner().invoke(cli.app, ["traduzir", str(ref), "--perfil", "nathan", "--para", "es",
                                       "--perfis-dir", str(base), "--segmentos",
                                       str(translated(tmp_path)), "--accept-cpml", "--takes", "1",
                                       "--out", str(tmp_path / "d.m4a")])
    rep = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert res.exit_code == 2 and rep["validated"] is False
    assert rep["overflow"] and rep["suspect_takes"]
    assert "não teve a qualidade verificada" in res.output and "encurte" in res.output


def test_takes_zero_cai_no_erro_de_speak_em_falar_e_traduzir(tmp_path, ref, monkeypatch):
    mock_audio(monkeypatch)
    _, perfil = make_profile(tmp_path, ref, ajustes={"takes": 2})
    with pytest.raises(VoiceError, match="pelo menos 1"):
        falar.run(["Olá mundo agora"], perfil, "pt", tmp_path / "o", Recorder(), takes=0)
    with pytest.raises(VoiceError, match="pelo menos 1"):
        traduzir.render(ref, translated(tmp_path), perfil, "en", tmp_path / "d.m4a", Recorder(),
                        takes=0)


def test_perfil_e_ref_juntos_falha_em_falar(tmp_path, ref):
    with pytest.raises(VoiceError, match="não os dois"):
        falar.resolve("nathan", ref, True)

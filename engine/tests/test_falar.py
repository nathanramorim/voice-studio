import json
import shutil

import pytest
from conftest import write_wav
from typer.testing import CliRunner

from voice_studio import cli, falar, profile
from voice_studio import synth as synth_mod
from voice_studio.errors import VoiceError


def fake_extract(origem, destino, start, duration):
    shutil.copyfile(origem, destino)


def make_profile(tmp_path, ref, vocab=None, ajustes=None):
    base = tmp_path / "perfis"
    profile.create("nathan", ref, True, base, extract=fake_extract, ajustes=ajustes)
    for lang, mapa in (vocab or {}).items():
        arq = tmp_path / f"v-{lang}.json"
        arq.write_text(json.dumps(mapa), encoding="utf-8")
        profile.set_vocabulary("nathan", lang, arq, base)
    return base, profile.load("nathan", base)


class Recorder:
    """Sintetizador simulado: grava o que o motor recebeu e escreve um seno."""

    def __init__(self, seconds=1.2):
        self.calls, self.seconds = [], seconds

    def __call__(self, text, ref, lang, out, temperature):
        self.calls.append((text, str(ref), lang))
        write_wav(out, self.seconds)


def test_texto_chega_ao_motor_com_vocabulario_e_amostra(tmp_path, ref):
    _, perfil = make_profile(tmp_path, ref, {"pt": {"IA": "IÁ"}, "en": {"IA": "AI"}})
    synth = Recorder(seconds=1.2)  # ~1,2 s esperados para 20 caracteres em pt
    report = falar.run(["Vamos usar a IA hoje"], perfil, "pt", tmp_path / "o", synth, takes=1)
    assert synth.calls == [("Vamos usar a IÁ hoje", perfil["amostra_path"], "pt")]
    assert set(report[0]) == {"linha", "arquivo", "segundos", "ok", "validated", "falado"}
    assert report[0]["falado"] == "Vamos usar a IÁ hoje" and report[0]["validated"] is True
    assert report[0]["ok"] is True
    assert (tmp_path / "o" / report[0]["arquivo"]).is_file()


def test_texto_usa_takes_e_velocidade_do_perfil(tmp_path, ref):
    _, perfil = make_profile(tmp_path, ref, ajustes={"takes": 2})
    synth = Recorder()
    falar.run(["Olá mundo agora"], perfil, "pt", tmp_path / "o", synth)
    assert len(synth.calls) == 2


def test_ajustes_invalidos_sao_rejeitados(tmp_path, ref):
    for bad in ({"velocidade": 0}, {"velocidade": "x"}, {"takes": 0}, {"takes": 1.5},
                {"takes": True}, {"volume": 1}):
        with pytest.raises(VoiceError):
            profile.check_adjusts(bad)
    with pytest.raises(VoiceError, match="desconhecidos"):
        make_profile(tmp_path, ref, ajustes={"volume": 1})
    base, _ = make_profile(tmp_path, ref)
    file = base / "nathan" / "perfil.json"
    data = json.loads(file.read_text(encoding="utf-8"))
    data["ajustes"] = {"velocidade": -1, "takes": 3}
    file.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(VoiceError, match="velocidade"):
        profile.load("nathan", base)


def test_consentimento_sem_perfil_nem_ref_falha(tmp_path, ref):
    with pytest.raises(VoiceError, match="--perfil"):
        falar.resolve(None, None, False)
    with pytest.raises(VoiceError, match="confirm-own-voice"):
        falar.resolve(None, ref, False)
    assert falar.resolve(None, ref, True)["amostra_path"] == str(ref)


def test_consentimento_sem_cpml_falha_antes_do_motor(tmp_path, ref, monkeypatch):
    base, _ = make_profile(tmp_path, ref)
    monkeypatch.delenv("VOICE_STUDIO_ACCEPT_CPML", raising=False)
    touched = []
    monkeypatch.setattr(synth_mod, "xtts_synth", lambda speed=1.08: touched.append(1))
    res = CliRunner().invoke(cli.app, ["falar", "Olá", "--perfil", "nathan",
                                       "--perfis-dir", str(base), "--out", str(tmp_path / "o")])
    assert res.exit_code == 1 and "CPML" in res.output and not touched
    res = CliRunner().invoke(cli.app, ["falar", "Olá", "--ref", str(ref), "--accept-cpml"])
    assert res.exit_code == 1 and "confirm-own-voice" in res.output and not touched
    res = CliRunner().invoke(cli.app, ["falar", "Olá", "--accept-cpml"])
    assert res.exit_code == 1 and "--perfil" in res.output and not touched


def test_cli_falar_ponta_a_ponta_com_motor_simulado(tmp_path, ref, monkeypatch):
    base, _ = make_profile(tmp_path, ref, {"pt": {"IA": "IÁ"}})
    synth = Recorder()
    monkeypatch.setattr(synth_mod, "xtts_synth", lambda speed=1.08: synth)
    out = tmp_path / "o"
    res = CliRunner().invoke(cli.app, ["falar", "Vamos usar a IA hoje", "--perfil", "nathan",
                                       "--perfis-dir", str(base), "--accept-cpml",
                                       "--out", str(out), "--takes", "1"])
    assert res.exit_code == 0, res.output
    assert json.loads((out / "report.json").read_text(encoding="utf-8"))[0]["falado"].endswith("hoje")
    assert synth.calls[0][0] == "Vamos usar a IÁ hoje"


@pytest.mark.parametrize("lang", ["es", "fr"], ids=["nao-validado-es", "nao-validado-fr"])
def test_idioma_nao_validado_avisa_e_marca(tmp_path, ref, lang):
    _, perfil = make_profile(tmp_path, ref)
    report = falar.run(["Hola, ¿cómo estás hoy?"], perfil, lang, tmp_path / "o", Recorder(), 1)
    assert report[0]["validated"] is False
    assert any("não teve a qualidade verificada" in a for a in falar.avisos(lang, report))
    assert falar.avisos("pt", [{"linha": 1, "ok": True}]) == []


def test_suspeita_todas_variacoes_resulta_em_ok_false_e_aviso(tmp_path, ref):
    _, perfil = make_profile(tmp_path, ref)
    synth = Recorder(seconds=30.0)  # absurdamente longa para o texto
    report = falar.run(["Oi"], perfil, "pt", tmp_path / "o", synth, takes=2)
    assert report[0]["ok"] is False
    assert any("Linhas [1]" in a for a in falar.avisos("pt", report))


def test_suspeita_cli_sai_com_codigo_2(tmp_path, ref, monkeypatch):
    base, _ = make_profile(tmp_path, ref)
    monkeypatch.setattr(synth_mod, "xtts_synth", lambda speed=1.08: Recorder(seconds=30.0))
    res = CliRunner().invoke(cli.app, ["falar", "Oi", "--perfil", "nathan", "--perfis-dir",
                                       str(base), "--accept-cpml", "--out", str(tmp_path / "o"),
                                       "--takes", "1"])
    assert res.exit_code == 2 and "Linhas [1]" in res.output


def test_texto_ou_arquivo(tmp_path):
    arq = tmp_path / "f.json"
    arq.write_text(json.dumps({"lines": ["a b", "c d"]}), encoding="utf-8")
    assert falar.load_texts(None, arq) == ["a b", "c d"]
    with pytest.raises(VoiceError):
        falar.load_texts("x", arq)
    with pytest.raises(VoiceError):
        falar.load_texts(None, None)

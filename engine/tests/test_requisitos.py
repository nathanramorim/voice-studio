"""scripts/requisitos.py: checar e instalar, sem tocar a máquina (tudo injetado)."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
ARQ = RAIZ / "scripts" / "requisitos.py"
spec = importlib.util.spec_from_file_location("requisitos", ARQ)
req = importlib.util.module_from_spec(spec)
sys.modules["requisitos"] = req
spec.loader.exec_module(req)

VERSOES = {
    "uv": "uv 0.9.7 (abc)", "brew": "Homebrew 4.0.0", "ffmpeg": "ffmpeg version 8.0.1",
    "ffprobe": "ffprobe version 8.0.1", "whisper-cli": "whisper 1.9.5",
}


def amb(tmp_path, tem=("brew", "uv", "ffmpeg", "ffprobe", "whisper-cli"), env=None, repo=None,
        sistema="Darwin", maquina="arm64", disco=30.0, python_ok=True):
    def executar(args):
        if args[:3] == ["uv", "python", "find"]:
            return "/x/python3.11" if python_ok else None
        if args[0] == "/x/python3.11":
            return "Python 3.11.14"
        return VERSOES.get(args[0]) if args[0] in tem else None

    def which(nome):
        return f"/bin/{nome}" if nome in tem else None

    return req.Ambiente(home=tmp_path, env=env or {}, repo=repo, sistema=sistema, maquina=maquina,
                        executar=executar, which=which, disco_livre_gb=lambda _: disco)


def por_nome(itens):
    return {i.nome: i for i in itens}


def test_tudo_instalado_sem_falta_obrigatoria(tmp_path):
    itens = req.checar(amb(tmp_path))
    assert not req.falta_obrigatorio(itens)
    d = por_nome(itens)
    assert d["ffmpeg"].versao == "8.0.1" and d["uv"].versao == "0.9.7"
    assert d["python-3.11"].estado == req.OK


def test_falta_ffmpeg_vira_faltando_com_brew(tmp_path):
    d = por_nome(req.checar(amb(tmp_path, tem=("brew", "uv"))))
    assert d["ffmpeg"].estado == req.FALTANDO
    assert d["ffmpeg"].comandos == [["brew", "install", "ffmpeg"]]
    assert d["whisper-cli"].estado == req.OPCIONAL and not d["whisper-cli"].obrigatorio


def test_python_no_apple_silicon_pede_o_arm64(tmp_path):
    d = por_nome(req.checar(amb(tmp_path, python_ok=False)))
    assert d["python-3.11"].comandos == [["uv", "python", "install", req.PYTHON_ARM]]
    d = por_nome(req.checar(amb(tmp_path, python_ok=False, sistema="Linux", maquina="x86_64")))
    assert d["python-3.11"].comandos == [["uv", "python", "install", "3.11"]]


def test_modelo_whisper_respeita_a_variavel(tmp_path):
    modelo = tmp_path / "m.bin"
    d = por_nome(req.checar(amb(tmp_path, env={"VOICE_STUDIO_WHISPER_MODEL": str(modelo)})))
    assert d["modelo-whisper"].estado == req.OPCIONAL
    assert d["modelo-whisper"].comandos[0][-2:] == [str(modelo), req.URL_WHISPER]
    modelo.write_bytes(b"x")
    d = por_nome(req.checar(amb(tmp_path, env={"VOICE_STUDIO_WHISPER_MODEL": str(modelo)})))
    assert d["modelo-whisper"].estado == req.OK


def test_modelo_xtts_e_perfil_sao_do_usuario_e_sem_comando(tmp_path):
    d = por_nome(req.checar(amb(tmp_path)))
    for nome in ("modelo-xtts", "perfil-de-voz"):
        assert d[nome].tipo == req.SEU and d[nome].comandos == []
    assert "--accept-cpml" in d["modelo-xtts"].explicacao
    (tmp_path / "tts" / req.XTTS_PASTA).mkdir(parents=True)
    d = por_nome(req.checar(amb(tmp_path, env={"TTS_HOME": str(tmp_path)})))
    assert d["modelo-xtts"].estado == req.OK


def test_motor_com_clone_mostra_uv_sync_com_python_arm(tmp_path):
    d = por_nome(req.checar(amb(tmp_path, repo=tmp_path)))
    cmd = d["motor-xtts"].comandos[0]
    assert cmd[:2] == ["uv", "sync"] and req.PYTHON_ARM in cmd and cmd[-2:] == ["--extra", "xtts"]
    d = por_nome(req.checar(amb(tmp_path, repo=None)))
    assert d["motor-xtts"].comandos == []


def test_json_e_codigo_de_saida(tmp_path, capsys):
    assert req.main(["checar", "--json"], amb(tmp_path, tem=("brew", "uv"))) == 1
    dados = json.loads(capsys.readouterr().out)
    assert dados["ok"] is False
    campos = {"nome", "estado", "versao", "obrigatorio", "tipo", "comandos", "explicacao"}
    assert all(set(r) == campos for r in dados["requisitos"])
    assert req.main(["checar"], amb(tmp_path)) == 0
    assert "Requisito" in capsys.readouterr().out


def test_instalar_sem_tty_so_mostra(tmp_path):
    rodados, linhas = [], []
    codigo = req.instalar(amb(tmp_path, tem=("brew", "uv")), interativo=False,
                          rodar=lambda c: rodados.append(c) or 0, saida=linhas.append)
    assert rodados == [] and codigo == 1
    assert any("brew install ffmpeg" in linha for linha in linhas)
    assert any("Isto é com você" in linha for linha in linhas)


def test_instalar_pergunta_e_respeita_o_nao(tmp_path):
    rodados, perguntas = [], []
    req.instalar(amb(tmp_path, tem=("brew", "uv")), interativo=True,
                 perguntar=lambda p: perguntas.append(p) or False,
                 rodar=lambda c: rodados.append(c) or 0, saida=lambda _: None)
    assert perguntas and rodados == []


def test_instalar_sim_roda_uma_vez_e_nunca_itens_do_usuario(tmp_path):
    rodados = []
    req.instalar(amb(tmp_path, tem=("brew", "uv")), sim=True,
                 rodar=lambda c: rodados.append(c) or 0, saida=lambda _: None)
    assert rodados.count(["brew", "install", "ffmpeg"]) == 1
    texto = json.dumps(rodados)
    for proibido in ("--accept-cpml", "--confirm-own-voice", "ACCEPT_CPML", "zshrc"):
        assert proibido not in texto


def test_instalar_sem_pendencia_nao_faz_nada(tmp_path):
    (tmp_path / ".voice-studio" / "perfis" / "a").mkdir(parents=True)
    (tmp_path / ".voice-studio" / "perfis" / "a" / "perfil.json").write_text("{}")
    (tmp_path / "Library" / "Application Support" / "tts" / req.XTTS_PASTA).mkdir(parents=True)
    modelo = tmp_path / ".cache" / "whisper" / "ggml-small.bin"
    modelo.parent.mkdir(parents=True)
    modelo.write_bytes(b"x")
    (tmp_path / "venv" / "lib" / "python3.11" / "site-packages" / "TTS").mkdir(parents=True)
    linhas = []
    env = {"VOICE_STUDIO_WHISPER_MODEL": str(modelo), "UV_PROJECT_ENVIRONMENT": str(tmp_path / "venv")}
    a = amb(tmp_path, env=env, repo=tmp_path)
    assert req.instalar(a, sim=True, rodar=pytest.fail, saida=linhas.append) == 0
    assert linhas == ["Nada a instalar: tudo ok."]


def test_readme_tem_o_prompt_para_a_ia_antes_da_instalacao():
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")
    requisitos = texto.split("## Requisitos", 1)[1].split("\n## ", 1)[0]
    assert "Cole isto na sua IA antes de instalar" in requisitos
    assert "scripts/requisitos.py checar" in requisitos and "scripts/requisitos.py instalar" in requisitos
    assert "Não aceite licenças nem declarações por mim" in requisitos
    assert texto.index("Cole isto na sua IA") < texto.index("## Instalação")

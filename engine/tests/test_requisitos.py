"""Requisitos pelo motor vendorizado (scripts/requisitos.py, skills.lock): leve, sem rede, sem instalar."""

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
TOML = RAIZ / "requisitos.toml"
spec = importlib.util.spec_from_file_location("requisitos", RAIZ / "scripts" / "requisitos.py")
req = importlib.util.module_from_spec(spec)
sys.modules["requisitos"] = req
spec.loader.exec_module(req)


def ambiente(sistema, arch="x64", programas=(), **extra):
    """Máquina falsa: só `programas` existem no PATH; nada roda de verdade."""
    return req.Ambiente(sistema=sistema, arch=arch, home=Path("/casa"), env=extra.pop("env", {}),
                        which=lambda n: f"/bin/{n}" if n in programas else None,
                        executar=lambda argv: (127, ""), rodar=lambda argv: 0,
                        disco_livre_gb=lambda p: 100.0, memoria_gb=lambda: 16.0, **extra)


def itens():
    return {i.id: i for i in req.carregar(str(TOML))[1]}


def test_copia_do_motor_bate_com_o_skills_lock():
    lock = json.loads((RAIZ / "skills.lock").read_text(encoding="utf-8"))["skills"][0]
    assert lock["ref"] == "v0.1.0" and lock["commit"].startswith("93abe08")
    for destino, sha in lock["arquivos"].items():
        assert hashlib.sha256((RAIZ / destino).read_bytes()).hexdigest() == sha, destino


def test_receita_valida_nos_tres_sistemas(capsys):
    assert req.main(["--arquivo", str(TOML), "validar"]) == 0
    assert "macos, linux, windows" in capsys.readouterr().out


def test_checar_json_nesta_maquina(capsys):
    codigo = req.main(["--arquivo", str(TOML), "checar", "--json"])
    dados = json.loads(capsys.readouterr().out)
    assert codigo in (0, 1)
    assert {r["id"] for r in dados["requisitos"]} == set(itens())


def test_readme_traz_exatamente_o_prompt_do_motor(capsys):
    assert req.main(["--arquivo", str(TOML), "prompt"]) == 0
    bloco = capsys.readouterr().out.strip()
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    assert bloco in readme
    assert readme.index(bloco) < readme.index("## Instalação")
    assert "gh repo clone nathanramorim/voice-studio" in bloco


@pytest.mark.parametrize("sistema,arch", [("macos", "arm64"), ("macos", "x64"), ("linux", "x64"),
                                          ("linux", "arm64"), ("windows", "x64"), ("windows", "arm64")])
def test_toda_maquina_sem_gerenciador_tem_receita(sistema, arch):
    """Homebrew, winget e apt nunca são pré-requisito: sem nenhum, todo item ainda diz o que fazer."""
    amb = ambiente(sistema, arch)
    for item in itens().values():
        receita, _ = req.escolher_receita(item, amb)
        assert receita is not None, f"{item.id} sem receita em {sistema} {arch}"


def test_ninguem_aceita_licenca_nem_declara_a_voz_pela_pessoa():
    d = itens()
    for nome in ("licenca-xtts", "amostra-e-consentimento", "aprovar-voz"):
        assert d[nome].tipo == "pessoa"
    texto = TOML.read_text(encoding="utf-8")
    comandos = re.findall(r"comandos = (\[\[.*\]\])", texto)
    assert comandos and not any("accept-cpml" in c or "confirm-own-voice" in c for c in comandos)


def test_windows_arm64_sem_pytorch_e_apple_silicon_com_python_arm64():
    d = itens()
    r, _ = req.escolher_receita(d["motor-xtts"], ambiente("windows", "arm64"))
    assert "WSL" in r["nao_suportado"]
    r, _ = req.escolher_receita(d["python-3-11"], ambiente("macos", "arm64"))
    assert r["comandos"] == [["uv", "python", "install", "cpython-3.11-macos-aarch64-none"]]

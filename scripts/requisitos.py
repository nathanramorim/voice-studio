#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Confere e instala os requisitos do voice-studio (só biblioteca padrão; roda antes do clone).

Uso:
  uv run scripts/requisitos.py checar [--json]   # lista ok/faltando; código 1 se faltar algo obrigatório
  uv run scripts/requisitos.py instalar [--sim]  # mostra o comando de cada item que falta;
                                                 # pergunta antes de rodar; com --sim roda sem perguntar

Antes do clone:
  uv run https://raw.githubusercontent.com/nathanramorim/voice-studio/main/scripts/requisitos.py checar

Nunca aceita licença nem declaração pelo usuário (`--accept-cpml`, `--confirm-own-voice`),
nunca mexe em chave ou segredo e nunca edita o ~/.zshrc: esses itens são do tipo "seu" e só
são explicados.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

OK, FALTANDO, OPCIONAL = "ok", "faltando", "opcional"
SISTEMA, PROJETO, DOWNLOAD, SEU = "sistema", "projeto", "download", "seu"

UV_MINIMO = (0, 5)
PYTHON_ARM = "cpython-3.11-macos-aarch64-none"
URL_WHISPER = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
XTTS_PASTA = "tts_models--multilingual--multi-dataset--xtts_v2"
DISCO_MIN_GB = 4


@dataclass
class Item:
    nome: str
    estado: str
    versao: str
    obrigatorio: bool
    tipo: str
    comandos: list = field(default_factory=list)
    explicacao: str = ""


def executar(args: list) -> str | None:
    """Roda sem shell e devolve stdout+stderr, ou None se não rodou."""
    try:
        r = subprocess.run(args, check=False, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return (r.stdout + r.stderr).strip()


def _disco_livre_gb(pasta: Path) -> float:
    return shutil.disk_usage(pasta).free / 1e9


def _achar_repo() -> Path | None:
    """Pasta do voice-studio (clone local), ou None quando o script veio pela URL."""
    for base in (Path(__file__).resolve().parent.parent, Path.cwd()):
        toml = base / "engine" / "pyproject.toml"
        if toml.is_file() and 'name = "voice-studio"' in toml.read_text(encoding="utf-8"):
            return base
    return None


@dataclass
class Ambiente:
    """Tudo o que os checks consultam; injetável para testar sem tocar a máquina."""

    home: Path
    env: dict
    repo: Path | None
    sistema: str
    maquina: str
    executar: Callable[[list], str | None] = executar
    which: Callable[[str], str | None] = shutil.which
    disco_livre_gb: Callable[[Path], float] = _disco_livre_gb

    @property
    def apple_silicon(self) -> bool:
        return self.sistema == "Darwin" and self.maquina == "arm64"


def ambiente_real() -> Ambiente:
    return Ambiente(home=Path.home(), env=dict(os.environ), repo=_achar_repo(),
                    sistema=platform.system(), maquina=platform.machine())


def _versao(texto: str | None) -> str:
    m = re.search(r"(\d+\.\d+(?:\.\d+)?)", texto or "")
    return m.group(1) if m else "-"


def _brew(amb: Ambiente, pacote: str) -> list:
    return [["brew", "install", pacote]] if amb.which("brew") else []


def check_sistema(amb: Ambiente) -> Item:
    versao = f"{amb.sistema} {amb.maquina}"
    if amb.apple_silicon:
        return Item("sistema", OK, versao, False, SEU, [], "macOS com Apple Silicon: é o sistema testado.")
    return Item("sistema", OPCIONAL, versao, False, SEU, [],
                "Testado só no macOS com Apple Silicon; aqui pode funcionar, mas não foi testado.")


def check_homebrew(amb: Ambiente) -> Item:
    if amb.sistema != "Darwin":
        return Item("homebrew", OK, "-", False, SEU, [], "Fora do Mac, use o gerenciador de pacotes do seu sistema.")
    if amb.which("brew"):
        return Item("homebrew", OK, _versao(amb.executar(["brew", "--version"])), False, SEU, [], "")
    return Item("homebrew", OPCIONAL, "-", False, SEU, [],
                "Os programas abaixo se instalam com o Homebrew (https://brew.sh). Instalar o Homebrew "
                "pede a sua senha: rode você mesmo o comando do site.")


def check_uv(amb: Ambiente) -> Item:
    instalar = _brew(amb, "uv") or [["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"]]
    if not amb.which("uv"):
        return Item("uv", FALTANDO, "-", True, SISTEMA, instalar,
                    "Gerencia o Python e as dependências (você não usa pip).")
    versao = _versao(amb.executar(["uv", "--version"]))
    partes = tuple(int(p) for p in versao.split(".")[:2]) if versao != "-" else (0, 0)
    if partes < UV_MINIMO:
        return Item("uv", FALTANDO, versao, True, SISTEMA, [["uv", "self", "update"]],
                    "Precisa do uv 0.5 ou mais novo.")
    return Item("uv", OK, versao, True, SISTEMA, [], "")


def check_python(amb: Ambiente) -> Item:
    alvo = PYTHON_ARM if amb.apple_silicon else "3.11"
    explicacao = ("Python 3.11 arm64 (no Apple Silicon, sem ele o uv pode pegar um Python x86_64 e o "
                  "PyTorch não instala; rode o uv com --python " + PYTHON_ARM + ")."
                  if amb.apple_silicon else "Python 3.11, instalado pelo uv.")
    caminho = amb.executar(["uv", "python", "find", alvo]) if amb.which("uv") else None
    if not caminho:
        return Item("python-3.11", FALTANDO, "-", True, DOWNLOAD, [["uv", "python", "install", alvo]], explicacao)
    return Item("python-3.11", OK, _versao(amb.executar([caminho.splitlines()[-1], "--version"])) or "3.11",
                True, DOWNLOAD, [], explicacao)


def _check_ffmpeg(amb: Ambiente, exe: str) -> Item:
    if not amb.which(exe):
        return Item(exe, FALTANDO, "-", True, SISTEMA, _brew(amb, "ffmpeg"),
                    "Lê e grava áudio e vídeo (vem no pacote ffmpeg).")
    return Item(exe, OK, _versao(amb.executar([exe, "-version"])), True, SISTEMA, [], "")


def check_ffmpeg(amb: Ambiente) -> Item:
    return _check_ffmpeg(amb, "ffmpeg")


def check_ffprobe(amb: Ambiente) -> Item:
    return _check_ffmpeg(amb, "ffprobe")


def check_whisper_cli(amb: Ambiente) -> Item:
    explicacao = "Só para transcrever (`traduzir`, `transcribe`)."
    if not amb.which("whisper-cli"):
        return Item("whisper-cli", OPCIONAL, "-", False, SISTEMA, _brew(amb, "whisper-cpp"), explicacao)
    return Item("whisper-cli", OK, _versao(amb.executar(["whisper-cli", "--version"])), False, SISTEMA, [], explicacao)


def modelo_whisper(amb: Ambiente) -> Path:
    escolhido = amb.env.get("VOICE_STUDIO_WHISPER_MODEL")
    return Path(escolhido).expanduser() if escolhido else amb.home / ".cache" / "whisper" / "ggml-small.bin"


def check_modelo_whisper(amb: Ambiente) -> Item:
    arquivo = modelo_whisper(amb)
    aviso = "" if amb.env.get("VOICE_STUDIO_WHISPER_MODEL") else (
        f" Ele não é achado sozinho: defina VOICE_STUDIO_WHISPER_MODEL={arquivo} ou passe --model.")
    explicacao = "Modelo ggml-small do Whisper (cerca de 470 MB), só para transcrever." + aviso
    if not arquivo.is_file():
        return Item("modelo-whisper", OPCIONAL, "-", False, DOWNLOAD,
                    [["curl", "-L", "--create-dirs", "-o", str(arquivo), URL_WHISPER]], explicacao)
    return Item("modelo-whisper", OK, "ggml-small", False, DOWNLOAD, [], explicacao)


def _venv(amb: Ambiente) -> Path | None:
    if amb.env.get("UV_PROJECT_ENVIRONMENT"):
        return Path(amb.env["UV_PROJECT_ENVIRONMENT"]).expanduser()
    return amb.repo / "engine" / ".venv" if amb.repo else None


def check_motor(amb: Ambiente) -> Item:
    explicacao = ("Ambiente do motor de voz com o extra xtts (coqui-tts e PyTorch, cerca de 1 GB). "
                  "O uv cria sozinho no primeiro `uv run --extra xtts`; instalar antes só adianta o download.")
    venv = _venv(amb)
    if amb.repo is None or venv is None:
        return Item("motor-xtts", OPCIONAL, "-", False, PROJETO, [],
                    explicacao + " Sem o clone, o plugin cria o ambiente no primeiro uso.")
    if any(venv.glob("lib/python3.11/site-packages/TTS")):
        return Item("motor-xtts", OK, "instalado", False, PROJETO, [], explicacao)
    python = PYTHON_ARM if amb.apple_silicon else "3.11"
    comando = ["uv", "sync", "--project", str(amb.repo / "engine"), "--python", python, "--extra", "xtts"]
    return Item("motor-xtts", OPCIONAL, "-", False, PROJETO, [comando], explicacao)


def pasta_tts(amb: Ambiente) -> Path:
    if amb.env.get("TTS_HOME"):
        return Path(amb.env["TTS_HOME"]).expanduser() / "tts"
    if amb.env.get("XDG_DATA_HOME"):
        return Path(amb.env["XDG_DATA_HOME"]).expanduser() / "tts"
    if amb.sistema == "Darwin":
        return amb.home / "Library" / "Application Support" / "tts"
    return amb.home / ".local" / "share" / "tts"


def check_modelo_xtts(amb: Ambiente) -> Item:
    if (pasta_tts(amb) / XTTS_PASTA).is_dir():
        return Item("modelo-xtts", OK, "XTTS-v2", False, SEU, [],
                    "Licença Coqui CPML: só uso não comercial.")
    return Item("modelo-xtts", OPCIONAL, "-", False, SEU, [],
                "Modelo XTTS-v2 (cerca de 2 GB, licença Coqui CPML: só uso não comercial). Ele baixa sozinho "
                "na primeira fala, depois que VOCÊ aceitar a licença com --accept-cpml. Este script não aceita por você.")


def check_perfil(amb: Ambiente) -> Item:
    escolhido = amb.env.get("VOICE_STUDIO_HOME")
    base = Path(escolhido).expanduser() if escolhido else amb.home / ".voice-studio" / "perfis"
    perfis = [p for p in base.glob("*/perfil.json")] if base.is_dir() else []
    if perfis:
        return Item("perfil-de-voz", OK, f"{len(perfis)} perfil(is)", False, SEU, [], "")
    return Item("perfil-de-voz", OPCIONAL, "-", False, SEU, [],
                "Crie o seu com uma gravação sua de 6 a 30 s: `voice-studio perfil criar <nome> <gravação> "
                "--confirm-own-voice`. Declarar que a voz é sua é com você; o script nunca faz.")


def check_disco(amb: Ambiente) -> Item:
    livre = amb.disco_livre_gb(amb.home)
    versao = f"{livre:.1f} GB livres"
    if livre < DISCO_MIN_GB:
        return Item("disco", OPCIONAL, versao, False, SEU, [],
                    f"Reserve cerca de {DISCO_MIN_GB} GB (ambiente, modelo XTTS e Whisper). Libere espaço.")
    return Item("disco", OK, versao, False, SEU, [], "")


CHECKS = [check_sistema, check_homebrew, check_uv, check_python, check_ffmpeg, check_ffprobe,
          check_whisper_cli, check_modelo_whisper, check_motor, check_modelo_xtts, check_perfil, check_disco]


def checar(amb: Ambiente) -> list:
    return [c(amb) for c in CHECKS]


def falta_obrigatorio(itens: list) -> bool:
    return any(i.obrigatorio and i.estado != OK for i in itens)


def _como_resolver(i: Item) -> str:
    if i.estado == OK:
        return ""
    if i.comandos:
        return " && ".join(" ".join(c) for c in i.comandos)
    return i.explicacao


def em_tabela(itens: list) -> str:
    linhas = [("Requisito", "Estado", "Versão", "Como resolver")]
    linhas += [(i.nome, i.estado, i.versao, _como_resolver(i)) for i in itens]
    larg = [max(len(linha[c]) for linha in linhas) for c in range(3)]
    out = [" | ".join(linha[c].ljust(larg[c]) for c in range(3)) + " | " + linha[3] for linha in linhas]
    out.insert(1, "-+-".join("-" * n for n in larg) + "-+-" + "-" * 13)
    resumo = ("Falta algo obrigatório: rode `instalar`." if falta_obrigatorio(itens)
              else "Tudo o que é obrigatório está ok.")
    return "\n".join(out + ["", resumo])


def em_json(itens: list) -> str:
    return json.dumps({"ok": not falta_obrigatorio(itens), "requisitos": [asdict(i) for i in itens]},
                      ensure_ascii=False, indent=2)


def _perguntar(pergunta: str) -> bool:
    return input(pergunta).strip().lower() in ("s", "sim", "y")


def _rodar(cmd: list) -> int:
    try:
        return subprocess.run(cmd, check=False).returncode
    except OSError as e:
        print(f"    não rodou: {e}")
        return 1


def instalar(amb: Ambiente, sim: bool = False, interativo: bool | None = None,
             perguntar: Callable[[str], bool] = _perguntar, rodar: Callable[[list], int] = _rodar,
             saida: Callable[[str], None] = print) -> int:
    """Mostra e (com o seu ok ou --sim) roda o comando de cada item que falta. Idempotente."""
    if interativo is None:
        interativo = sys.stdin.isatty()
    ja_rodados: list = []
    pendentes = [i for i in checar(amb) if i.estado != OK]
    if not pendentes:
        saida("Nada a instalar: tudo ok.")
        return 0
    for i in pendentes:
        if i.tipo == SEU:
            saida(f"- {i.nome}: Isto é com você: {i.explicacao}")
            continue
        if not i.comandos:
            saida(f"- {i.nome}: {i.explicacao}")
            continue
        for cmd in i.comandos:
            texto = " ".join(cmd)
            saida(f"- {i.nome}: {texto}")
            if cmd in ja_rodados:
                saida("    já rodado acima.")
                continue
            if sim or (interativo and perguntar("    Rodar agora? [s/N] ")):
                codigo = rodar(cmd)
                ja_rodados.append(cmd)
                saida("    feito." if codigo == 0 else f"    falhou (código {codigo}).")
            elif not interativo:
                saida("    (só mostrado: rode de novo com --sim ou num terminal para confirmar)")
    final = checar(amb)
    if falta_obrigatorio(final):
        saida("Ainda falta algo obrigatório: confira com `checar`.")
        return 1
    return 0


def main(argv: list | None = None, amb: Ambiente | None = None) -> int:
    p = argparse.ArgumentParser(prog="requisitos.py", description="Requisitos do voice-studio.")
    sub = p.add_subparsers(dest="comando", required=True)
    c = sub.add_parser("checar", help="lista cada requisito; código 1 se faltar algo obrigatório")
    c.add_argument("--json", action="store_true", help="saída em JSON")
    i = sub.add_parser("instalar", help="mostra e, com o seu ok, roda o comando de cada item que falta")
    i.add_argument("--sim", action="store_true", help="roda sem perguntar (nunca aceita licença nem declaração)")
    args = p.parse_args(argv)
    amb = amb or ambiente_real()
    if args.comando == "checar":
        itens = checar(amb)
        print(em_json(itens) if args.json else em_tabela(itens))
        return 1 if falta_obrigatorio(itens) else 0
    return instalar(amb, sim=args.sim)


if __name__ == "__main__":
    sys.exit(main())

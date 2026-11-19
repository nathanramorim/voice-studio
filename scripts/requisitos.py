#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""requisitos.py — confere e instala, com o seu ok, o que um repositório precisa (Linux, Windows e macOS).

Lê o `requisitos.toml` do repositório (contrato: sdd/spec/contrato-requisitos.md) e:
  plataforma [--json]                       mostra o que foi detectado (SO, distro, arquitetura, GPU, gerenciadores)
  validar                                   confere o toml (tipos, dependências, as 3 plataformas, trava)
  checar [--json]                           ok/faltando/aviso/pessoa/nao-suportado; código 1 se faltar obrigatório
  instalar [item ...] [--sim] [--dry-run]   na ordem das dependências; pergunta antes de cada item (ou --sim)
  prompt                                    imprime o bloco "Cole isto na sua IA" para o README

Nunca roda shell, nunca põe `sudo` sozinho, nunca aceita licença, consentimento ou login pela pessoa e
nunca lê nem mostra segredo. Códigos: 0 ok, 1 falta obrigatório ou algo falhou, 2 uso ou receita inválida.
Só biblioteca padrão: copie este arquivo (skills.lock) ou rode por URL com `--arquivo <url do toml>`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform as _platform
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

VERSAO = "0.1.0"
SISTEMAS = ("macos", "linux", "windows")
ARCHS = ("arm64", "x64")
GPUS = ("cuda", "rocm", "mps", "cpu")
TIPOS = ("programa", "biblioteca", "pacote-python", "pacote-node", "download", "servico", "maquina",
         "variavel", "path", "permissao", "credencial", "pessoa")
NUNCA_RODA = {"variavel", "permissao", "credencial", "pessoa"}
GERENCIADORES = {"macos": ("brew", "port"), "linux": ("apt", "dnf", "pacman", "zypper", "apk", "brew"),
                 "windows": ("winget", "choco", "scoop")}
EXECUTAVEL = {"apt": "apt-get"}
PRECISA_ADMIN = {"apt", "apt-get", "dnf", "yum", "pacman", "zypper", "apk", "choco"}
OK, FALTANDO, AVISO, PESSOA, NAO_SUPORTADO = "ok", "faltando", "aviso", "pessoa", "nao-suportado"
RX_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RX_VAR = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
RX_SEGREDO = re.compile(r"TOKEN|SECRET|PASSWORD|PASSWD|SENHA|CHAVE|API_?KEY|_KEY$|CREDENTIAL", re.I)
RX_PH = re.compile(r"\{([a-z]+)(?::([A-Za-z_][A-Za-z0-9_]*))?\}")
PLACEHOLDERS = {"home", "raiz", "cache", "dados", "config", "temp", "env"}
TIMEOUT_CHECAR = 60


class ReceitaInvalida(Exception):
    """O requisitos.toml não segue o contrato (código 2)."""


# ---------- plataforma ----------

def _rodar_saida(argv: list) -> tuple[int, str]:
    """Roda sem shell; devolve (código, stdout+stderr). Código 127 se não rodou."""
    exe = shutil.which(argv[0]) or argv[0]
    if inseguro_no_cmd(exe, argv):
        return 126, ""
    try:
        r = subprocess.run([exe, *argv[1:]], check=False, capture_output=True, text=True,
                           timeout=TIMEOUT_CHECAR, encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return 127, ""
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()


def _rodar_visivel(argv: list) -> int:
    exe = shutil.which(argv[0]) or argv[0]
    if inseguro_no_cmd(exe, argv):
        print(f"    recusado: {exe} passaria pelo cmd.exe com caracteres de shell")
        return 126
    try:
        return subprocess.run([exe, *argv[1:]], check=False).returncode
    except OSError as e:
        print(f"    não rodou: {e}")
        return 127


def ler_os_release(texto: str) -> dict:
    """Interpreta /etc/os-release: devolve {'id': ..., 'like': [...], 'versao': ...}."""
    campos = {}
    for linha in texto.splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            k, v = linha.split("=", 1)
            campos[k.strip()] = v.strip().strip('"').strip("'")
    return {"id": campos.get("ID", "").lower(), "like": campos.get("ID_LIKE", "").lower().split(),
            "versao": campos.get("VERSION_ID", "")}


def normalizar_arch(maquina: str) -> str:
    m = maquina.lower()
    if m in ("arm64", "aarch64", "armv8", "armv8l"):
        return "arm64"
    if m in ("x86_64", "amd64", "x64", "i686", "x86"):
        return "x64"
    return m or "?"


@dataclass
class Ambiente:
    """Tudo o que o motor consulta da máquina; injetável nos testes."""

    sistema: str
    arch: str
    home: Path
    env: dict
    distro: dict = field(default_factory=lambda: {"id": "", "like": [], "versao": ""})
    arch_hw: str = ""
    rosetta: bool = False
    wsl: bool = False
    gpu: str = "cpu"
    shell: str = ""
    admin: bool = False
    which: Callable[[str], str | None] = shutil.which
    executar: Callable[[list], tuple[int, str]] = _rodar_saida
    rodar: Callable[[list], int] = _rodar_visivel
    disco_livre_gb: Callable[[Path], float] = lambda p: shutil.disk_usage(p).free / 2**30
    memoria_gb: Callable[[], float] = lambda: 0.0

    def gerenciadores(self) -> list:
        return [g for g in GERENCIADORES.get(self.sistema, ()) if self.which(EXECUTAVEL.get(g, g))]

    def resumo(self) -> dict:
        return {"sistema": self.sistema, "arch": self.arch, "arch_hw": self.arch_hw or self.arch,
                "rosetta": self.rosetta, "wsl": self.wsl, "distro": self.distro.get("id", ""),
                "distro_like": self.distro.get("like", []), "distro_versao": self.distro.get("versao", ""),
                "gpu": self.gpu, "shell": self.shell, "admin": self.admin, "gerenciadores": self.gerenciadores()}


def _memoria_real() -> float:
    try:
        if hasattr(os, "sysconf") and "SC_PHYS_PAGES" in os.sysconf_names:
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30
    except (OSError, ValueError):
        pass
    if sys.platform == "win32":
        import ctypes

        class _Mem(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("resto", ctypes.c_ulonglong * 6)]
        m = _Mem()
        m.dwLength = ctypes.sizeof(_Mem)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            return m.ullTotalPhys / 2**30
    code, out = _rodar_saida(["sysctl", "-n", "hw.memsize"])
    return int(out) / 2**30 if code == 0 and out.isdigit() else 0.0


def _admin_real(sistema: str) -> bool:
    if sistema == "windows":
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError):
            return False
    return hasattr(os, "geteuid") and os.geteuid() == 0


def _gpu_real(sistema: str, arch_hw: str) -> str:
    if sistema == "macos":
        return "mps" if arch_hw == "arm64" else "cpu"
    if shutil.which("nvidia-smi") and _rodar_saida(["nvidia-smi", "-L"])[0] == 0:
        return "cuda"
    if shutil.which("rocminfo") or Path("/opt/rocm").is_dir():
        return "rocm"
    return "cpu"


def _shell_real(sistema: str, env: dict) -> str:
    if sistema == "windows":
        return "windows"  # PowerShell ou cmd não dá para saber com certeza: as instruções mostram os dois
    return Path(env.get("SHELL", "sh")).name or "sh"


def ambiente_real() -> Ambiente:
    sistema = {"Darwin": "macos", "Windows": "windows"}.get(_platform.system(), "linux")
    arch = normalizar_arch(_platform.machine())
    arch_hw, rosetta, wsl, distro = arch, False, False, {"id": "", "like": [], "versao": ""}
    if sistema == "macos" and _rodar_saida(["sysctl", "-n", "sysctl.proc_translated"])[1] == "1":
        arch_hw, rosetta = "arm64", True
    if sistema == "linux":
        for f in (Path("/etc/os-release"), Path("/usr/lib/os-release")):
            if f.is_file():
                distro = ler_os_release(f.read_text(encoding="utf-8", errors="replace"))
                break
        try:
            wsl = "microsoft" in Path("/proc/version").read_text(errors="replace").lower()
        except OSError:
            wsl = False
    env = dict(os.environ)
    return Ambiente(sistema=sistema, arch=arch, arch_hw=arch_hw, rosetta=rosetta, wsl=wsl, distro=distro,
                    home=Path.home(), env=env, gpu=_gpu_real(sistema, arch_hw), shell=_shell_real(sistema, env),
                    admin=_admin_real(sistema), memoria_gb=_memoria_real)


# ---------- placeholders e caminhos ----------

def _bases(amb: Ambiente) -> dict:
    h, e = amb.home, amb.env
    if amb.sistema == "macos":
        return {"cache": h / "Library" / "Caches", "dados": h / "Library" / "Application Support",
                "config": h / "Library" / "Application Support"}
    if amb.sistema == "windows":
        local = Path(e.get("LOCALAPPDATA") or h / "AppData" / "Local")
        roaming = Path(e.get("APPDATA") or h / "AppData" / "Roaming")
        return {"cache": local, "dados": roaming, "config": roaming}
    return {"cache": Path(e.get("XDG_CACHE_HOME") or h / ".cache"),
            "dados": Path(e.get("XDG_DATA_HOME") or h / ".local" / "share"),
            "config": Path(e.get("XDG_CONFIG_HOME") or h / ".config")}


def expandir(texto: str, amb: Ambiente, raiz: Path) -> str | None:
    """Troca {home} {raiz} {cache} {dados} {config} {temp} {env:NOME}; None se a variável não existir."""
    bases = _bases(amb)
    faltou = False

    def troca(m: re.Match) -> str:
        nonlocal faltou
        nome, var = m.group(1), m.group(2)
        if nome == "env":
            valor = amb.env.get(var or "")
            faltou = faltou or not valor
            return valor or ""
        valores = {"home": amb.home, "raiz": raiz, "temp": Path(tempfile.gettempdir()), **bases}
        return str(valores[nome])

    saida = RX_PH.sub(troca, texto)
    return None if faltou else saida


# ---------- trava: nunca agir pela pessoa ----------

SHELLS = {"sh", "bash", "zsh", "fish", "dash", "ash", "ksh", "mksh", "csh", "tcsh", "yash", "nu", "xonsh",
          "elvish", "busybox", "cmd", "powershell", "pwsh", "iex", "invoke-expression", "eval"}
ELEVA = {"sudo", "doas", "su", "runas", "pkexec", "gsudo", "run0"}
EMBRULHO_ARG0 = {"env", "xargs", "nohup", "nice", "timeout", "time", "watch", "start"}
EMBRULHO = {"env", "xargs", "nohup"}
RX_INTERPRETADOR = re.compile(r"^(python|pypy|py|node|nodejs|ruby|perl|php|deno|bun|osascript|lua|luajit|tclsh|wish|"
                              r"rscript|julia)(\d+(\.\d+)*)?[wt]?$")
OPCAO_DE_INTERPRETADOR = {"--version", "-v", "-V", "-m", "-I", "-B", "-u", "--help"}
MODULOS_PERMITIDOS = {"pip", "venv", "ensurepip"}
PROGRAMA_POSICIONAL = {"awk", "gawk", "mawk", "nawk", "busybox", "sed", "gsed"}
EXECUTA_STRING = {"npx", "npm", "pnpm", "pnpx", "yarn", "bunx", "find"}
OPCAO_QUE_EXECUTA = {"-c", "--call", "-exec", "-execdir", "-ok", "-okdir"}
META = set("|;&`$^%<>\n\r")
RX_SILENCIOSO = re.compile(r"^(/q[nbrf]?[!+-]?|/quiet|/passive|/s|/silent|/verysilent|--?silent)$", re.I)
ACEITE_EXATO = {"yes", "assume-yes", "assumeyes", "noconfirm", "no-confirm", "non-interactive", "force-yes",
                "auto-approve", "unattended", "quiet-yes", "accept", "agree"}  # comparados sem os traços
ACEITE_PARTE = ("accept", "agree", "licen", "eula", "confirm", "consent")
ACEITE_POR_PROGRAMA = {"winget": {"-h"}, "zypper": {"-n"}, "apk": {"--no-interactive"}}
RX_VERSAO = re.compile(r"^[A-Za-z0-9_.\[\],-]*(?:[<>]=?|==|!=|~=)[0-9][0-9A-Za-z.*+!-]*$")


def _nome(arg: str) -> str:
    nome = re.split(r"[\\/]", arg.rstrip("/\\"))[-1].lower()
    return nome[:-4] if nome.endswith(".exe") else nome


def _metacaractere(arg: str) -> bool:
    """`< >` só são aceitos num especificador de versão (`torch<2.9`, `>=3.11`); o resto é shell."""
    sobra = set(arg) & META
    if sobra and sobra <= {"<", ">"} and RX_VERSAO.match(arg):
        return False
    return bool(sobra)


def _interpretador_inline(argv: list, nomes: list) -> bool:
    """Depois de um interpretador, só opções de uma lista fechada e `-m` só com pip, venv ou ensurepip.

    Exceção única: `uv python ...` (subcomando do uv, não o interpretador)."""
    inicio = 2 if nomes[:2] == ["uv", "python"] else 0
    for k in range(inicio, len(argv)):
        if not argv[k].startswith("-") and RX_INTERPRETADOR.match(nomes[k]):
            resto = argv[k + 1:]
            if any(a.startswith("-") and a not in OPCAO_DE_INTERPRETADOR for a in resto):
                return True
            return any(a == "-m" and (i + 1 >= len(resto) or resto[i + 1] not in MODULOS_PERMITIDOS)
                       for i, a in enumerate(resto))
    return False


def _executa_string(argv: list, nomes: list, soltos: set) -> bool:
    """awk/sed com programa, `npx -c`, `npm exec --call=`, `find -exec`: equivalem a um shell."""
    for k, n in enumerate(nomes):
        if n in PROGRAMA_POSICIONAL and not argv[k].startswith("-"):
            if any(a not in ("--version", "--help") for a in argv[k + 1:]):
                return True
    if soltos & EXECUTA_STRING:
        return any(a in OPCAO_QUE_EXECUTA or a.startswith(("--call=", "-c=")) for a in argv)
    return False


def proibido(argv: list) -> str | None:
    """Motivo pelo qual o comando poderia agir pela pessoa (ou passar por shell); None se for seguro.

    Lista de bloqueio que prefere bloquear a mais (ADR-0005): shell, embrulho e administrador em qualquer
    argumento que não seja opção; os falsos positivos aceitos estão no contrato (use `manual`)."""
    if not argv:
        return "comando vazio"
    nomes = [_nome(a) for a in argv]
    soltos = {n for a, n in zip(argv, nomes, strict=True) if not a.startswith("-")}
    if nomes[0] in EMBRULHO_ARG0 or soltos & EMBRULHO:
        return "embrulha outro comando (env, xargs, nohup...)"
    if soltos & SHELLS:
        return "passa por um shell"
    if soltos & ELEVA:
        return "o motor nunca pede administrador sozinho (só mostra)"
    if _interpretador_inline(argv, nomes) or _executa_string(argv, nomes, soltos):
        return "código inline ou programa como texto (equivale a um shell)"
    por_programa = set().union(*(ACEITE_POR_PROGRAMA.get(n, set()) for n in soltos))
    for arg in argv:
        if _metacaractere(arg):
            return f"metacaractere de shell em '{arg}'"
        if RX_SILENCIOSO.match(arg) or arg in por_programa:
            return f"'{arg}' instala em silêncio ou confirma pela pessoa"
        limpo = re.sub(r"(?:[A-Za-z][\w+.-]*://|~|\.{0,2}[\\/])[^\s=:,]*",
                       lambda m: _nome(m.group(0)), arg)
        for t in (t for t in re.split(r"[\s=:,]+", limpo.lower()) if t):
            if t.lstrip("-") in ACEITE_EXATO or any(p in t for p in ACEITE_PARTE) or re.fullmatch(r"-[a-z]*y[a-z]*", t):
                return f"'{arg}' aceitaria ou confirmaria algo pela pessoa"
    return None


def inseguro_no_cmd(exe: str, argv: list) -> bool:
    """No Windows, .cmd/.bat passam pelo cmd.exe: recusa qualquer caractere que ele interprete."""
    return exe.lower().endswith((".cmd", ".bat")) and any(set(a) & (META | {"!", "(", ")", '"'}) for a in argv[1:])


# ---------- receita: leitura e validação ----------

CHAVES_ITEM = {"id", "descricao", "tipo", "obrigatorio", "depende_de", "tamanho", "cache", "checar", "receita",
               "variavel", "nota"}
CHAVES_RECEITA = {"quando", "comandos", "admin", "baixar", "manual", "nao_suportado", "dispensado", "checar",
                  "path", "nota"}
CHAVES_QUANDO = {"sistema", "arch", "gpu", "distro", "gerenciador", "wsl", "rosetta"}
CHAVES_CHECAR = {"comando", "regex", "versao_regex", "versao_minima", "versao_maxima", "arquivo", "env",
                 "disco_gb", "memoria_gb", "procurar_em", "sensivel", "arch_binario"}


@dataclass
class Item:
    dados: dict
    raiz: Path

    def __getattr__(self, nome: str):
        return self.dados.get(nome)

    @property
    def receitas(self) -> list:
        return self.dados.get("receita", [])


def ler_texto(arquivo: str) -> tuple[str, Path]:
    """Texto do toml e a raiz ({raiz}); aceita caminho local ou URL https."""
    if arquivo.startswith("https://"):
        with urllib.request.urlopen(arquivo, timeout=30) as r:
            return r.read().decode("utf-8"), Path.cwd()
    if "://" in arquivo:
        raise ReceitaInvalida(f"só https é aceito: {arquivo}")
    p = Path(arquivo)
    if not p.is_file():
        raise ReceitaInvalida(f"não achei {p}")
    return p.read_text(encoding="utf-8"), p.resolve().parent


def achar_toml() -> str:
    for base in (Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parent.parent):
        if (base / "requisitos.toml").is_file():
            return str(base / "requisitos.toml")
    raise ReceitaInvalida("não achei requisitos.toml (use --arquivo)")


def carregar(arquivo: str, _vistos: set | None = None) -> tuple[dict, list]:
    """Lê o toml (e os `projeto.incluir`) e devolve (projeto, itens). Valida tudo; erro levanta ReceitaInvalida."""
    vistos = _vistos if _vistos is not None else set()
    texto, raiz = ler_texto(arquivo)
    try:
        dados = tomllib.loads(texto)
    except tomllib.TOMLDecodeError as e:
        raise ReceitaInvalida(f"{arquivo}: TOML inválido: {e}") from None
    erros = validar(dados)
    if erros:
        raise ReceitaInvalida("\n".join(f"{arquivo}: {e}" for e in erros))
    itens = [Item(d, raiz) for d in dados["requisito"]]
    for rel in dados["projeto"].get("incluir", []):
        alvo = (raiz / rel).resolve()
        if alvo in vistos:
            continue
        vistos.add(alvo)
        itens += carregar(str(alvo), vistos)[1]
    ids = [i.id for i in itens]
    repetidos = sorted({x for x in ids if ids.count(x) > 1})
    if repetidos:
        raise ReceitaInvalida(f"id repetido entre arquivos: {', '.join(repetidos)}")
    erros = _erros_grafo({i.id: i.depende_de or [] for i in itens})
    if erros:
        raise ReceitaInvalida("\n".join(erros))
    return dados["projeto"], itens


def _erros_texto(valor, onde: str, env: bool = False) -> list:
    """Texto não vazio com placeholders conhecidos; {env:NOME} só onde nada é mostrado (checar)."""
    if not isinstance(valor, str) or not valor.strip():
        return [f"{onde}: precisa ser texto não vazio"]
    if not env and "{env:" in valor:
        return [f"{onde}: {{env:...}} só vale em checar (o valor poderia ser segredo e apareceria na saída)"]
    ruins = [m.group(1) for m in RX_PH.finditer(valor) if m.group(1) not in PLACEHOLDERS
             or (m.group(1) == "env") != bool(m.group(2))]
    sobra = re.sub(RX_PH, "", valor)
    if ruins or re.search(r"\{[a-z]+(:[^}]*)?\}", sobra):
        return [f"{onde}: placeholder desconhecido (use {{home}} {{raiz}} {{cache}} {{dados}} {{config}} "
                f"{{temp}} {{env:NOME}})"]
    return []


def _erros_comando(cmd, onde: str, env: bool = False) -> list:
    if not isinstance(cmd, list) or not cmd or not all(isinstance(a, str) and a for a in cmd):
        return [f"{onde}: comando é lista de argumentos (texto não vazio), sem shell"]
    motivo = proibido(cmd)
    erros = [f"{onde}: recusado pela trava: {motivo}"] if motivo else []
    return erros + [e for a in cmd for e in _erros_texto(a, onde, env)]


def _erros_checar(c, onde: str) -> list:
    if not isinstance(c, dict):
        return [f"{onde}: checar precisa ser tabela"]
    erros = [f"{onde}: chave desconhecida '{k}'" for k in c if k not in CHAVES_CHECAR]
    if "comando" in c:
        erros += _erros_comando(c["comando"], f"{onde}.comando", env=True)
    for k in ("regex", "versao_regex"):
        if k in c:
            try:
                re.compile(c[k])
            except (re.error, TypeError):
                erros.append(f"{onde}.{k}: regex inválida")
    for k in ("versao_minima", "versao_maxima"):
        if k in c and not re.fullmatch(r"\d+(\.\d+)*", str(c[k])):
            erros.append(f"{onde}.{k}: use números como 3.11 ou 0.5.0")
    arquivos = c.get("arquivo", [])
    for a in ([arquivos] if isinstance(arquivos, str) else arquivos) + list(c.get("procurar_em", [])):
        erros += _erros_texto(a, f"{onde}.arquivo", env=True)
    if "env" in c and not RX_VAR.fullmatch(str(c["env"])):
        erros.append(f"{onde}.env: nome de variável inválido")
    for k in ("disco_gb", "memoria_gb"):
        if k in c and not isinstance(c[k], (int, float)):
            erros.append(f"{onde}.{k}: número")
    if "arch_binario" in c and (c["arch_binario"] not in ARCHS or "comando" not in c):
        erros.append(f"{onde}.arch_binario: use arm64 ou x64, junto com comando")
    return erros


def _erros_quando(q, onde: str) -> list:
    if not isinstance(q, dict):
        return [f"{onde}: quando precisa ser tabela"]
    erros = [f"{onde}: chave desconhecida '{k}'" for k in q if k not in CHAVES_QUANDO]
    for chave, validos in (("sistema", SISTEMAS), ("arch", ARCHS), ("gpu", GPUS)):
        if chave in q and q[chave] not in validos:
            erros.append(f"{onde}.{chave}: use um de {', '.join(validos)}")
    for chave in ("wsl", "rosetta"):
        if chave in q and not isinstance(q[chave], bool):
            erros.append(f"{onde}.{chave}: true ou false")
    return erros


def _erros_receita(r, tipo: str, onde: str) -> list:
    if not isinstance(r, dict):
        return [f"{onde}: receita precisa ser tabela"]
    erros = [f"{onde}: chave desconhecida '{k}'" for k in r if k not in CHAVES_RECEITA]
    erros += _erros_quando(r.get("quando", {}), f"{onde}.quando")
    acoes = [k for k in ("comandos", "baixar", "manual", "nao_suportado", "dispensado") if k in r]
    if not acoes:
        erros.append(f"{onde}: diga o que fazer (comandos, baixar, manual, nao_suportado ou dispensado)")
    if {"nao_suportado", "dispensado"} & set(acoes) and len(acoes) > 1:
        erros.append(f"{onde}: nao_suportado e dispensado não se misturam com outra ação")
    if tipo in NUNCA_RODA and {"comandos", "baixar"} & set(acoes):
        erros.append(f"{onde}: o tipo '{tipo}' é com a pessoa: use manual, nunca comandos ou baixar")
    for k in ("manual", "nao_suportado", "dispensado", "nota"):
        if k in r:
            erros += _erros_texto(r[k], f"{onde}.{k}")
    for n, cmd in enumerate(r.get("comandos", []) if isinstance(r.get("comandos", []), list) else [None]):
        erros += _erros_comando(cmd, f"{onde}.comandos[{n}]")
    if "comandos" in r and not r["comandos"]:
        erros.append(f"{onde}.comandos: lista vazia")
    if "baixar" in r:
        b = r["baixar"]
        if not isinstance(b, dict) or not str(b.get("url", "")).startswith("https://") or "destino" not in b:
            erros.append(f"{onde}.baixar: precisa de url https:// e destino")
        else:
            erros += _erros_texto(b["destino"], f"{onde}.baixar.destino")
            if "sha256" in b and not re.fullmatch(r"[0-9a-f]{64}", str(b["sha256"])):
                erros.append(f"{onde}.baixar.sha256: 64 hex minúsculos")
    if "checar" in r:
        erros += _erros_checar(r["checar"], f"{onde}.checar")
    for p in r.get("path", []):
        erros += _erros_texto(p, f"{onde}.path")
    if "admin" in r and not isinstance(r["admin"], bool):
        erros.append(f"{onde}.admin: true ou false")
    return erros


def _cobertura(receitas: list) -> list:
    """Sistemas sem nenhuma receita que se aplique."""
    falta = []
    for s in SISTEMAS:
        if not any(r.get("quando", {}).get("sistema", s) == s for r in receitas if isinstance(r, dict)):
            falta.append(s)
    return falta


def _erros_item(d, n: int) -> list:
    onde = f"requisito[{n}]" + (f" ({d.get('id')})" if isinstance(d, dict) and d.get("id") else "")
    if not isinstance(d, dict):
        return [f"{onde}: precisa ser tabela"]
    erros = [f"{onde}: chave desconhecida '{k}'" for k in d if k not in CHAVES_ITEM]
    if not RX_ID.fullmatch(str(d.get("id", ""))):
        erros.append(f"{onde}.id: use [a-z0-9-]")
    erros += _erros_texto(d.get("descricao"), f"{onde}.descricao")
    tipo = d.get("tipo")
    if tipo not in TIPOS:
        erros.append(f"{onde}.tipo: use um de {', '.join(TIPOS)}")
    if not isinstance(d.get("obrigatorio", False), bool):
        erros.append(f"{onde}.obrigatorio: true ou false")
    if not isinstance(d.get("depende_de", []), list):
        erros.append(f"{onde}.depende_de: lista de ids")
    if "checar" in d:
        erros += _erros_checar(d["checar"], f"{onde}.checar")
    receitas = d.get("receita", [])
    if not isinstance(receitas, list) or not receitas:
        return [*erros, f"{onde}: precisa de [[requisito.receita]] (uma por plataforma ou geral)"]
    for k, r in enumerate(receitas):
        erros += _erros_receita(r, tipo, f"{onde}.receita[{k}]")
    sem_checar = [r for r in receitas if isinstance(r, dict) and "checar" not in r
                  and not {"nao_suportado", "dispensado"} & set(r)]
    if tipo not in NUNCA_RODA and "checar" not in d and sem_checar:
        erros.append(f"{onde}: diga como conferir ([requisito.checar] ou checar na receita)")
    falta = _cobertura(receitas)
    if falta:
        erros.append(f"{onde}: sem receita para {', '.join(falta)} (use nao_suportado com a alternativa)")
    if tipo == "variavel":
        v = d.get("variavel")
        if not isinstance(v, dict) or not RX_VAR.fullmatch(str(v.get("nome", ""))):
            erros.append(f"{onde}.variavel: precisa de nome")
        elif "valor" in v and RX_SEGREDO.search(v["nome"]):
            erros.append(f"{onde}.variavel: '{v['nome']}' parece segredo: sem valor na receita (use credencial)")
        elif "valor" in v:
            erros += _erros_texto(v["valor"], f"{onde}.variavel.valor")
    return erros


def _erros_grafo(deps: dict) -> list:
    erros = [f"depende_de: '{d}' não existe (em {i})" for i, ds in deps.items() for d in ds if d not in deps]
    if erros:
        return erros
    try:
        ordem_topologica(deps, list(deps))
    except ReceitaInvalida as e:
        return [str(e)]
    return []


def validar(dados: dict) -> list:
    """Lista de erros do toml (vazia = válido)."""
    if dados.get("versao") != 1:
        return ["versao: use 1"]
    projeto = dados.get("projeto")
    if not isinstance(projeto, dict) or not str(projeto.get("nome", "")).strip():
        return ["[projeto] precisa de nome"]
    erros = [f"projeto: chave desconhecida '{k}'" for k in projeto if k not in {"nome", "script", "incluir", "repo"}]
    itens = dados.get("requisito")
    if not isinstance(itens, list) or not itens:
        return [*erros, "precisa de pelo menos um [[requisito]]"]
    for n, d in enumerate(itens):
        erros += _erros_item(d, n)
    if erros:
        return erros
    ids = [d["id"] for d in itens]
    erros += [f"id repetido: {x}" for x in sorted({x for x in ids if ids.count(x) > 1})]
    if not projeto.get("incluir"):  # com incluir, o grafo é conferido depois de juntar os arquivos
        erros += _erros_grafo({d["id"]: d.get("depende_de", []) for d in itens})
    return erros


def ordem_topologica(deps: dict, alvos: list) -> list:
    """Alvos e as suas dependências, dependências primeiro; ciclo levanta ReceitaInvalida."""
    ordem, marca = [], {}

    def visitar(i: str, trilha: tuple) -> None:
        if marca.get(i) == 2:
            return
        if marca.get(i) == 1:
            raise ReceitaInvalida(f"depende_de em ciclo: {' -> '.join((*trilha, i))}")
        marca[i] = 1
        for d in deps.get(i, []):
            visitar(d, (*trilha, i))
        marca[i] = 2
        ordem.append(i)

    for a in alvos:
        visitar(a, ())
    return ordem


# ---------- checagem ----------

@dataclass
class Resultado:
    id: str
    descricao: str
    tipo: str
    obrigatorio: bool
    status: str
    versao: str = "-"
    fazer: str = ""
    comandos: list = field(default_factory=list)
    admin: bool = False
    baixar: dict | None = None
    path: list = field(default_factory=list)
    nota: str = ""

    def como_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


def _casa(q: dict, amb: Ambiente) -> bool:
    if q.get("sistema", amb.sistema) != amb.sistema or q.get("arch", amb.arch) != amb.arch:
        return False
    if q.get("gpu", amb.gpu) != amb.gpu or q.get("wsl", amb.wsl) != amb.wsl:
        return False
    if q.get("rosetta", amb.rosetta) != amb.rosetta:
        return False
    if "distro" in q and q["distro"].lower() not in [amb.distro.get("id", ""), *amb.distro.get("like", [])]:
        return False
    if "gerenciador" in q:
        g = q["gerenciador"]
        return bool(amb.which(EXECUTAVEL.get(g, g)))
    return True


def escolher_receita(item: Item, amb: Ambiente) -> tuple[dict | None, list]:
    """Primeira receita que casa com a máquina; e os gerenciadores que faltaram para as do mesmo sistema."""
    faltam = []
    for r in item.receitas:
        q = r.get("quando", {})
        if _casa(q, amb):
            return r, []
        sem_g = {k: v for k, v in q.items() if k != "gerenciador"}
        if "gerenciador" in q and _casa(sem_g, amb):
            faltam.append(q["gerenciador"])
    return None, faltam


def _num(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:4])


def _versao_de(saida: str, regex: str | None) -> str:
    m = re.search(regex or r"(\d+\.\d+(?:\.\d+)?)", saida)
    if not m:
        return "-"
    return m.group(1) if m.groups() else m.group(0)


def conferir(c: dict, amb: Ambiente, raiz: Path) -> tuple[bool, str, str]:
    """Aplica a checagem: (passou, versão, observação)."""
    sensivel = c.get("sensivel", False) or any("{env:" in a for a in c.get("comando", []))
    versao = "-"
    if "env" in c and not amb.env.get(c["env"]):
        return False, "-", f"variável {c['env']} não definida"
    if "arquivo" in c:
        alvos = [c["arquivo"]] if isinstance(c["arquivo"], str) else c["arquivo"]
        caminhos = [expandir(a, amb, raiz) for a in alvos]
        if not any(p and _existe(p) for p in caminhos):
            return False, "-", "não encontrado"
    if "disco_gb" in c:
        try:
            livre = amb.disco_livre_gb(amb.home)
        except OSError:
            return False, "-", "não deu para medir o disco"
        versao = f"{livre:.0f} GB livres"
        if livre < c["disco_gb"]:
            return False, versao, f"precisa de {c['disco_gb']} GB livres"
    if "memoria_gb" in c:
        mem = amb.memoria_gb()
        versao = f"{mem:.0f} GB RAM"
        if mem and mem < c["memoria_gb"]:
            return False, versao, f"precisa de {c['memoria_gb']} GB de RAM"
    if "comando" in c:
        argv = [expandir(a, amb, raiz) for a in c["comando"]]
        if None in argv:
            return False, "-", "variável de ambiente do comando não definida"
        if not amb.which(argv[0]):
            fora = _fora_do_path(argv[0], c, amb, raiz)
            return False, "-", (f"instalado em {fora}, mas fora do PATH" if fora else "não encontrado")
        codigo, saida = amb.executar(argv)
        if codigo != 0:
            return False, "-", "a conferência falhou"
        if "regex" in c and not re.search(c["regex"], saida):
            return (False, "-" if sensivel else _versao_de(saida, c.get("versao_regex")),
                    "a saída não confere" if sensivel else f"a saída não confere com /{c['regex']}/")
        if not sensivel:
            versao = _versao_de(saida, c.get("versao_regex"))
        if "versao_minima" in c and (versao == "-" or _num(versao) < _num(str(c["versao_minima"]))):
            return False, versao, f"precisa de {c['versao_minima']} ou mais nova"
        if "versao_maxima" in c and (versao == "-" or _num(versao) >= _num(str(c["versao_maxima"]))):
            return False, versao, f"precisa ser anterior a {c['versao_maxima']}"
        if "arch_binario" in c:
            archs = arch_do_binario(amb.which(argv[0]) or "")
            if c["arch_binario"] not in archs:
                return False, versao, f"o binário é {'/'.join(sorted(archs)) or '?'}, precisa de {c['arch_binario']}"
    return True, ("-" if sensivel else versao), ""


def arch_do_binario(caminho: str) -> set:
    """Arquiteturas do executável lendo o cabeçalho (Mach-O, universal, ELF ou PE); vazio se não souber."""
    try:
        with open(Path(caminho).resolve(), "rb") as f:
            cab = f.read(4096)
    except OSError:
        return set()
    macho = {0x0100000C: "arm64", 0x01000007: "x64"}
    if cab[:4] == b"\xcf\xfa\xed\xfe":
        return {macho.get(int.from_bytes(cab[4:8], "little"), "?")} - {"?"}
    if cab[:4] == b"\xca\xfe\xba\xbe":
        n = int.from_bytes(cab[4:8], "big")
        tipos = [int.from_bytes(cab[8 + 20 * k:12 + 20 * k], "big") for k in range(min(n, 8))]
        return {macho[t] for t in tipos if t in macho}
    if cab[:4] == b"\x7fELF":
        return {{0xB7: "arm64", 0x3E: "x64"}.get(int.from_bytes(cab[18:20], "little"), "?")} - {"?"}
    if cab[:2] == b"MZ" and len(cab) > 0x40:
        pe = int.from_bytes(cab[0x3C:0x40], "little")
        if cab[pe:pe + 4] == b"PE\0\0":
            return {{0xAA64: "arm64", 0x8664: "x64"}.get(int.from_bytes(cab[pe + 4:pe + 6], "little"), "?")} - {"?"}
    return set()


def _existe(caminho: str) -> bool:
    """Existe? Aceita glob (`*?[`) em caminho absoluto ou enraizado, em qualquer SO."""
    if not any(ch in caminho for ch in "*?["):
        return Path(caminho).exists()
    p = Path(caminho)
    ancora = p.anchor or "."
    resto = str(p)[len(p.anchor):] if p.anchor else str(p)
    try:
        return any(Path(ancora).glob(resto))
    except (OSError, ValueError, NotImplementedError):
        return False


def _fora_do_path(exe: str, c: dict, amb: Ambiente, raiz: Path) -> str:
    """Pasta (como mostrar) onde o programa está fora do PATH; com {env:} mostra o placeholder, nunca o valor."""
    for pasta in c.get("procurar_em", []):
        base = expandir(pasta, amb, raiz)
        if base and any((Path(base) / (exe + ext)).is_file() for ext in ("", ".exe", ".cmd")):
            return pasta if "{env:" in pasta else base
    return ""


def _texto_comando(cmd: list, admin: bool, amb: Ambiente) -> str:
    txt = " ".join(f'"{a}"' if " " in a else a for a in cmd)
    if admin and not amb.admin:
        return f"sudo {txt}" if amb.sistema != "windows" else f"{txt}  (num terminal de administrador)"
    return txt


def instrucao_path(pasta: str, amb: Ambiente) -> str:
    sh = amb.shell
    if amb.sistema == "windows":
        return (f'PowerShell: [Environment]::SetEnvironmentVariable("Path", "{pasta};" + '
                '[Environment]::GetEnvironmentVariable("Path", "User"), "User")  (ou Configurações > Variáveis '
                'de ambiente; abra outro terminal)')
    if sh == "fish":
        return f"fish_add_path {pasta}"
    rc = {"zsh": "~/.zshrc", "bash": "~/.bashrc"}.get(sh, "~/.profile")
    return f'export PATH="{pasta}:$PATH"  (adicione ao {rc} e abra outro terminal)'


def instrucao_variavel(nome: str, valor: str, amb: Ambiente) -> str:
    if amb.sistema == "windows":
        return (f'PowerShell: [Environment]::SetEnvironmentVariable("{nome}", "{valor}", "User")  '
                f'ou cmd: setx {nome} "{valor}"')
    if amb.shell == "fish":
        return f'set -Ux {nome} "{valor}"'
    rc = {"zsh": "~/.zshrc", "bash": "~/.bashrc"}.get(amb.shell, "~/.profile")
    return f'export {nome}="{valor}"  (adicione ao {rc})'


def _precisa_admin(r: dict) -> bool:
    if "admin" in r:
        return r["admin"]
    return any(_nome(c[0]) in PRECISA_ADMIN for c in r.get("comandos", []))


def checar_item(item: Item, amb: Ambiente) -> Resultado:
    res = Resultado(item.id, item.descricao, item.tipo, bool(item.obrigatorio), FALTANDO, nota=item.nota or "")
    r, faltam = escolher_receita(item, amb)
    if r is None:
        res.status = FALTANDO if res.obrigatorio else AVISO
        res.fazer = (f"instale um gerenciador de pacotes: {' ou '.join(faltam)}" if faltam
                     else "nenhuma receita para esta máquina")
        return res
    if r.get("nota"):
        res.nota = r["nota"]
    if "nao_suportado" in r:
        res.status, res.fazer = NAO_SUPORTADO, r["nao_suportado"]
        return res
    if "dispensado" in r:
        res.status, res.fazer = OK, ""
        res.nota = r["dispensado"]
        return res
    c = r.get("checar", item.checar)
    if item.tipo == "credencial":
        c = {**(c or {}), "sensivel": True}
    passou, versao, obs = conferir(c, amb, item.raiz) if c else (False, "-", "")
    res.versao = versao
    if passou:
        res.status = OK
        return res
    res.status = PESSOA if item.tipo in NUNCA_RODA else (FALTANDO if res.obrigatorio else AVISO)
    _preencher_acao(res, r, item, amb, obs)
    return res


def _preencher_acao(res: Resultado, r: dict, item: Item, amb: Ambiente, obs: str) -> None:
    partes = [obs] if obs and obs != "não encontrado" else []
    res.admin = _precisa_admin(r)
    res.path = [p for p in (expandir(x, amb, item.raiz) for x in r.get("path", [])) if p]
    if "comandos" in r:
        res.comandos = [[expandir(a, amb, item.raiz) or a for a in c] for c in r["comandos"]]
        partes.append(" && ".join(_texto_comando(c, res.admin, amb) for c in res.comandos))
    if "baixar" in r:
        destino = expandir(r["baixar"]["destino"], amb, item.raiz)
        res.baixar = {**r["baixar"], "destino": destino}
        partes.append(f"baixar {r['baixar']['url']} -> {destino}" + (f" ({item.tamanho})" if item.tamanho else ""))
    if item.tipo == "variavel" and item.variavel:
        v = item.variavel
        valor = expandir(v.get("valor", "<valor>"), amb, item.raiz) or v.get("valor", "<valor>")
        partes.append(instrucao_variavel(v["nome"], valor, amb))
    if "manual" in r:
        partes.append(r["manual"])
    if res.path and not partes:
        partes.append("; ".join(instrucao_path(p, amb) for p in res.path))
    res.fazer = " | ".join(p for p in partes if p) or obs


def checar(itens: list, amb: Ambiente) -> list:
    return [checar_item(i, amb) for i in itens]


def falta_obrigatorio(resultados: list) -> bool:
    return any(r.obrigatorio and r.status != OK for r in resultados)


# ---------- instalação ----------

def baixar(info: dict, saida: Callable[[str], None]) -> bool:
    """Baixa por https para um temporário ao lado do destino e troca de forma atômica; confere sha256."""
    destino = Path(info["destino"])
    destino.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".baixando-", dir=destino.parent)
    h = hashlib.sha256()
    try:
        with os.fdopen(fd, "wb") as f, urllib.request.urlopen(info["url"], timeout=60) as r:
            while bloco := r.read(1 << 20):
                f.write(bloco)
                h.update(bloco)
        if info.get("sha256") and h.hexdigest() != info["sha256"]:
            saida("    sha256 não confere: arquivo descartado.")
            return False
        os.replace(tmp, destino)
        return True
    except OSError as e:
        saida(f"    download falhou: {e}")
        return False
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _perguntar(pergunta: str) -> bool:
    try:
        return input(pergunta).strip().lower() in ("s", "sim", "y")
    except EOFError:
        return False


def instalar(itens: list, amb: Ambiente, nomes: list | None = None, sim: bool = False, dry_run: bool = False,
             interativo: bool | None = None, perguntar: Callable[[str], bool] = _perguntar,
             saida: Callable[[str], None] = print, baixador: Callable = baixar) -> int:
    """Instala, na ordem das dependências, o que falta. Nunca roda item da pessoa nem comando de admin."""
    interativo = sys.stdin.isatty() if interativo is None else interativo
    por_id = {i.id: i for i in itens}
    desconhecidos = [n for n in nomes or [] if n not in por_id]
    if desconhecidos:
        saida(f"Item desconhecido: {', '.join(desconhecidos)}. Itens: {', '.join(por_id)}.")
        return 2
    estado = {r.id: r for r in checar(itens, amb)}
    alvos = nomes or [i for i, r in estado.items() if r.status != OK]
    ordem = ordem_topologica({i.id: i.depende_de or [] for i in itens}, alvos)
    if all(estado[i].status == OK for i in ordem):
        saida("Nada a instalar: tudo ok.")
        return 0
    falhou, bloqueados = False, set()
    for iid in ordem:
        res = checar_item(por_id[iid], amb)
        if res.status == OK:
            continue
        pendentes = [d for d in por_id[iid].depende_de or [] if d in bloqueados]
        if pendentes:
            saida(f"- {iid}: espera {', '.join(pendentes)}.")
            bloqueados.add(iid)
            continue
        feito = _instalar_um(res, amb, sim, dry_run, interativo, perguntar, saida, baixador)
        if feito is False:
            falhou = True
        if feito is not True or checar_item(por_id[iid], amb).status != OK:
            bloqueados.add(iid)
    if dry_run:
        saida("(--dry-run: nada foi rodado)")
        return 0
    final = checar([por_id[i] for i in ordem], amb)
    if falhou:
        saida("Algum passo falhou: confira a mensagem acima e rode `checar`.")
        return 1
    return 1 if falta_obrigatorio(final) else 0


def _instalar_um(res: Resultado, amb: Ambiente, sim: bool, dry_run: bool, interativo: bool,
                 perguntar: Callable, saida: Callable, baixador: Callable) -> bool | None:
    """True instalou, False falhou, None só mostrou (pessoa, admin, não suportado ou sem ok)."""
    if res.status == NAO_SUPORTADO:
        saida(f"- {res.id}: não suportado nesta máquina: {res.fazer}")
        return None
    if res.tipo in NUNCA_RODA or not (res.comandos or res.baixar):
        saida(f"- {res.id}: é com você: {res.fazer or res.descricao}")
        return None
    if res.admin and not amb.admin:
        saida(f"- {res.id}: precisa de administrador; rode você: {res.fazer}")
        return None
    for cmd in res.comandos:
        motivo = proibido(cmd)
        if motivo:
            saida(f"- {res.id}: recusado ({motivo}).")
            return False
    saida(f"- {res.id}: {res.fazer}")
    if dry_run:
        return None
    if not (sim or (interativo and perguntar("    Rodar agora? [s/N] "))):
        saida(f"    (só mostrado: com o ok da pessoa, rode `instalar --sim {res.id}`)")
        return None
    for cmd in res.comandos:
        codigo = amb.rodar(cmd)
        if codigo != 0:
            saida(f"    falhou (código {codigo}).")
            return False
    if res.baixar and not baixador(res.baixar, saida):
        return False
    for p in res.path:
        saida(f"    ponha no PATH: {instrucao_path(p, amb)}")
    saida("    feito.")
    return True


# ---------- saída ----------

def configurar_saida() -> None:
    """Acentos sem quebrar no console do Windows (cp1252)."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def em_tabela(resultados: list, amb: Ambiente) -> str:
    p = amb.resumo()
    cab = (f"Plataforma: {p['sistema']} {p['arch']}" + (" (Rosetta)" if p["rosetta"] else "")
           + (f", {p['distro']}" if p["distro"] else "") + (" (WSL)" if p["wsl"] else "")
           + f", GPU {p['gpu']}, gerenciadores: {', '.join(p['gerenciadores']) or 'nenhum'}")
    linhas = [("Item", "Status", "Versao", "O que fazer")]
    for r in resultados:
        fazer = r.fazer if r.status != OK else r.nota
        linhas.append((r.id + ("" if r.obrigatorio else " (opcional)"), r.status, r.versao, fazer))
    larg = [max(len(x[c]) for x in linhas) for c in range(3)]
    out = [cab, ""] + [" | ".join(x[c].ljust(larg[c]) for c in range(3)) + " | " + x[3] for x in linhas]
    out.insert(3, "-+-".join("-" * n for n in larg) + "-+-" + "-" * 11)
    resumo = ("Falta algo obrigatório: rode `instalar`." if falta_obrigatorio(resultados)
              else "Tudo o que é obrigatório está ok.")
    return "\n".join([*out, "", resumo])


def em_json(resultados: list, amb: Ambiente) -> str:
    return json.dumps({"versao_motor": VERSAO, "plataforma": amb.resumo(), "ok": not falta_obrigatorio(resultados),
                       "requisitos": [r.como_dict() for r in resultados]}, ensure_ascii=False, indent=2)


def bloco_prompt(projeto: dict) -> str:
    """Bloco curto e específico do README: bootstrap por SO, ok item a item, nada aceito pela pessoa."""
    script = projeto.get("script", "scripts/requisitos.py")
    pasta = script.rsplit("/", 1)[0] if "/" in script else "."
    clone = ""
    if projeto.get("repo"):
        clone = ("Se o repositório ainda não estiver clonado, clone com o GitHub CLI: "
                 f"`gh repo clone {projeto['repo']}` "
                 "(instale o gh com `winget install --id GitHub.cli -e` no Windows, pelo https://cli.github.com no "
                 "macOS e pelo pacote `gh` da sua distro no Linux; o `gh auth login` é comigo). ")
    return (
        "> **Cole isto na sua IA antes de instalar:**\n>\n"
        f'> "Confira os requisitos do {projeto["nome"]}. {clone}'
        f"No Windows, rode `powershell -ExecutionPolicy Bypass -File {pasta}/bootstrap.ps1`; no macOS ou Linux, "
        f"rode `sh {pasta}/bootstrap.sh`. Ele confere e, com o meu ok, instala o uv, e depois mostra o que falta. "
        f"Para cada item, peça meu ok e rode `uv run {script} instalar --sim <item>`. Itens marcados como é com "
        "você (licença, consentimento ou voz, login, permissões do sistema, senha de administrador): me explique "
        'e espere eu fazer. Não aceite licenças nem declarações por mim e não mexa em senhas, chaves ou tokens."'
    )


# ---------- CLI ----------

def main(argv: list | None = None, amb: Ambiente | None = None) -> int:
    configurar_saida()
    ap = argparse.ArgumentParser(prog="requisitos.py", description=(
        "Confere e instala, com o seu ok, o que este repositório precisa (Linux, Windows e macOS). "
        "Nunca aceita licença, consentimento ou login por você."))
    ajuda_arq = "requisitos.toml (caminho ou URL https); padrão: o mais próximo"
    ap.add_argument("--arquivo", help=ajuda_arq)
    ap.add_argument("--version", action="version", version=f"requisitos.py {VERSAO}")
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("--arquivo", default=argparse.SUPPRESS, help=ajuda_arq)
    sub = ap.add_subparsers(dest="comando", required=True)
    p = sub.add_parser("plataforma", help="mostra o que foi detectado nesta máquina")
    p.add_argument("--json", action="store_true")
    sub.add_parser("validar", parents=[comum], help="confere o requisitos.toml (código 2 se inválido)")
    c = sub.add_parser("checar", parents=[comum], help="lista cada requisito; código 1 se faltar algo obrigatório")
    c.add_argument("--json", action="store_true", help="saída em JSON")
    i = sub.add_parser("instalar", parents=[comum], help="instala o que falta, na ordem, pedindo o seu ok")
    i.add_argument("item", nargs="*", help="só estes itens (e as suas dependências)")
    i.add_argument("--sim", action="store_true", help="roda sem perguntar (nunca aceita licença nem declaração)")
    i.add_argument("--dry-run", action="store_true", help="só mostra o plano; não roda nada")
    sub.add_parser("prompt", parents=[comum], help='imprime o bloco "Cole isto na sua IA" para o README')
    args = ap.parse_args(argv)
    amb = amb or ambiente_real()
    if args.comando == "plataforma":
        r = amb.resumo()
        print(json.dumps(r, ensure_ascii=False, indent=2) if args.json
              else "\n".join(f"{k}: {', '.join(v) if isinstance(v, list) else v}" for k, v in r.items()))
        return 0
    try:
        projeto, itens = carregar(args.arquivo or achar_toml())
    except (ReceitaInvalida, OSError) as e:
        print(f"Receita inválida:\n{e}", file=sys.stderr)
        return 2
    if args.comando == "validar":
        print(f"receita ok: {len(itens)} requisitos, {', '.join(SISTEMAS)} cobertos")
        return 0
    if args.comando == "prompt":
        print(bloco_prompt(projeto))
        return 0
    if args.comando == "checar":
        res = checar(itens, amb)
        print(em_json(res, amb) if args.json else em_tabela(res, amb))
        return 1 if falta_obrigatorio(res) else 0
    return instalar(itens, amb, nomes=args.item, sim=args.sim, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())

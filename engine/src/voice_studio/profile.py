"""Perfil de voz: amostra normalizada + consentimento + ajustes, numa pasta fora do repositório."""

from __future__ import annotations

import json
import os
import re
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from . import audio, consent
from .errors import VoiceError

HOME_ENV = "VOICE_STUDIO_HOME"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")
PROFILE_FILE = "perfil.json"
SAMPLE_FILE = "voz-ref.wav"
MAX_BYTES = 64 * 1024
DEFAULT_ADJUSTS = {"velocidade": 1.08, "takes": 3}

# origem, destino, início, duração
Extract = Callable[[Path, Path, float, float], None]


def default_base() -> Path:
    """`VOICE_STUDIO_HOME` (se definida) ou `~/.voice-studio/perfis`."""
    env = os.environ.get(HOME_ENV)
    return Path(env).expanduser() if env else Path.home() / ".voice-studio" / "perfis"


def _resolve_base(base: Path | None) -> Path:
    """Resolve a base e recusa pastas dentro de um repositório git (amostra é dado pessoal)."""
    root = (base if base is not None else default_base()).expanduser().resolve()
    for folder in (root, *root.parents):
        if (folder / ".git").exists():
            raise VoiceError(
                f"A pasta de perfis não pode ficar dentro de um repositório git ({folder}). "
                "Use uma pasta fora do projeto (ex.: ~/.voice-studio/perfis)."
            )
    return root


def check_name(nome: str) -> str:
    if not isinstance(nome, str) or not NAME_RE.fullmatch(nome):
        raise VoiceError(
            "Nome de perfil inválido: use de 1 a 40 caracteres em minúsculas, números, "
            "'-' ou '_', começando por letra ou número."
        )
    return nome


def _default_extract(origem: Path, destino: Path, start: float, duration: float) -> None:
    audio.extract_sample(origem, destino, start, duration)


def create(nome: str, origem: Path, confirm: bool, base: Path | None = None,
           start: float = 0.0, duration: float = 28.0, ajustes: dict | None = None,
           extract: Extract = _default_extract) -> dict:
    """Cria o perfil: só com consentimento, nunca sobrescreve, escreve só em `<base>/<nome>/`."""
    check_name(nome)
    consent.require_consent(confirm, origem)
    root = _resolve_base(base)
    folder = root / nome
    if folder.exists():
        raise VoiceError(f"O perfil '{nome}' já existe; escolha outro nome (nada é sobrescrito).")
    settings = {**DEFAULT_ADJUSTS, **(ajustes or {})}
    now = datetime.now(UTC).isoformat(timespec="seconds")
    data = {
        "nome": nome,
        "criado_em": now,
        "consentimento": {"confirmado_pelo_usuario": True, "em": now},
        "amostra": SAMPLE_FILE,
        "ajustes": settings,
        "vocabularios": {},
    }
    root.mkdir(parents=True, exist_ok=True)
    folder.mkdir()
    try:
        extract(origem, folder / SAMPLE_FILE, start, duration)
        (folder / PROFILE_FILE).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except BaseException:
        shutil.rmtree(folder, ignore_errors=True)  # não deixa perfil pela metade
        raise
    return data


def load(nome: str, base: Path | None = None) -> dict:
    """Lê e valida o `perfil.json`; o caminho da amostra sai resolvido em `amostra_path`."""
    check_name(nome)
    folder = _resolve_base(base) / nome
    file = folder / PROFILE_FILE
    if not file.is_file():
        raise VoiceError(f"Perfil '{nome}' não encontrado (crie com `perfil criar`).")
    if file.stat().st_size > MAX_BYTES:
        raise VoiceError(f"perfil.json grande demais no perfil '{nome}'.")
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VoiceError(f"perfil.json corrompido no perfil '{nome}': {exc}") from exc
    if (not isinstance(data, dict) or data.get("nome") != nome
            or not isinstance(data.get("consentimento"), dict)
            or data.get("amostra") != SAMPLE_FILE):
        raise VoiceError(f"perfil.json inválido no perfil '{nome}'.")
    if not (folder / SAMPLE_FILE).is_file():
        raise VoiceError(f"Perfil '{nome}' sem a amostra {SAMPLE_FILE}.")
    data["amostra_path"] = str(folder / SAMPLE_FILE)
    return data


def list_profiles(base: Path | None = None) -> list[str]:
    """Nomes dos perfis em ordem; ignora pastas sem `perfil.json`."""
    root = _resolve_base(base)
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir()
                  if p.is_dir() and NAME_RE.fullmatch(p.name) and (p / PROFILE_FILE).is_file())

"""Perfil de voz: amostra normalizada + consentimento + ajustes, numa pasta fora do repositório."""

from __future__ import annotations

import json
import os
import re
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from . import audio, consent, languages, vocab
from .errors import VoiceError

HOME_ENV = "VOICE_STUDIO_HOME"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")
PROFILE_FILE = "perfil.json"
SAMPLE_FILE = "voz-ref.wav"
MAX_BYTES = 64 * 1024
DEFAULT_ADJUSTS = {"velocidade": 1.08, "takes": 3}

# origem, destino, início, duração
Extract = Callable[[Path, Path, float, float], None]


def check_adjusts(ajustes: object) -> dict:
    """Valida `ajustes`: `velocidade` número > 0, `takes` inteiro >= 1; chave desconhecida é erro."""
    if not isinstance(ajustes, dict):
        raise VoiceError("Ajustes do perfil inválidos: esperado um objeto JSON.")
    unknown = sorted(set(ajustes) - set(DEFAULT_ADJUSTS))
    if unknown:
        raise VoiceError(f"Ajustes desconhecidos no perfil: {', '.join(map(str, unknown))} "
                         f"(aceitos: {', '.join(DEFAULT_ADJUSTS)}).")
    out = dict(DEFAULT_ADJUSTS) | ajustes
    speed, takes = out["velocidade"], out["takes"]
    if isinstance(speed, bool) or not isinstance(speed, int | float) or not speed > 0 \
            or speed == float("inf"):
        raise VoiceError("Ajuste 'velocidade' inválido: use um número maior que zero.")
    if isinstance(takes, bool) or not isinstance(takes, int) or takes < 1:
        raise VoiceError("Ajuste 'takes' inválido: use um inteiro maior ou igual a 1.")
    return out


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
    settings = check_adjusts(ajustes or {})
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
    try:
        folder.mkdir()
    except FileExistsError as exc:  # ex.: symlink pendente em <base>/<nome>
        raise VoiceError(
            f"Não foi possível criar a pasta do perfil '{nome}': já existe um item "
            "(talvez um link quebrado) nesse caminho. Remova-o ou escolha outro nome."
        ) from exc
    except OSError as exc:
        raise VoiceError(f"Não foi possível criar a pasta do perfil '{nome}': {exc}") from exc
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
    data["ajustes"] = check_adjusts(data.get("ajustes", {}))
    data["amostra_path"] = str(folder / SAMPLE_FILE)
    return data


def list_profiles(base: Path | None = None) -> list[str]:
    """Nomes dos perfis em ordem; ignora pastas sem `perfil.json`."""
    root = _resolve_base(base)
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir()
                  if p.is_dir() and NAME_RE.fullmatch(p.name) and (p / PROFILE_FILE).is_file())


def _vocab_name(lang: str) -> str:
    return f"vocab.{lang}.json"


def set_vocabulary(nome: str, lang: str, arquivo: Path, base: Path | None = None) -> dict:
    """Valida o mapa, grava `vocab.<lang>.json` na pasta do perfil e registra em `perfil.json`.

    Escreve só dentro de `<base>/<nome>/`; qualquer falha deixa o perfil como estava.
    """
    languages.require(lang)
    mapping = vocab.load(arquivo)  # valida tamanho, tipos e chaves antes de tocar no perfil
    if not mapping:
        raise VoiceError(f"O vocabulário está vazio: {arquivo}")
    data = load(nome, base)
    folder = Path(data["amostra_path"]).parent
    target = folder / _vocab_name(lang)
    previous = target.read_bytes() if target.is_file() else None
    saved = {k: v for k, v in data.items() if k != "amostra_path"}
    saved["vocabularios"] = {**(saved.get("vocabularios") or {}), lang: _vocab_name(lang)}
    tmp_vocab, tmp_profile = folder / ".vocab.tmp", folder / ".perfil.tmp"
    try:
        tmp_vocab.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_profile.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_vocab.replace(target)
        try:
            tmp_profile.replace(folder / PROFILE_FILE)
        except BaseException:
            if previous is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(previous)
            raise
    except OSError as exc:
        raise VoiceError(f"Não foi possível gravar o vocabulário no perfil '{nome}': {exc}") from exc
    finally:
        tmp_vocab.unlink(missing_ok=True)
        tmp_profile.unlink(missing_ok=True)
    return load(nome, base)


def vocabulary(perfil: dict, lang: str) -> dict[str, str]:
    """Mapa do idioma pedido (`{}` se não houver); nunca mistura mapas de idiomas diferentes."""
    languages.require(lang)
    registered = (perfil.get("vocabularios") or {}).get(lang)
    if registered is None:
        return {}
    if registered != _vocab_name(lang):
        raise VoiceError(f"Vocabulário '{lang}' inválido no perfil '{perfil.get('nome')}'.")
    return vocab.load(Path(perfil["amostra_path"]).parent / registered)

"""Vocabulário de pronúncia: troca a grafia da tela pela grafia falada, só no texto da voz."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .errors import VoiceError

MAX_BYTES = 256 * 1024
MAX_ENTRIES = 2000


def load(path: Path) -> dict[str, str]:
    """Lê e valida um `pronuncia.json` (mapa texto -> texto)."""
    if not path.is_file():
        raise VoiceError(f"Vocabulário não encontrado: {path}")
    if path.stat().st_size > MAX_BYTES:
        raise VoiceError(f"Vocabulário grande demais (máx. {MAX_BYTES // 1024} KB): {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VoiceError(f"Vocabulário com JSON inválido ({path}): {exc}") from exc
    return clean(raw)


def clean(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise VoiceError("O vocabulário deve ser um objeto JSON {\"termo\": \"como falar\"}.")
    if len(raw) > MAX_ENTRIES:
        raise VoiceError(f"Vocabulário com mais de {MAX_ENTRIES} entradas.")
    out: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise VoiceError("Vocabulário: chaves e valores precisam ser texto.")
        key, value = key.strip(), value.strip()
        if not key or not value:
            raise VoiceError("Vocabulário: chave ou valor vazio.")
        out[key] = value
    return out


def _case_sensitive(term: str) -> bool:
    """Siglas em maiúsculas ('IA', 'PR') só casam em maiúsculas: 'ia' (verbo) fica intacto."""
    letters = [c for c in term if c.isalpha()]
    return len(letters) >= 2 and all(c.isupper() for c in letters)


def apply_spoken(text: str, mapping: dict[str, str]) -> str:
    """Troca termos por palavra inteira, em uma só passada, preservando o resto do texto."""
    if not mapping:
        return text
    exact = {k: v for k, v in mapping.items() if _case_sensitive(k)}
    folded = {k.casefold(): v for k, v in mapping.items() if not _case_sensitive(k)}
    parts = []
    for term in sorted(mapping, key=len, reverse=True):
        body = re.escape(term)
        parts.append(body if _case_sensitive(term) else f"(?i:{body})")
    pattern = re.compile(r"(?<!\w)(?:" + "|".join(parts) + r")(?!\w)")

    def swap(match: re.Match[str]) -> str:
        found = match.group(0)
        return exact.get(found) or folded.get(found.casefold()) or found

    return pattern.sub(swap, text)

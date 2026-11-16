"""Catálogo único de idiomas: código, nome, caracteres por segundo e se já foi validado."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import VoiceError


@dataclass(frozen=True)
class Lang:
    code: str
    nome: str
    cps: float  # caracteres (com espaços) por segundo
    validated: bool  # True só quando medido com falas reais


# pt e en foram medidos em falas reais com o XTTS-v2. Os valores de es, fr, de e it NÃO foram
# medidos: são estimativas. Recalibrar com falas reais quando houver teste manual.
CATALOG: dict[str, Lang] = {
    lang.code: lang for lang in (
        Lang("pt", "português", 15.0, True),
        Lang("en", "inglês", 12.5, True),
        Lang("es", "espanhol", 15.0, False),
        Lang("fr", "francês", 14.0, False),
        Lang("de", "alemão", 13.0, False),
        Lang("it", "italiano", 15.0, False),
    )
}


def require(code: str) -> Lang:
    """Devolve o idioma ou falha listando os aceitos."""
    lang = CATALOG.get(code)
    if lang is None:
        raise VoiceError(f"Idioma não suportado: {code} (use {', '.join(sorted(CATALOG))}).")
    return lang


def is_validated(code: str) -> bool:
    return require(code).validated

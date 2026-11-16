"""Falar: texto digitado -> fala na voz do perfil, com o vocabulário do idioma da fala."""

from __future__ import annotations

import json
from pathlib import Path

from . import consent, languages, profile
from .errors import VoiceError
from .synth import Synth, speak


def avulso(ref: Path, confirm: bool) -> dict:
    """Perfil descartável para uma amostra avulsa (`--ref`): exige a confirmação do usuário."""
    consent.require_consent(confirm, ref)
    return {"nome": None, "amostra_path": str(ref), "vocabularios": {},
            "ajustes": dict(profile.DEFAULT_ADJUSTS)}


def resolve(nome: str | None, ref: Path | None, confirm: bool, base: Path | None = None) -> dict:
    """Perfil salvo (consentimento já registrado nele) ou amostra avulsa; sem nenhum, falha."""
    if nome and ref:
        raise VoiceError("Use --perfil ou --ref, não os dois.")
    if nome:
        return profile.load(nome, base)
    if ref:
        return avulso(ref, confirm)
    raise VoiceError("Informe --perfil NOME (ou --ref AUDIO com --confirm-own-voice): "
                     "sem amostra, sem voz.")


def load_texts(texto: str | None, arquivo: Path | None) -> list[str]:
    """Textos de `falas.json` (lista ou {"lines": [...]}) ou o texto digitado."""
    if bool(texto) == bool(arquivo):
        raise VoiceError("Informe o texto OU --arquivo falas.json (um dos dois).")
    if texto:
        return [texto]
    assert arquivo is not None
    if not arquivo.is_file():
        raise VoiceError(f"Arquivo de falas não encontrado: {arquivo}")
    try:
        raw = json.loads(arquivo.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VoiceError(f"Falas com JSON inválido: {exc}") from exc
    texts = raw.get("lines") if isinstance(raw, dict) else raw
    if not isinstance(texts, list) or not texts or not all(isinstance(t, str) for t in texts):
        raise VoiceError("O arquivo deve ser uma lista de textos ou {\"lines\": [...]}.")
    return texts


def run(textos: list[str], perfil: dict, lang: str, out: Path, synth: Synth,
        takes: int | None = None) -> list[dict]:
    """Gera uma fala por texto; o sintetizador entra por parâmetro (VOZ-09)."""
    language = languages.require(lang)
    settings = profile.check_adjusts(perfil.get("ajustes", {}))
    result = speak(textos, Path(perfil["amostra_path"]), lang, out, synth,
                   profile.vocabulary(perfil, lang), takes or settings["takes"],
                   settings["velocidade"])
    return [{"linha": r.index, "arquivo": r.path.name, "segundos": r.seconds, "ok": r.ok,
             "validated": language.validated, "falado": r.spoken} for r in result]


def avisos(lang: str, relatorio: list[dict]) -> list[str]:
    """Avisos para o usuário: idioma não validado e linhas suspeitas (nunca silenciadas)."""
    out = []
    if not languages.is_validated(lang):
        out.append(f"O idioma '{lang}' ainda não teve a qualidade verificada com falas reais: "
                   "ouça o resultado com atenção.")
    bad = [r["linha"] for r in relatorio if not r["ok"]]
    if bad:
        out.append(f"Linhas {bad} ficaram fora da duração esperada em todas as variações "
                   "(possível fala cortada ou repetida): confira o áudio.")
    return out

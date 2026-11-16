"""Traduzir: áudio ou vídeo -> outro idioma com a voz do perfil, em duas fases.

Fase 1 (`prepare`): transcreve localmente e grava os segmentos com `source` e `text` vazio.
O agente (ou o usuário) traduz `source` para `text`; só texto passa pelo diálogo (VOZ-03).
Fase 2 (`render`): valida a tradução e dubla com a voz do perfil e o vocabulário do idioma.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from . import audio, dub, languages, profile, transcribe
from .errors import VoiceError
from .synth import Synth

Transcriber = Callable[[Path, Path | None, str], list[dict]]


def check_segments(segmentos: Path) -> list[dub.Segment]:
    """Valida os segmentos traduzidos (aponta o número do segmento sem `text`)."""
    return dub.load_segments(segmentos)


def prepare(entrada: Path, perfil: dict, de: str, para: str, model: Path | None,
            destino: Path = Path("segments.json"),
            transcriber: Transcriber | None = None) -> list[dict]:
    """Fase 1: transcreve `entrada` (idioma `de`) e grava `destino` com `text` vazio."""
    languages.require(para)
    languages.require(de)
    if not perfil.get("amostra_path"):
        raise VoiceError("Perfil sem amostra de voz.")
    if destino.exists():
        raise VoiceError(f"{destino} já existe (pode conter sua tradução): use --out para "
                         "outro caminho ou apague o arquivo.")
    segments = (transcriber or transcribe.transcribe)(entrada, model, de)
    if not segments:
        raise VoiceError("Nenhuma fala encontrada na entrada.")
    rows = [{"start": s["start"], "end": s["end"], "source": s["source"], "text": ""}
            for s in segments]
    destino.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def render(entrada: Path, segmentos: Path, perfil: dict, para: str, out: Path, synth: Synth,
           takes: int | None = None) -> dict:
    """Fase 2: dubla `entrada` com a voz do perfil; o sintetizador entra por parâmetro (VOZ-09)."""
    language = languages.require(para)
    segs = check_segments(segmentos)
    settings = profile.check_adjusts(perfil.get("ajustes", {}))
    chosen = takes if takes is not None else settings["takes"]
    report = dub.dub(entrada, segs, Path(perfil["amostra_path"]), para, out, synth,
                     out.parent / f".{out.stem}-work", profile.vocabulary(perfil, para), chosen)
    report["validated"] = language.validated
    return report


def default_out(entrada: Path) -> Path:
    """Saída padrão: vídeo vira `dublado.mp4`; só áudio vira `dublado.m4a`."""
    return Path("dublado.mp4" if audio.has_video(entrada) else "dublado.m4a")


def avisos(para: str, report: dict) -> list[str]:
    """Avisos nunca silenciados: idioma não validado, estouro de tempo e falas suspeitas."""
    out = []
    if not languages.is_validated(para):
        out.append(f"O idioma '{para}' ainda não teve a qualidade verificada com falas reais: "
                   "ouça o resultado com atenção.")
    if report["overflow"]:
        out.append(f"Segmentos {report['overflow']} ficaram maiores que o tempo disponível: "
                   "encurte o texto traduzido.")
    if report["suspect_takes"]:
        out.append(f"Segmentos {report['suspect_takes']} ficaram fora da duração esperada em "
                   "todas as variações (possível fala cortada ou repetida): confira o áudio.")
    return out

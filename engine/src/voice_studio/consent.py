"""Consentimento de voz e aceite da licença do modelo. Nada é aceito em nome de ninguém."""

from __future__ import annotations

import os
from pathlib import Path

from .errors import VoiceError

CPML_URL = "https://coqui.ai/cpml"
LICENSE_ENV = "VOICE_STUDIO_ACCEPT_CPML"


def require_consent(confirmed: bool, ref: Path | None) -> Path:
    """Sem referência, sem voz; sem a confirmação de que a voz é sua (ou autorizada), erro."""
    if ref is None or not ref.is_file():
        raise VoiceError("Informe --ref com um áudio de referência existente: sem amostra, sem voz.")
    if not confirmed:
        raise VoiceError(
            "Passe --confirm-own-voice para confirmar que a voz da amostra é sua "
            "ou que você tem autorização para cloná-la."
        )
    return ref


def require_license(accepted: bool, env: dict[str, str] | None = None) -> None:
    """O XTTS-v2 é Coqui CPML (uso não comercial). O aceite é do usuário, explícito."""
    source = os.environ if env is None else env
    if accepted or source.get(LICENSE_ENV) == "1":
        return
    raise VoiceError(
        f"O modelo XTTS-v2 usa a licença Coqui CPML (somente uso não comercial): {CPML_URL}. "
        f"Se você concorda, passe --accept-cpml ou defina {LICENSE_ENV}=1."
    )

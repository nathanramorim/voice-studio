"""Erros do domínio, com mensagem pronta para o usuário."""


class VoiceError(Exception):
    """Falha esperada (entrada inválida, falta de consentimento, ferramenta ausente)."""

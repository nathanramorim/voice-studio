# ADR-0003: Python sempre via uv

- **Data:** 2026-11-19 (retroativa: decisão em vigor desde o início do projeto)
- **Status:** `aprovado`
- **Regras afetadas (IDs da constitution):** `ARQ-04`, `COD-02`, Regra 7
- **Autor / Responsável:** dono do repositório

## Contexto

O motor roda na máquina de quem instala o plugin e depende de PyTorch e do `coqui-tts`, que só funcionam numa faixa estreita de versões (`requires-python = ">=3.11,<3.12"`, `torch<2.9`). Instruções com pip e venv manual quebram e poluem o ambiente.

## Opções Consideradas

1. **pip + requirements.txt:** frágil, global, sem lock.
2. **uv com `engine/pyproject.toml` e `engine/uv.lock`:** ambiente isolado, versão de Python escolhida pelo `uv`, motor pesado no extra `xtts`.

## Decisão

Opção 2, já em uso: `uv run --extra xtts voice-studio ...` em `engine/`; testes com `uv run pytest`. Nunca escrever pip nas instruções.

## Consequências

- **Positivas:** um comando prepara e roda tudo; lock reprodutível.
- **Negativas / Trade-offs:** exige `uv` instalado; no Apple Silicon é preciso fixar `--python cpython-3.11-macos-aarch64-none`.
- **Ações de acompanhamento:** README lista `uv` em `## Requisitos`.

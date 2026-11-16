---
description: Cria e gerencia perfis de voz (amostra, consentimento e vocabulário por idioma).
argument-hint: "criar NOME ORIGEM | listar | mostrar NOME | vocab NOME ARQUIVO --lang pt"
---

Siga a skill `voice-studio` (seção "Perfil de voz"): pergunte ao usuário se a voz é dele ou autorizada e só então passe `--confirm-own-voice`. Rode `uv run --python 3.11 --extra xtts voice-studio perfil $ARGUMENTS` em `${CLAUDE_PLUGIN_ROOT}/engine`. Peça ao usuário para ouvir a amostra do perfil.

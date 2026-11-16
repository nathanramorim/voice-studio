---
description: Gera narração com a sua voz clonada (local, grátis), a partir de uma lista de falas.
argument-hint: "[falas.json] [--ref voice-ref.wav] [--lang pt|en]"
---

Siga a skill `voice-studio`: confirme o consentimento da voz e o aceite da licença CPML com o usuário, e só então rode `uv run --python 3.11 --extra xtts voice-studio speak $ARGUMENTS` em `${CLAUDE_PLUGIN_ROOT}/engine` (Apple Silicon: `--python cpython-3.11-macos-aarch64-none`). Peça ao usuário para ouvir as falas.

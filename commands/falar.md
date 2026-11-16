---
description: Fala um texto digitado com a voz de um perfil, no idioma escolhido.
argument-hint: '"texto" --perfil NOME [--lang pt|en|es|fr|de|it]'
---

Siga a skill `voice-studio` (seção "Falar um texto"): confirme com o usuário o aceite da licença CPML e só então rode `uv run --python 3.11 --extra xtts voice-studio falar $ARGUMENTS --accept-cpml` em `${CLAUDE_PLUGIN_ROOT}/engine`. Avise se o idioma não for validado e peça ao usuário para ouvir. Código de saída `2`: há fala suspeita, confira o `report.json`.

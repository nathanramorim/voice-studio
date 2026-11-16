---
description: Traduz um áudio ou vídeo para outro idioma com a voz de um perfil, em duas fases.
argument-hint: "ENTRADA --para en --perfil NOME [--de pt] [--model ggml.bin]"
---

Siga a skill `voice-studio` (seção "Traduzir áudio ou vídeo"): rode a fase 1 (`traduzir $ARGUMENTS`), traduza você mesmo `source` para `text` no `segments.json` (só texto; nunca anexe áudio), confirme a licença CPML com o usuário e rode a fase 2 com `--segmentos segments.json --accept-cpml`. Mostre `overflow` e `suspect_takes` do relatório e peça ao usuário para ouvir.

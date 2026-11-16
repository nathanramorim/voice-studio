---
description: Como cumprir consentimento da voz, licença do modelo, execução local e privacidade dos artefatos.
globs: ["engine/**", "skills/**", "commands/**", ".gitignore", "README.md", "NOTICE.md"]
regras: [VOZ-01, VOZ-02, VOZ-03, VOZ-04]
---

# Guia Prático — Consentimento, Licença e Privacidade da Voz

Procedimentos para `VOZ-01` a `VOZ-04` de `sdd/memory/constitution.md` (`GOV-04`).

## Consentimento (`VOZ-01`)
- Todo comando que gera voz chama `consent.require_consent` antes de tocar no motor; sem `--ref` existente ou sem `--confirm-own-voice`, erro claro.
- O agente pergunta ao usuário **uma vez** se a voz é dele (ou autorizada) e só então passa a flag. Nunca por conta própria, nunca em script de teste real.

## Licença do modelo (`VOZ-02`)
- `consent.require_license` roda antes de `xtts_synth`; `COQUI_TOS_AGREED` só é definido depois dele.
- Não distribua pesos, não os coloque em releases e não os versione (`.gitignore` já bloqueia `bin`, `pth`, `safetensors`).
- README e `NOTICE.md` dizem: código MIT, modelo CPML (não comercial). Trocar de motor é implementar `synth.Synth`.

## Local por padrão (`VOZ-03`)
- Nenhum cliente HTTP de voz no motor. Transcrição só com `whisper-cli` local.
- O LLM recebe e devolve texto: transcrição e tradução. Nunca anexe áudio à conversa.

## Privacidade dos artefatos (`VOZ-04`)
- Amostras, falas e vídeos ficam na pasta de trabalho do usuário e nunca em `exemplos/` ou `engine/tests/` (os testes geram seno sintético).
- Antes de cada commit: `git ls-files | grep -Ei '\.(wav|mp3|m4a|mp4|mov)$'` deve vir vazio.
- Exemplos e logs não carregam nome de cliente ou de projeto de terceiros (`SEG-05`).

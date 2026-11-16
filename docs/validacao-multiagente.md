# Validação multiagente

Checklist para confirmar que a skill funciona em cada agente. Marque só o que você viu funcionar; o README não afirma nada que não esteja registrado aqui.

Passos (em cada agente):
1. Abrir o repositório.
2. O agente leu `skills/voice-studio/SKILL.md` (pergunte "o que você sabe fazer aqui?").
3. Rodar `voice-studio --help` (em `engine/`) e ver `perfil`, `falar` e `traduzir`.
4. Criar um perfil (`perfil criar`): o agente pergunta o consentimento antes de passar `--confirm-own-voice`.
5. Falar uma frase (`falar`): o agente pergunta o aceite da licença CPML antes de passar `--accept-cpml`, e você ouve o resultado.

| Agente | Abrir o repo | Leu a skill | `--help` | Criar perfil | Falar uma frase | Data | O que funcionou / o que falhou |
|---|---|---|---|---|---|---|---|
| Claude Code | [ ] | [ ] | [ ] | [ ] | [ ] | | |
| agy (Antigravity) | [ ] | [ ] | [ ] | [ ] | [ ] | | |
| Codex | [ ] | [ ] | [ ] | [ ] | [ ] | | |

Enquanto uma linha não estiver marcada, o agente conta como "instruções prontas, não validado".

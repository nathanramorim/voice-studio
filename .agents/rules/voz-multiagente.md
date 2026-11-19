---
description: Como manter um só corpo de skill e adaptadores finos para Claude Code, agy (Gemini) e Codex.
globs: ["scripts/**", "README.md", "skills/**", "commands/**", "AGENTS.md", "CLAUDE.md", "GEMINI.md", ".claude-plugin/**", ".gemini/**"]
regras: [VOZ-08, VOZ-10, DUP-10]
---

# Guia Prático — Um Plugin, Vários Agentes

Procedimentos para `VOZ-08`, `VOZ-10` e `DUP-10` (`GOV-04`).

- **Fonte única:** `skills/voice-studio/SKILL.md` (e `references/`). Nenhum agente tem cópia do corpo.
- **Claude Code:** plugin via `.claude-plugin/` e `commands/`.
- **agy (Antigravity/Gemini):** `GEMINI.md` aponta para a skill e para as regras; mesma CLI.
- **Codex:** `AGENTS.md` aponta para a skill; mesma CLI.
- Adaptador novo = arquivo fino que referencia a skill, nunca duplica instruções.
- A CLI (`voice-studio ...`) é o contrato comum e mantém os mesmos argumentos em todos os agentes (`ARQ-06`).

## Prompt que usa script (`VOZ-10`)

- O que é determinístico (conferir programa, versão, arquivo, modelo) vira script em `scripts/`, só com a biblioteca padrão, para rodar antes do clone (`uv run <url-raw> ...`).
- O prompt para a IA (no README, em quote, antes da instalação) só chama o script: `checar` e, com o ok da pessoa, `instalar`.
- Licença, declaração e chave são do tipo "seu": o script explica e nunca roda (`VOZ-01`, `VOZ-02`).

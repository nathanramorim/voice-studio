---
description: Como manter um só corpo de skill e adaptadores finos para Claude Code, agy (Gemini) e Codex.
globs: ["skills/**", "commands/**", "AGENTS.md", "CLAUDE.md", "GEMINI.md", ".claude-plugin/**", ".gemini/**"]
regras: [VOZ-08, DUP-10]
---

# Guia Prático — Um Plugin, Vários Agentes

Procedimentos para `VOZ-08` e `DUP-10` (`GOV-04`).

- **Fonte única:** `skills/voice-studio/SKILL.md` (e `references/`). Nenhum agente tem cópia do corpo.
- **Claude Code:** plugin via `.claude-plugin/` e `commands/`.
- **agy (Antigravity/Gemini):** `GEMINI.md` aponta para a skill e para as regras; mesma CLI.
- **Codex:** `AGENTS.md` aponta para a skill; mesma CLI.
- Adaptador novo = arquivo fino que referencia a skill, nunca duplica instruções.
- A CLI (`voice-studio ...`) é o contrato comum e mantém os mesmos argumentos em todos os agentes (`ARQ-06`).

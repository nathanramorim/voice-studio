# Status — 01 Voz multilíngue, perfis e sotaque

**Status:** spec aprovada, fatiada em 8 tasks (3 ondas) e **enfileiradas** (`forge queue list`: 8 `queued`, spec `reviewed`).

**Próximo passo:** `/implementar` (sem `.forge/config/forge.json`, não há despacho ao Builder); começar pela onda 1 (feat-01-01 e 01-02).

**A confirmar:**
- Pasta dos perfis: `~/.voice-studio/perfis/<nome>/` (ADR-0002, na feat-01-01).
- Idiomas além de en e pt saem `validated: false` até haver teste manual.
- ID `01` mantido (a branch já existia); `forge next-id` sugeriria `02`.
- C1 a C3 da feat-01-08 são do usuário (ouvir é a prova).

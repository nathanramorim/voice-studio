# Plano — 01 Voz multilíngue, perfis e sotaque

| Onda | Task | Depende de | Paralelo | Rules/IDs |
|---|---|---|---|---|
| 1 | feat-01-01 módulo `profile`: criar, listar, carregar e validar perfil de voz (nome seguro, amostra copiada, consentimento registrado, pasta fora do repositório) + ADR-0002 | — | sim | SEG-01, SEG-02, VOZ-01, VOZ-04, ARQ-10, DUP-01, TST-01 |
| 1 | feat-01-02 catálogo único de idiomas (`languages`: códigos, estado `validated`, caracteres por segundo) e guarda para os 6 idiomas | — | sim | VOZ-06, VOZ-07, DUP-01, DUP-04, TST-01 |
| 2 | feat-01-03 vocabulário de pronúncia por idioma dentro do perfil | 01, 02 | não | VOZ-05, DUP-01, DUP-03, TST-01 |
| 2 | feat-01-04 `falar`: texto digitado + perfil (ou amostra avulsa) com relatório (`ok`, `validated`) | 01, 02, 03 | não | VOZ-01, VOZ-06, VOZ-09, ARQ-06, ARQ-10, TST-01 |
| 2 | feat-01-05 entrada áudio ou vídeo e saída correspondente (`mix_dub` com ramo só áudio) | 02 | sim | SEG-03, DUP-03, TST-01 |
| 3 | feat-01-06 `traduzir ... --para <idioma> --perfil`: transcrever, receber segmentos traduzidos pelo agente, dublar com a voz do perfil | 04, 05 | não | VOZ-01, VOZ-03, ARQ-06, ARQ-10, TST-01 |
| 3 | feat-01-07 skill, comandos e adaptadores nos 3 agentes (Claude Code, agy, Codex), README atualizado e checklist de validação multiagente | 04, 06 | não | VOZ-08, DUP-10, ARQ-06 |
| 3 | feat-01-08 QA manual: C1 (perfil mineiro), C2 (en e es) e C3 (agy e Codex) com registro no `status.md` | 06, 07 | não | VOZ-07, TST-01 |

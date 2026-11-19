# Decisões — voice-studio

## Resolvidas

| # | Decisão | Resolução | Motivo |
|---|---------|-----------|--------|
| D1 | Motor de voz padrão | XTTS-v2 atrás de `synth.Synth` (ADR-0001) | Único comprovado na máquina do autor; clona, multilíngue, CPU |
| D2 | Onde roda | Local; LLM só vê texto (ADR-0001) | Privacidade da voz (`VOZ-03`) |
| D3 | Licença | Código MIT; modelo CPML com aceite explícito (ADR-0001) | CPML é não comercial |
| D4 | Sotaque | Vem da amostra e do vocabulário (ADR-0001) | XTTS não tem pt-BR/mineiro nativo |
| D5 | Agentes | Um corpo de skill, adaptadores finos (ADR-0001) | `DUP-10` |
| D8 | Perfis de voz | Fora do repositório, `~/.voice-studio/perfis/<nome>/` (ADR-0002) | Amostra é dado pessoal (`VOZ-04`) |
| D9 | Python | Sempre `uv`, nunca pip (ADR-0003) | Ambiente reprodutível |
| D10 | Processo | Forge SDD 4.9.1-beta, fluxo obrigatório, skill replicável (ADR-0004) | Skill é produto de TI |

## Abertas

| # | Questão |
|---|---------|
| D6 | [ ] Motor alternativo de licença permissiva (ex.: Chatterbox) para uso comercial |
| D7 | [ ] Como medir objetivamente "soa mineiro" além de ouvir |

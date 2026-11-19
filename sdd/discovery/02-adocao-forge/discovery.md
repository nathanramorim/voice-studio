# Discovery 02 — adoção do padrão Forge SDD das skills

**Branch:** `chore/forge-sdd` (a partir de `main`). **Modelo:** `enxuto` (só estrutura e documentação; nenhum código do motor muda).

## Problema
O voice-studio tinha o Forge SDD 4.8.0 com as regras genéricas do template. O padrão das skills pede: repositório próprio e replicável, estrutura Forge, `/constitution` alinhada, toda feature ou fix pelo fluxo Forge, Python só via `uv` e README pelo readme-studio com `## Requisitos`.

## O que muda
- Estrutura atualizada para o Forge 4.9.1-beta (`forge update --upgrade`), com o conteúdo do projeto preservado em `CLAUDE.md`, `GEMINI.md` e `.gemini/system_instructions.md`.
- Constituição: regras 1, 2, 3, 7, 12, 13, 14 e 15 (ADR-0004); decisões com ADR-0002 a ADR-0004; divergências conhecidas registradas.
- `sdd/spec/` em dia com o código (`profile`, `languages`, `falar`, `traduzir`).
- ADR-0003 (uv, retroativa) e ADR-0004 (adoção e regras).
- `.gitignore`: telemetria de sessão, runtime do Forge e `.DS_Store` fora do git.

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Estrutura Forge | `sdd/`, `.agents/`, `.claude/` | Forge 4.8.0 | estender | Atualizar, não reinstalar |
| Regras de voz | Constituição, `VOZ-01..09` | completas | reusar | A Regra 15 só remete a elas |

## Dependências novas
Nenhuma.

## Exceção temporária (`GOV-02`)
```constitution-exception
regra: Regra 11 (FLX-07) — versões -beta não entram na main
motivo: a estrutura instalada é do Forge 4.9.1-beta, versão em uso por todos os repositórios de skill; não há estável equivalente
prazo: 2026-12-31
responsavel: dono do repositório (nathanramorim)
```

## Critérios de Aceitação Executáveis
1. `cat sdd/.sdd-version` = `4.9.1-beta`.
2. `forge brief --check` reporta `pronta`.
3. `forge gate` sem falha bloqueante (falsos positivos documentados no `status.md`).
4. `cd engine && uv run ruff check && uv run pytest` passam.

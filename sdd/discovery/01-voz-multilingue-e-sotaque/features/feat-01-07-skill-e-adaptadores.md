# feat-01-07-skill-e-adaptadores — Skill, comandos e adaptadores nos três agentes

## Modelo do módulo
enxuto — documentação operacional e adaptadores finos; sem lógica nova.

## Decisões do projeto aplicadas
ADR-0001 (um só corpo de skill), ADR-0002. Rules: `voz-multiagente`, `sdd-reuso-e-duplicacao` (`DUP-10`).

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Corpo da skill | `skills/voice-studio/SKILL.md` | cobre `sample`, `speak`, `transcribe`, `dub` | estender | Passa a cobrir `perfil`, `falar` e `traduzir` |
| Comandos do plugin | `commands/clonar-voz.md`, `commands/dublar.md` | usam `speak` e `dub` | estender | Viram `/perfil-de-voz`, `/falar` e `/traduzir`; os antigos apontam para os novos |
| Adaptadores | `AGENTS.md`, `GEMINI.md`, `CLAUDE.md` | apontam para a skill | reusar | Sem copiar instruções; só atualizar a lista de comandos |
| README | `README.md` (seção Planejado) | descreve o que falta | estender | Move o que foi entregue para "Uso" e atualiza "Status e limites" |

## Dependências novas
Nenhuma (`ARQ-04`).

## Rules e IDs da Constituição Aplicáveis
VOZ-08, DUP-10, ARQ-06

## Escopo
- `SKILL.md`: fluxos de perfil (amostra mineira, vocabulário), `falar`, `traduzir` em duas fases (o agente traduz), idiomas e `validated`, aviso de sotaque (`VOZ-07`), consentimento e licença.
- Comandos `/perfil-de-voz`, `/falar` e `/traduzir`; `clonar-voz` e `dublar` ficam como atalhos documentados.
- `docs/validacao-multiagente.md`: checklist curto para Claude Code, agy e Codex (abrir o repositório, ler a skill, rodar `voice-studio --help`, criar perfil, falar uma frase) com campo para registrar o que funcionou.
- `README.md` atualizado sem afirmar o que não foi validado (C3 na feat-01-08).

## Critérios de Aceitação Executáveis
- `cd engine && uv run pytest tests/test_docs.py -k comandos`: todo comando da CLI (`perfil`, `falar`, `traduzir`, `sample`, `speak`, `transcribe`, `dub`) é citado em `SKILL.md`.
- `uv run pytest tests/test_docs.py -k adaptadores`: `AGENTS.md`, `GEMINI.md` e `CLAUDE.md` citam `skills/voice-studio/SKILL.md` e não contêm cópia do corpo da skill (nenhum trecho com mais de 5 linhas idênticas ao `SKILL.md`).
- `uv run pytest tests/test_docs.py -k plugin`: `.claude-plugin/plugin.json` e `marketplace.json` são JSON válido e cada arquivo em `commands/` tem `description`.
- `uv run pytest && uv run ruff check` passam.

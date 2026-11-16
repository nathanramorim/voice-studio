# feat-01-08-qa-manual — QA manual: perfil mineiro, inglês e agentes

## Modelo do módulo
enxuto — fecha a iniciativa com verificação humana; só adiciona um teste de fumaça da CLI.

## Decisões do projeto aplicadas
ADR-0001 (sotaque vem da amostra; aprovação ouvindo), `VOZ-07`. Rules: `voz-pronuncia-e-qualidade`, `voz-multiagente`.

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Teste de fumaça da CLI | `engine/tests` | só testes de domínio | criar | Um teste que roda `--help` e confere os comandos |
| Checklist multiagente | feat-01-07 (`docs/validacao-multiagente.md`) | checklist | reusar | C3 preenche o checklist |
| Registro de QA | `status.md` da iniciativa | estado e próximos passos | reusar | Resultado dos C1 a C3 vai ali |

## Dependências novas
Nenhuma (`ARQ-04`).

## Rules e IDs da Constituição Aplicáveis
VOZ-07, TST-01

## Escopo
- `engine/tests/test_cli_smoke.py`: `voice-studio --help` lista `perfil`, `falar`, `traduzir`, `sample`, `speak`, `transcribe` e `dub`.
- C1 (perfil mineiro): gravar 20 a 30 s, `perfil criar mineiro ... --confirm-own-voice`, `perfil vocab mineiro --lang pt exemplos/pronuncia-pt.json`, gerar 5 frases com 3 versões cada, ouvir e anotar grafias ajustadas.
- C2 (idiomas): `traduzir` de um clipe de 20 s pt -> en (ouvir e medir o tempo total) e um teste em es só para ver `validated: false`.
- C3 (agentes): seguir o checklist em agy e Codex e registrar o que funcionou e o que não.
- Quem executa os C1 a C3 é o usuário (ouvir é a prova, `VOZ-07`); o agente só prepara os comandos e registra o resultado.

## Critérios de Aceitação Executáveis
- `cd engine && uv run pytest tests/test_cli_smoke.py`: a CLI lista os sete comandos.
- `uv run pytest && uv run ruff check` passam.
- Manual: C1, C2 e C3 registrados no `status.md` com data e resultado; o README só afirma suporte a agy e Codex depois do C3.

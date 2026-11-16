# feat-01-02-catalogo-de-idiomas — Catálogo único de idiomas e guarda por idioma

## Modelo do módulo
enxuto — um módulo de dados com uma função de consulta; a regra já existe e só muda de casa.

## Decisões do projeto aplicadas
ADR-0001. Rules: `voz-pronuncia-e-qualidade`, `sdd-reuso-e-duplicacao` (`DUP-04`: constantes com definição única).

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Lista de idiomas | `synth.LANGS` | conjunto fixo de 6 códigos | estender | Passa para o catálogo e `synth` consulta o catálogo |
| Caracteres por segundo | `guard.CPS` | só pt e en medidos | estender | Mesmo dado, agora no catálogo, com es, fr, de e it estimados |
| Duração esperada e suspeita | `guard.expected_seconds`, `is_suspect` | funcionam por idioma | reusar | A API pública de `guard` não muda |
| Catálogo de idiomas | — | nada | criar | Dono único de códigos, estado e caracteres por segundo (`DUP-01`) |

## Dependências novas
Nenhuma (`ARQ-04`).

## Rules e IDs da Constituição Aplicáveis
VOZ-06, VOZ-07, DUP-01, DUP-04, TST-01

## Escopo
- `languages.py`: `Lang(code, nome, cps, validated)`; catálogo com pt (15,0; validado), en (12,5; validado), es, fr, de, it (valores estimados, `validated: false`).
- `require(code) -> Lang` (erro claro e lista dos idiomas aceitos) e `is_validated(code)`.
- `guard.expected_seconds` e `synth.speak` passam a consultar o catálogo; `synth.LANGS` e `guard.CPS` deixam de existir (sem duplicação, `COD-04`).
- Comentário no catálogo: os valores de es, fr, de e it não foram medidos; recalibrar com falas reais quando houver teste manual.

## Critérios de Aceitação Executáveis
- `cd engine && uv run pytest tests/test_languages.py -k catalogo`: os 6 idiomas existem; `pt` e `en` têm `validated: true`; es, fr, de e it têm `false`.
- `uv run pytest tests/test_languages.py -k require`: idioma fora do catálogo falha com mensagem que lista os aceitos.
- `uv run pytest tests/test_guard.py`: continua passando sem alterar as asserções existentes (mesma API).
- `uv run pytest tests/test_speak.py -k entradas`: `speak` com idioma inválido segue falhando pelo catálogo.
- `uv run pytest && uv run ruff check` passam.

# feat-01-04-falar — `falar`: texto digitado com a voz de um perfil

## Modelo do módulo
completo — comando novo de uso principal, com contrato público e relatório.

## Decisões do projeto aplicadas
ADR-0001, ADR-0002. Rules: `voz-consentimento-e-privacidade`, `voz-pronuncia-e-qualidade`, `sdd-reuso-e-duplicacao`.

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Geração com variações e guarda | `synth.speak` | N variações, guarda, corte de pontas | reusar | `falar` é uma casca sobre ele |
| Comando de baixo nível | `cli.speak` (lista JSON + `--ref`) | funciona | reusar | Continua existindo; `falar` é o caminho amigável |
| Consentimento e licença | `consent.py` | funções prontas | reusar | O perfil já traz o consentimento; a licença CPML segue explícita |
| Perfil e vocabulário por idioma | feat-01-01 e 01-03 | `load`, `vocabulary` | reusar | Fornecem amostra, ajustes e mapa |
| Catálogo de idiomas | feat-01-02 | `require`, `is_validated` | reusar | Valida `--lang` e preenche `validated` |

## Dependências novas
Nenhuma (`ARQ-04`).

## Rules e IDs da Constituição Aplicáveis
VOZ-01, VOZ-06, VOZ-09, ARQ-06, ARQ-10, TST-01

## Escopo
- `falar.py` (domínio): `run(textos, perfil, lang, out, synth, takes)` recebe o sintetizador por parâmetro (`VOZ-09`) e devolve o relatório `[{linha, arquivo, segundos, ok, validated, falado}]`.
- CLI: `voice-studio falar "texto" [--arquivo falas.json] --perfil NOME --lang pt --accept-cpml [--out DIR] [--takes N]`. Alternativa sem perfil: `--ref AUDIO --confirm-own-voice` (amostra avulsa).
- O texto digitado nunca é gravado em log além do relatório do usuário; o relatório mostra o texto falado (com a grafia do vocabulário) para o usuário ouvir e ajustar.
- Linha com `ok: false` (todas as variações suspeitas) é sinalizada no resumo e no código de saída informativo, nunca silenciada (`VOZ-06`).
- Idioma não validado (`validated: false`) imprime aviso de que a qualidade não foi verificada.

## Critérios de Aceitação Executáveis
- `cd engine && uv run pytest tests/test_falar.py -k texto`: com sintetizador simulado, o texto digitado chega ao motor com o vocabulário do idioma aplicado e a amostra do perfil; o relatório traz `ok`, `validated` e `falado`.
- `uv run pytest tests/test_falar.py -k consentimento`: sem perfil nem `--ref`, falha; `--ref` sem `--confirm-own-voice` falha; sem `--accept-cpml` falha antes de tocar no motor.
- `uv run pytest tests/test_falar.py -k nao-validado`: `--lang es` gera o aviso e `validated: false`.
- `uv run pytest tests/test_falar.py -k suspeita`: todas as variações suspeitas resultam em `ok: false` e aviso.
- `uv run pytest && uv run ruff check` passam.

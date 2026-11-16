# feat-01-03-vocabulario-por-idioma — Vocabulário de pronúncia por idioma no perfil

## Modelo do módulo
enxuto — estende a carga do vocabulário e o perfil; a troca de termos não muda.

## Decisões do projeto aplicadas
ADR-0001, ADR-0002. Rules: `voz-pronuncia-e-qualidade`, `sdd-reuso-e-duplicacao`.

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Carga e validação do mapa | `vocab.load`, `vocab.clean` | valida tamanho, tipos e chaves | reusar | Os vocabulários do perfil passam pela mesma validação |
| Troca por palavra inteira | `vocab.apply_spoken` | siglas só em maiúsculas | reusar | Sem mudança |
| Perfil com campo `vocabularios` | feat-01-01 (`profile`) | mapa idioma -> arquivo | estender | Esta task preenche e lê o campo |

## Dependências novas
Nenhuma (`ARQ-04`).

## Rules e IDs da Constituição Aplicáveis
VOZ-05, DUP-01, DUP-03, TST-01

## Escopo
- `profile.set_vocabulary(nome, lang, arquivo, base)`: valida com `vocab.load`, confere o idioma no catálogo (feat-01-02) e copia para `<base>/<nome>/vocab.<lang>.json`, registrando em `perfil.json`.
- `profile.vocabulary(perfil, lang) -> dict`: devolve o mapa do idioma (vazio se não houver); nunca mistura mapas de idiomas diferentes.
- CLI: `voice-studio perfil vocab NOME --lang pt ARQUIVO.json`.
- O mapa pt de `exemplos/pronuncia-pt.json` serve de ponto de partida do perfil `mineiro` (documentado, não embutido).

## Critérios de Aceitação Executáveis
- `cd engine && uv run pytest tests/test_vocab.py -k idioma`: perfil com mapas `pt` e `en` aplica o do idioma da fala e ignora o outro.
- `uv run pytest tests/test_profile.py -k vocabulario`: arquivo inválido (vazio, grande demais, valor não texto) falha sem alterar o perfil; idioma fora do catálogo falha; sem mapa para o idioma devolve `{}`.
- `uv run pytest && uv run ruff check` passam.

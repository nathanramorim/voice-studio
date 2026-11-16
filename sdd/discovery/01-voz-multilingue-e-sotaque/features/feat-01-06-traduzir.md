# feat-01-06-traduzir — `traduzir`: áudio ou vídeo para outro idioma, com a voz do perfil

## Modelo do módulo
completo — comando de orquestração em duas fases (o agente traduz entre elas), com contrato público.

## Decisões do projeto aplicadas
ADR-0001 (o LLM só vê texto), ADR-0002. Rules: `voz-consentimento-e-privacidade`, `voz-pronuncia-e-qualidade`, `sdd-reuso-e-duplicacao`.

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Transcrição local | `transcribe.transcribe` | segmentos `{start, end, source}` | reusar | Fase 1 do comando |
| Dublagem por segmento | `dub.dub`, `load_segments` | valida, encaixa, mixa, relatório | reusar | Fase 2 do comando |
| Entrada áudio ou vídeo | feat-01-05 | `has_video`, mix com ramo de áudio | reusar | O comando aceita os dois |
| Perfil, vocabulário e idiomas | feat-01-01, 02 e 03 | `load`, `vocabulary`, `require` | reusar | Voz, pronúncia e validação do `--para` |
| Comando de baixo nível | `cli.transcribe`, `cli.dub` | existem | reusar | `traduzir` os encadeia com perfil e idioma |

## Dependências novas
Nenhuma (`ARQ-04`).

## Rules e IDs da Constituição Aplicáveis
VOZ-01, VOZ-03, ARQ-06, ARQ-10, TST-01

## Escopo
- `traduzir.py` (domínio): `prepare(entrada, perfil, de, para, model)` transcreve e grava `segments.json` com `source` e `text` vazio; `render(entrada, segmentos, perfil, para, out, synth, takes)` valida que todo `text` está preenchido e dubla.
- CLI: `voice-studio traduzir ENTRADA --para en --perfil NOME [--de pt] [--model ggml.bin]` (fase 1, imprime "traduza `source` para `text` e rode de novo com `--segmentos`") e `... --segmentos seg.json --accept-cpml [--out SAIDA]` (fase 2).
- Perfil sem consentimento, idioma fora do catálogo ou segmentos sem tradução falham antes de tocar no motor.
- Idioma não validado imprime aviso e `validated: false` no relatório; `overflow` e `suspect_takes` continuam no relatório.
- Só texto passa pelo agente: o áudio nunca é anexado ao diálogo (`VOZ-03`).

## Critérios de Aceitação Executáveis
- `cd engine && uv run pytest tests/test_traduzir.py -k fases`: a fase 1 grava segmentos com `text` vazio (transcrição simulada); a fase 2 com segmentos preenchidos gera o áudio dublado com sintetizador simulado.
- `uv run pytest tests/test_traduzir.py -k perfil`: sem perfil ou perfil sem consentimento, falha antes do motor.
- `uv run pytest tests/test_traduzir.py -k traducao-faltando`: segmento com `text` vazio falha apontando o número do segmento.
- `uv run pytest tests/test_traduzir.py -k idioma`: `--para` fora do catálogo falha; `--para es` traz `validated: false` e aviso.
- `uv run pytest && uv run ruff check` passam.

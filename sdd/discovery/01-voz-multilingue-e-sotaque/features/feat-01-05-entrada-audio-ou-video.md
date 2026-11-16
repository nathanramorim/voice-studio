# feat-01-05-entrada-audio-ou-video — Dublagem com entrada e saída de áudio ou vídeo

## Modelo do módulo
enxuto — um ramo novo na mixagem e uma checagem do tipo de mídia; a dublagem por segmento não muda.

## Decisões do projeto aplicadas
ADR-0001. Rules: `sdd-seguranca` (`SEG-03`: processos sem shell), `sdd-reuso-e-duplicacao`.

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Mixagem da dublagem | `audio.mix_dub` | exige vídeo (`-map 0:v`, copia o vídeo) | estender | Acrescenta o ramo só de áudio |
| Chamada de processos | `audio.run` | lista de argumentos, sem shell | reusar | Mesmo ponto de chamada (`SEG-03`) |
| Dublagem por segmento | `dub.dub` | encaixe `atempo`, relatório, `overflow` | reusar | Só passa a aceitar mídia de áudio |
| Detecção de vídeo | — | nada | criar | `audio.has_video(path)` com `ffprobe` |

## Dependências novas
Nenhuma (`ARQ-04`): `ffprobe` já acompanha o ffmpeg.

## Rules e IDs da Constituição Aplicáveis
SEG-03, DUP-03, TST-01

## Escopo
- `audio.has_video(path) -> bool` (ffprobe, lista de argumentos).
- `audio.mix_dub`: se a entrada não tem vídeo, a saída é só áudio (`.m4a` ou `.wav` pela extensão de `--out`); se tem vídeo, mantém o comportamento atual.
- `dub.dub` e a CLI `dub` aceitam entrada de áudio; a extensão da saída incompatível com o tipo de entrada (`.mp4` para áudio) é erro claro.
- O relatório é o mesmo nos dois casos.

## Critérios de Aceitação Executáveis
- `cd engine && uv run pytest tests/test_traduzir.py -k audio`: entrada `.wav` (seno gerado pelo teste) com sintetizador simulado produz saída de áudio; usa ffmpeg real e é ignorado se ele não existir.
- `uv run pytest tests/test_traduzir.py -k video`: entrada com faixa de vídeo mantém a saída em vídeo.
- `uv run pytest tests/test_traduzir.py -k extensao`: saída `.mp4` para entrada só áudio falha com mensagem clara.
- `uv run pytest && uv run ruff check` passam.

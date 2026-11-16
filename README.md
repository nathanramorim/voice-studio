# voice-studio

**Sua voz clonada, local e de graça.** Gera narração em português ou inglês com a sua voz, dubla vídeos de português para inglês e corrige a pronúncia de siglas e marcas. Plugin para Claude Code (e qualquer agente que leia skills) com um motor Python por trás.

- 🔒 **Local:** o áudio nunca sai da sua máquina (XTTS-v2 + whisper.cpp).
- 🗣️ **Pronúncia sob controle:** `pronuncia.json` troca a grafia da tela pela grafia falada ("IA" -> "IÁ", "PR" -> "PIER", "Forge SDD" -> "Forge S D D").
- 🛡️ **Guarda contra falas defeituosas:** o modelo às vezes alucina (3 s viram 10 s). O motor gera várias variações e descarta as de duração absurda.
- 🌎 **Dublagem pt -> en:** transcreve, o agente traduz, a sua voz fala em inglês, encaixada no tempo do vídeo.

> É **fala gerada a partir de texto**, não conversão da voz existente. O timbre vem da sua amostra; sotaque e naturalidade do inglês variam. Ouça sempre o resultado.

## Licenças (leia antes de usar)

| Parte | Licença |
|---|---|
| Código deste repositório | MIT |
| Modelo **XTTS-v2** (usado por padrão) | **Coqui CPML: somente uso não comercial** |

Os pesos do modelo **não** são distribuídos aqui; o motor baixa o modelo na primeira geração. Você aceita a CPML explicitamente com `--accept-cpml` (ou `VOICE_STUDIO_ACCEPT_CPML=1`). Para uso comercial, troque o motor por um de licença permissiva (ex.: Chatterbox, MIT); o sintetizador é uma interface (`synth.Synth`) justamente para isso.

## Consentimento e privacidade

- Só clone a **sua** voz ou a de quem autorizou. A CLI exige `--confirm-own-voice`.
- Amostras e áudios gerados nunca são versionados (`.gitignore` bloqueia `wav`, `mp3`, `m4a`, `mp4`). Não publique voz de ninguém sem permissão.

## Instalação

Pré-requisitos: [`uv`](https://docs.astral.sh/uv/), `ffmpeg` e, para transcrever, `whisper-cpp` (`brew install ffmpeg whisper-cpp`) com um modelo ggml (ex.: `ggml-small.bin`).

```bash
# como plugin do Claude Code
/plugin marketplace add nathanramorim/voice-studio
/plugin install voice-studio@voice-studio

# ou direto pela CLI
git clone https://github.com/nathanramorim/voice-studio && cd voice-studio/engine
uv run --python 3.11 --extra xtts voice-studio --help
```

No **Mac com Apple Silicon**, use `--python cpython-3.11-macos-aarch64-none` (sem isso o `uv` pode escolher x86_64 sob Rosetta e o PyTorch não instala). A primeira geração baixa o modelo (~2 GB). Roda em CPU: cerca de 20 a 60 s por fala.

## Uso

```bash
# 1. amostra de referência (6 a 30 s de fala limpa) a partir de uma gravação
voice-studio sample minha-gravacao.mov -o voice-ref.wav

# 2. narração: uma fala por linha, com vocabulário de pronúncia
voice-studio speak exemplos/falas.json --ref voice-ref.wav --lang pt \
  --vocab exemplos/pronuncia-pt.json --takes 3 --confirm-own-voice --accept-cpml -o out

# 3. dublagem pt -> en
voice-studio transcribe video.mp4 -o segments.json --model ggml-small.bin
#    (traduza `source` para `text`; no Claude Code, a skill faz isso para você)
voice-studio dub video.mp4 segments.json --ref voice-ref.wav --lang en \
  --vocab exemplos/pronuncia-en.json --confirm-own-voice --accept-cpml -o dublado.mp4
```

No Claude Code: `/clonar-voz` e `/dublar` seguem a skill e pedem o consentimento e o aceite da licença.

## Pronúncia

`pronuncia.json` é um mapa `{"como aparece": "como falar"}`:

- Troca por palavra inteira, só no texto enviado à voz; a legenda mantém a grafia original.
- Siglas em maiúsculas só casam em maiúsculas (`"IA"` não troca o verbo `ia`).
- `exemplos/pronuncia-pt.json` registra o sotaque mineiro do autor; use como ponto de partida e ajuste ao seu.
- O Whisper reescreve marcas para a grafia padrão, então a transcrição **não confirma** a pronúncia: ouça e ajuste.

## Status

v0.1.0. Testado em macOS (Apple Silicon): `speak` em inglês com vocabulário e guarda de duração, mais 17 testes unitários. A dublagem completa (`transcribe` + `dub`) ainda não foi exercitada de ponta a ponta com um vídeo real; o encaixe e a mixagem têm testes só com sintetizador simulado. Marcas difíceis (ex.: "Forge SDD") pedem iterar a grafia falada até soar certo.

## Como funciona

```
amostra ──► XTTS-v2 (local) ◄── texto (com pronuncia.json)
              │  N variações por fala
              ▼
   guarda de duração (caracteres/s) ──► melhor variação ──► corte de silêncio nas pontas
              │
   dub: encaixe no tempo (atempo até 1,25x) ──► mix no vídeo (ffmpeg)
```

Código em `engine/src/voice_studio/`: `vocab`, `guard`, `synth` (motor injetável), `dub`, `audio`, `transcribe`, `consent`. Os testes usam um sintetizador simulado e nunca baixam o modelo.

## Desenvolvimento

```bash
cd engine
uv run --python 3.11 --group dev pytest -q
uv run --python 3.11 --group dev ruff check .
```

## Limites

- Sotaque regional da amostra não é garantido: gere 3 a 4 variações e escolha ouvindo.
- O inglês dublado tem a sua voz, mas a prosódia é a do modelo.
- Dublagem é por segmento: textos traduzidos longos demais estouram o tempo (o relatório avisa em `overflow`).

## Licença

MIT para o código. O modelo XTTS-v2 segue a [Coqui CPML](https://coqui.ai/cpml).

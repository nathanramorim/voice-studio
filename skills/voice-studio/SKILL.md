---
name: voice-studio
description: Use para clonar a voz do usuário (local e gratuito), gerar narração em português ou inglês com ela, ou dublar um vídeo de português para inglês. Ative quando pedirem "clonar minha voz", "narrar com a minha voz", "voz virtual", "dublar", "traduzir o vídeo para inglês", "versão em inglês do reel", ou quando uma palavra sair com a pronúncia errada na voz gerada.
---

# voice-studio

Clona a voz do usuário com o XTTS-v2, 100% local (nada de áudio vai para a nuvem). O código é MIT; **o modelo XTTS-v2 é Coqui CPML, uso não comercial**. O LLM (você) só escreve e traduz texto: nunca ouve áudio.

`RAIZ` é a pasta do plugin (`${CLAUDE_PLUGIN_ROOT}` no Claude Code). Rode sempre em `RAIZ/engine`:

```bash
uv run --python 3.11 --extra xtts voice-studio <comando>
```

No Mac com Apple Silicon use `--python cpython-3.11-macos-aarch64-none` (sem isso o `uv` pode escolher x86_64 sob Rosetta e as dependências não instalam).

## Antes de qualquer geração (obrigatório)

1. **Consentimento da voz.** Só clone a voz do próprio usuário ou de alguém com autorização. Pergunte uma vez; depois passe `--confirm-own-voice`. Nunca passe a flag por conta própria.
2. **Licença do modelo.** Explique que o XTTS-v2 é CPML (não comercial) e peça o aceite. Só então use `--accept-cpml`. Para uso comercial, sugira outro motor (ex.: Chatterbox, MIT).
3. **Privacidade.** Amostra e áudios gerados ficam na pasta de trabalho do usuário. Nunca versionar nem publicar (o `.gitignore` já bloqueia `wav`, `mp3`, `m4a`, `mp4`).

## Fluxos

### Amostra de voz
```bash
voice-studio sample gravacao.mov -o voice-ref.wav --start 0 --duration 28
```
Escolha um trecho de fala contínua, sem música e sem outra voz (6 a 30 s). **Peça ao usuário para ouvir** antes de usar.

### Narração
`falas.json` é uma lista de textos. Um arquivo `pronuncia.json` (opcional) troca a grafia da tela pela grafia falada.
```bash
voice-studio speak falas.json --ref voice-ref.wav --lang pt --takes 3 \
  --vocab pronuncia.json --confirm-own-voice --accept-cpml -o out
```
Gera `out/line-NN.wav` e `out/report.json`. O motor gera N variações por fala e fica com a mais próxima da duração esperada; falas de duração absurda (o modelo às vezes alucina, 3 s viram 10 s) são descartadas. Se `ok` for `false` na linha, todas as variações saíram suspeitas: gere de novo ou mude o texto.

### Dublagem português -> inglês
1. `voice-studio transcribe video.mp4 -o segments.json --model ggml-small.bin` (precisa de `whisper-cli`: `brew install whisper-cpp`, e um modelo ggml).
2. **Você traduz**: para cada segmento, escreva o inglês no campo `text` (mantenha `start` e `end`). Frases curtas e naturais; o inglês costuma ser mais curto que o português, mas cuide dos segmentos longos. Não use markdown.
3. `voice-studio dub video.mp4 segments.json --ref voice-ref.wav --lang en --vocab pronuncia-en.json --confirm-own-voice --accept-cpml -o dublado.mp4`
4. Leia o relatório: `overflow` lista segmentos que não couberam (acelera no máximo 1,25x); encurte o texto traduzido e rode de novo. `--keep-original 0.1` mantém o áudio original baixinho.

É **fala gerada a partir de texto**, não conversão da voz existente: o timbre vem da amostra; o sotaque e a naturalidade do inglês variam.

## Pronúncia

Marcas e siglas saem erradas ("Forge SDD" vira "for August"). Resolva com o `pronuncia.json`: `{"IA": "IÁ", "PR": "PIER", "Forge SDD": "Forge S D D"}`. Siglas em maiúsculas só casam em maiúsculas ("ia" verbo fica intacto). A legenda mantém a grafia original: só o texto enviado à voz muda. Exemplos em `exemplos/`.

**Verificação:** o Whisper reescreve marcas para a grafia padrão ("Geminai" volta como "Gemini"), então a transcrição **não prova** a pronúncia. Peça ao usuário para ouvir as falas com termos do vocabulário e ajuste a grafia falada com ele.

## Limites honestos

- CPU: cerca de 20 a 60 s por fala; a primeira execução baixa o modelo (~2 GB).
- O sotaque regional da amostra não é garantido. Gere 3 a 4 variações e escolha ouvindo.
- Idiomas do XTTS usados aqui: pt, en, es, fr, de, it.

---
name: voice-studio
description: Use para clonar a voz do usuário (local e gratuito), criar um perfil de voz, falar um texto digitado em vários idiomas com ela, ou traduzir e dublar áudio ou vídeo. Ative quando pedirem "clonar minha voz", "narrar com a minha voz", "voz virtual", "perfil de voz", "falar este texto", "dublar", "traduzir o áudio", "traduzir o vídeo para inglês", "versão em inglês do reel", ou quando uma palavra sair com a pronúncia errada na voz gerada.
---

# voice-studio

Clona a voz do usuário com o XTTS-v2, 100% local (nada de áudio vai para a nuvem). O código é MIT; **o modelo XTTS-v2 é Coqui CPML, uso não comercial**. O LLM (você) só escreve e traduz texto: nunca ouve áudio.

`RAIZ` é a pasta do plugin (`${CLAUDE_PLUGIN_ROOT}` no Claude Code). Rode sempre em `RAIZ/engine`:

```bash
uv run --python 3.11 --extra xtts voice-studio <comando>
```

No Mac com Apple Silicon use `--python cpython-3.11-macos-aarch64-none` (sem isso o `uv` pode escolher x86_64 sob Rosetta e as dependências não instalam).

## Antes de qualquer geração (obrigatório)

0. **Requisitos.** Rode `sh RAIZ/scripts/bootstrap.sh --arquivo RAIZ/requisitos.toml checar` (macOS e Linux) ou `powershell -ExecutionPolicy Bypass -File RAIZ/scripts/bootstrap.ps1 --arquivo RAIZ/requisitos.toml checar` (Windows): ele confere o uv (e só o instala com o ok do usuário) e roda `checar` sobre a receita do voice-studio. Passe sempre `--arquivo RAIZ/requisitos.toml`: sem ele, o motor usa o `requisitos.toml` da pasta atual (que pode ser de outro projeto). Se faltar algo, mostre a lista e peça o ok item por item; para cada aprovado, rode `uv run RAIZ/scripts/requisitos.py --arquivo RAIZ/requisitos.toml instalar --sim <item>`. Itens com status `pessoa` (licença CPML, declaração da voz, amostra, aprovação, variável do shell) você só explica; quem faz é o usuário (passos 1 e 2). Itens `nao-suportado` trazem a alternativa (ex.: WSL no Windows arm64).
1. **Consentimento da voz.** Só clone a voz do próprio usuário ou de alguém com autorização. Pergunte ao usuário e só então passe `--confirm-own-voice`. Nunca passe a flag por conta própria.
2. **Licença do modelo.** Explique que o XTTS-v2 é CPML (não comercial) e peça o aceite. Só então use `--accept-cpml`; nunca por conta própria. Para uso comercial, sugira outro motor (ex.: Chatterbox, MIT).
3. **Privacidade.** Amostra e áudios gerados ficam na pasta de trabalho do usuário. Nunca versionar nem publicar (o `.gitignore` já bloqueia `wav`, `mp3`, `m4a`, `mp4`).

## Fluxos

### Perfil de voz (padrão)
O perfil guarda a amostra tratada, o consentimento e o vocabulário por idioma, fora do repositório (`~/.voice-studio/perfis`, ou `VOICE_STUDIO_HOME`).
```bash
voice-studio perfil criar nathan gravacao.mov --confirm-own-voice --start 0 --duration 28
voice-studio perfil vocab nathan pronuncia-pt.json --lang pt
voice-studio perfil listar
voice-studio perfil mostrar nathan
```
**Amostra mineira:** para o português mineiro, a amostra deve ser de fala contínua do próprio usuário falando do jeito dele; o sotaque vem dela e do vocabulário (`exemplos/pronuncia-pt.json` é ponto de partida), nunca de uma promessa do modelo. Peça ao usuário para ouvir `amostra.wav` do perfil antes de usar.

### Falar um texto
```bash
voice-studio falar "Vamos usar a IA hoje" --perfil nathan --lang pt --accept-cpml -o out
voice-studio falar --arquivo falas.json --perfil nathan --lang en --accept-cpml -o out
```
`--ref AUDIO --confirm-own-voice` usa uma amostra avulsa no lugar do perfil. Gera `out/line-NN.wav` e `out/report.json` (com `validated`). Usa o vocabulário do perfil para o idioma da fala.

### Traduzir áudio ou vídeo (duas fases)
1. `voice-studio traduzir entrada.mp4 --para en --perfil nathan [--de pt] --model ggml-small.bin` transcreve (local) e grava `segments.json` com `source` e `text` vazio.
2. **Você traduz**: para cada segmento, escreva a tradução no campo `text` (mantenha `start`, `end` e `source`). Frases curtas e naturais, sem markdown. Só texto passa por você; nunca anexe o áudio.
3. `voice-studio traduzir entrada.mp4 --para en --perfil nathan --segmentos segments.json --accept-cpml [--out dublado.mp4]` dubla com a voz do perfil. Entrada só áudio gera `.m4a` ou `.wav`; vídeo gera `.mp4`.
4. Leia o `report.json`: `overflow` (segmentos que não couberam; encurte o texto e rode de novo) e `suspect_takes` (fala suspeita; confira ou regere). Segmento sem tradução falha apontando o número.

## Idiomas e `validated`
`pt`, `en`, `es`, `fr`, `de` e `it`. Só `pt` e `en` foram medidos com falas reais (`validated: true`). Nos demais o relatório traz `validated: false` e a CLI avisa: diga ao usuário que a qualidade não foi verificada e peça para ouvir com atenção.

## Sobrescrever saídas
`traduzir` e `dub` recusam `--out` igual à entrada e saída já existente. **Pergunte ao usuário antes de passar `--sobrescrever`** e nunca o passe por conta própria: a entrada nunca é sobrescrita, mas a saída anterior seria substituída.

## Códigos de saída
`0` ok; `1` erro de uso ou validação (nada foi gerado); `2` só em `falar` e `traduzir`: gerou, mas há fala(s) suspeita(s) (`ok: false`); confira o `report.json`. `speak` e `dub` (baixo nível) saem `0` mesmo com linha suspeita ou estouro de tempo: leia o `report.json` ou o resumo impresso.

## Sotaque (VOZ-07)
O sotaque vem da amostra e do vocabulário, não do modelo; nunca prometa sotaque. A transcrição não prova a pronúncia (o Whisper normaliza marcas). Peça ao usuário para ouvir.

### Comandos de baixo nível

#### Amostra de voz
```bash
voice-studio sample gravacao.mov -o voice-ref.wav --start 0 --duration 28
```
Escolha um trecho de fala contínua, sem música e sem outra voz (6 a 30 s). **Peça ao usuário para ouvir** antes de usar.

#### Narração
`falas.json` é uma lista de textos. Um arquivo `pronuncia.json` (opcional) troca a grafia da tela pela grafia falada.
```bash
voice-studio speak falas.json --ref voice-ref.wav --lang pt --takes 3 \
  --vocab pronuncia.json --confirm-own-voice --accept-cpml -o out
```
Gera `out/line-NN.wav` e `out/report.json`. O motor gera N variações por fala e fica com a mais próxima da duração esperada; falas de duração absurda (o modelo às vezes alucina, 3 s viram 10 s) são descartadas. Se `ok` for `false` na linha, todas as variações saíram suspeitas: gere de novo ou mude o texto.

#### Dublagem manual (`transcribe` + `dub`)
1. `voice-studio transcribe video.mp4 -o segments.json --model ggml-small.bin` (precisa de `whisper-cli` e de um modelo ggml: `uv run RAIZ/scripts/requisitos.py --arquivo RAIZ/requisitos.toml instalar whisper-cli modelo-whisper` mostra o comando do sistema).
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

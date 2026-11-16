<p align="center">
  <img src="docs/img/banner.svg" alt="voice-studio: Narre um texto ou duble um vídeo" width="100%">
</p>

<p align="center">
  <a href="https://github.com/nathanramorim/voice-studio/releases"><img alt="versão" src="https://img.shields.io/github/v/tag/nathanramorim/voice-studio?label=vers%C3%A3o&color=ff7a59&labelColor=0c0b14"></a>
  <img alt="licença" src="https://img.shields.io/badge/licen%C3%A7a-MIT-8b6cff?labelColor=0c0b14">
  <img alt="local" src="https://img.shields.io/badge/roda-100%25%20local-6ee7b7?labelColor=0c0b14">
  <img alt="modelo" src="https://img.shields.io/badge/modelo-XTTS--v2%20%C2%B7%20n%C3%A3o%20comercial-ffb26b?labelColor=0c0b14">
</p>

<h3 align="center">Narre um texto ou duble um vídeo<br>com a sua voz, no seu computador.</h3>

---

## O que é

O **voice-studio** clona a sua voz **no seu próprio computador**. Você dá uma amostra de áudio (de 6 a 30 segundos falando) e ele:

- **guarda a sua voz num perfil** (amostra, consentimento e vocabulário de pronúncia por idioma);
- **fala o texto que você digitar**, com a sua voz (narração para reels, vídeos e apresentações);
- **traduz um áudio ou vídeo para outro idioma** com a sua voz, encaixando cada fala no tempo da mídia (o inglês é o idioma validado).

Funciona como plugin do **Claude Code**, com instruções prontas também para **agy (Antigravity)** e **Codex**. A tradução do texto é feita pelo agente; o áudio nunca sai da sua máquina.

> É voz gerada a partir de texto, não uma conversão da voz que já existe. O timbre vem da sua amostra; sotaque e naturalidade do idioma variam. **Ouça sempre o resultado antes de publicar.**

## Por que usar

| | |
|---|---|
| 🔒 **Tudo local** | A amostra, as falas e a transcrição ficam no seu computador. |
| 💸 **Grátis** | Usa o modelo XTTS-v2 e ferramentas abertas, sem assinatura de serviço de voz. |
| 🗣️ **Pronúncia sob controle** | Um vocabulário troca "IA" por "IÁ", "PR" por "PIER" e assim por diante, só na fala; a legenda não muda. |
| 🛡️ **Falas conferidas** | Cada fala gera várias versões e descarta as defeituosas (uma fala de 3 s que sai com 10 s, por exemplo). |
| 👤 **Perfis de voz** | Um perfil por voz ou sotaque, com amostra, consentimento e vocabulário por idioma. |
| 🌎 **Tradução de áudio ou vídeo** | Transcreve, o agente traduz e a sua voz fala no idioma escolhido, no tempo da mídia (áudio entra e sai como áudio; vídeo, como vídeo). |

## Antes de começar

| Requisito | Para quê |
|---|---|
| [`uv`](https://docs.astral.sh/uv/) | Instala o Python 3.11 e as dependências do motor (você não precisa instalar o Python). |
| `ffmpeg` (inclui o `ffprobe`) | Corta, acelera e mixa o áudio; detecta se a entrada tem vídeo. `brew install ffmpeg`. |
| `whisper-cpp` e um modelo ggml (ex.: `ggml-small.bin`) | **Só para transcrever** (`traduzir`, `transcribe`). `brew install whisper-cpp`. |
| Extra `xtts` | Traz o motor de voz e o PyTorch. É instalado com `--extra xtts`; o modelo (cerca de 2 GB) é baixado na primeira geração. |
| Um agente com suporte a skills | Claude Code, agy ou Codex. Sem agente, a linha de comando funciona sozinha. |
| Uma **amostra da sua voz** | 6 a 30 s de fala contínua, sem música nem outras vozes. |

Roda em CPU: de 20 a 60 segundos por fala. Os perfis ficam em `~/.voice-studio/perfis/` (mude com `VOICE_STUDIO_HOME` ou `--perfis-dir`), sempre **fora** de qualquer repositório git.

## Instalação

**Como plugin do Claude Code**

```
/plugin marketplace add nathanramorim/voice-studio
/plugin install voice-studio@voice-studio
```

**Direto pela linha de comando**

```bash
git clone https://github.com/nathanramorim/voice-studio
cd voice-studio/engine
uv run --python 3.11 --extra xtts voice-studio --help
```

No **Mac com Apple Silicon**, use `--python cpython-3.11-macos-aarch64-none` (sem isso o `uv` pode escolher x86_64 e o PyTorch não instala).

**agy e Codex:** abra o repositório; as instruções estão em `GEMINI.md` (agy) e `AGENTS.md` (Codex) e apontam para a mesma skill e a mesma linha de comando.

## Como usar

**1. Perfil da sua voz** (a partir de uma gravação sua; guarda a amostra e o consentimento)

```bash
voice-studio perfil criar nathan minha-gravacao.mov --confirm-own-voice
voice-studio perfil vocab nathan exemplos/pronuncia-pt.json --lang pt
```

**2. Falar um texto com a voz do perfil, no idioma que quiser**

```bash
voice-studio falar "Vamos usar a IA hoje" --perfil nathan --lang pt --accept-cpml -o out
```

**3. Traduzir um áudio ou vídeo com a sua voz** (o agente traduz entre as duas fases)

```bash
voice-studio traduzir video.mp4 --para en --perfil nathan --model ggml-small.bin
# traduza `source` para `text` em segments.json (no agente, a skill faz isso por você)
voice-studio traduzir video.mp4 --para en --perfil nathan --segmentos segments.json --accept-cpml
```

No Claude Code, `/perfil-de-voz`, `/falar` e `/traduzir` conduzem esses passos e pedem o consentimento e o aceite da licença (`/clonar-voz` e `/dublar` continuam como atalhos). Os comandos de baixo nível `sample`, `speak`, `transcribe` e `dub` seguem disponíveis.

**Saída nunca sobrescreve a entrada.** `traduzir` e `dub` recusam um `--out` igual à entrada e uma saída que já existe; para substituir uma saída existente, passe `--sobrescrever` (a entrada nunca é sobrescrita).

**Idiomas.** `pt`, `en`, `es`, `fr`, `de` e `it`. Só `pt` e `en` foram medidos com falas reais; nos demais o relatório traz `validated: false` e a CLI avisa.

**Códigos de saída.** `0` ok. `1` erro de uso ou validação (nada foi gerado). `2` só em `falar` e `traduzir`: gerou, mas há fala(s) suspeita(s) (`ok: false`); confira o `report.json`. `speak` e `dub` (baixo nível) saem `0` mesmo com linha suspeita ou estouro de tempo: leia o `report.json` ou o resumo impresso.

**Pronúncia.** O `pronuncia.json` é um mapa `{"como aparece": "como falar"}`. Troca por palavra inteira, só no texto da voz. Siglas em maiúsculas só casam em maiúsculas (`"IA"` não troca o verbo `ia`). `exemplos/pronuncia-pt.json` registra o sotaque mineiro do autor; use como ponto de partida.

**Sotaque.** Ele vem da **sua amostra** e do vocabulário: o modelo não tem sotaque mineiro pronto. Gere de 3 a 4 versões e escolha ouvindo. A transcrição automática **não prova a pronúncia** (ela reescreve marcas para a grafia padrão), então um humano precisa ouvir.

## Segurança e privacidade

- **Consentimento:** só clone a **sua** voz ou a de quem autorizou. A linha de comando exige `--confirm-own-voice`, e o agente pergunta antes de passar essa opção.
- **Privacidade:** amostras, falas e vídeos nunca são enviados para fora nem versionados (o `.gitignore` bloqueia `wav`, `mp3`, `m4a` e `mp4`). Não publique a voz de ninguém sem permissão.
- **Local:** o agente só lê e escreve texto; o áudio não vai para a conversa.

### Licenças (leia antes de usar)

| Parte | Licença |
|---|---|
| Código deste repositório | MIT |
| Modelo **XTTS-v2** (usado por padrão) | **Coqui CPML: somente uso não comercial** |

Os pesos do modelo **não** estão neste repositório: são baixados na primeira geração, e você aceita a licença com `--accept-cpml` (ou `VOICE_STUDIO_ACCEPT_CPML=1`). Para uso comercial, troque o motor por outro de licença permissiva implementando a interface `synth.Synth`. Veja o [`NOTICE.md`](NOTICE.md).

## Versões

| Versão | Novidades |
|---|---|
| **0.2.0** (em preparação, branch `feat/01-voz-multilingue-e-sotaque`) | Perfis de voz com consentimento registrado, vocabulário de pronúncia por idioma, catálogo de 6 idiomas (`pt` e `en` validados), comandos `falar` e `traduzir`, entrada e saída de áudio ou vídeo, proteção contra sobrescrever a entrada (`--sobrescrever`), skill única com adaptadores para Claude Code, agy e Codex. Falta o QA manual com voz real. |
| **0.1.0** | Primeira versão: voz clonada local (XTTS-v2), narração com vocabulário de pronúncia, várias versões por fala com guarda de duração, dublagem por segmento, consentimento e aviso de licença, plugin com skill e os comandos `/clonar-voz` e `/dublar`. |

## Status e limites

- **Testado:** `speak` em português e inglês pela linha de comando, no macOS (Apple Silicon), e testes automáticos (com sintetizador simulado, sem baixar o modelo).
- **Ainda não validado:** perfil, `falar` e `traduzir` com voz e vídeo reais (a verificação manual é feita ouvindo); a instalação pelo marketplace do Claude Code; agy e Codex: instruções prontas, não validado (veja [`docs/validacao-multiagente.md`](docs/validacao-multiagente.md)).
- **Idiomas além de `pt` e `en`:** qualidade não verificada (`validated: false`).
- **Marcas difíceis** (como "Forge SDD") pedem ajustar a grafia falada até soar certo.
- **Planejado:** validação com falas reais dos demais idiomas.

## Desenvolvimento e contribuição

```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.cache/voice-studio-venv   # ambiente fora do repositório
cd engine
uv run --python 3.11 --group dev pytest -q
uv run --python 3.11 --group dev ruff check .
```

O projeto segue o [Forge SDD](https://forge-sdd.org): regras em `sdd/memory/constitution.md` (IDs `VOZ-01` a `VOZ-09`) e decisões em `sdd/spec/adr/`. Para contribuir, leia o [`CONTRIBUTING.md`](CONTRIBUTING.md) e o [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md); para falhas de segurança ou de privacidade da voz, o [`SECURITY.md`](SECURITY.md).

## Licença

[MIT](LICENSE)

O modelo XTTS-v2 segue a [Coqui CPML](https://coqui.ai/cpml).

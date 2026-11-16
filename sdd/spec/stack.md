# Stack — voice-studio

## Dependências

| Camada | Escolha | Versão | Motivo |
|--------|---------|--------|--------|
| Runtime | python (uv) | 3.11 | `coqui-tts` suporta 3.11; `uv` isola o ambiente |
| CLI | typer | >=0.12 | borda fina, ajuda automática |
| Motor de voz (extra `xtts`) | coqui-tts (XTTS-v2) | >=0.27 | clona de amostra, multilíngue, local, CPU. Licença do modelo: CPML (não comercial) |
| Compatibilidade do extra | torch/torchaudio `<2.9`, transformers `<5`, six | — | versões que funcionaram sem `torchcodec` no Mac |
| Transcrição | whisper.cpp (`whisper-cli`) | externo | local; modelos ggml |
| Áudio e vídeo | ffmpeg | externo | corte, `atempo`, mixagem |
| Testes e lint | pytest, ruff | >=8, >=0.6 | portão de qualidade |
| DB | none | — | arquivos na pasta do usuário |

Apple Silicon: `uv run --python cpython-3.11-macos-aarch64-none` (sem isso o `uv` pode escolher x86_64 sob Rosetta e o PyTorch não instala).

## Layout do projeto
```
.claude-plugin/        manifesto do plugin (Claude Code)
skills/voice-studio/   corpo único da skill (todos os agentes)
commands/              /clonar-voz, /dublar
engine/src/voice_studio/  vocab, guard, synth, dub, audio, transcribe, consent, cli
engine/tests/          testes com sintetizador simulado
exemplos/              vocabulários e falas de exemplo (sem voz)
sdd/                   Forge SDD (constitution, spec, discovery)
AGENTS.md CLAUDE.md GEMINI.md   adaptadores finos por agente
```

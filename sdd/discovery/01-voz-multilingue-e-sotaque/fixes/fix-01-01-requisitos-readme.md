# Fix 01-01: requisitos incompletos no README

**Relato:** o padrão das skills (Regra 12) pede README pelo readme-studio com `## Requisitos` completa. O README tinha `## Antes de começar`, sem sistema testado, versões mínimas, o que é baixado (tamanho e lugar), máquina nem o que a pessoa fornece.
**Branch:** `fix/requisitos-readme`, a partir de `chore/forge-sdd` (PR empilhado).

## Feature Correlacionada
- **Origem:** `features/feat-01-07-skill-e-adaptadores.md` e o commit `e3a33d2` (docs: requisitos, perfis, proteção da mídia), que escreveu a tabela "Antes de começar".
- **Causa-raiz:** o template do readme-studio da época só pedia uma lista solta; os sete pontos fixos e o verificador (`scripts/verificar_readme.py`) vieram depois (readme-studio 0.4.0).
- **Evidência:** a seção antiga não dizia o sistema testado (só em "Status e limites"), deixava o `--python` do Apple Silicon fora dos requisitos, não citava onde o modelo XTTS fica, dava a entender que o modelo do Whisper vinha pronto e não falava de RAM, disco, contas nem do `--confirm-own-voice`. `verificar_readme.py` falhava: "falta a seção '## Requisitos'" e "sobrou '## Antes de começar'".

## Modelo do módulo
`enxuto`: só documentação. `## Antes de começar` vira `## Requisitos` (antes de `## Instalação`), tabela com os sete pontos. Nenhum código muda.

## Decisões do projeto aplicadas
Regra 12 (README com `## Requisitos`, `FLX-07`); Regra 7 (`uv`, ADR-0003); `VOZ-01`, `VOZ-02`, `VOZ-03` (consentimento, licença, local).

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Lista de requisitos | `README.md`, "Antes de começar" | 6 itens soltos | estender | Vira a seção `Requisitos` com os sete pontos. |
| Licenças | `README.md`, "Licenças (leia antes de usar)", `NOTICE.md` | tabela completa | reusar | Requisitos só aponta para ela. |
| Nota do Apple Silicon | `README.md`, "Instalação"; `sdd/spec/stack.md` | `--python cpython-3.11-macos-aarch64-none` | reusar | Repetida em "Onde roda", que é onde a pessoa decide se roda. |

## Dependências novas
Nenhuma.

## Rules e IDs da Constituição Aplicáveis
`FLX-07`, `DUP-01`, `VOZ-01`, `VOZ-02`, `VOZ-03`.

## Fontes de cada ponto
| Ponto | Fonte no código |
|---|---|
| Python 3.11 | `engine/pyproject.toml`: `requires-python = ">=3.11,<3.12"` |
| uv 0.5+ | `[dependency-groups]` em `engine/pyproject.toml` (suportado desde o uv 0.4.27); testado 0.9.7 |
| `--python` no Apple Silicon | `sdd/spec/stack.md`; README, "Instalação" |
| ffmpeg/ffprobe | `audio.py` (`ffmpeg`, `ffprobe` por lista de argumentos) |
| `whisper-cli` | `transcribe.py`: `audio.run(["whisper-cli", ...])` |
| Modelo Whisper não baixado sozinho | `transcribe.resolve_model`: exige `--model` ou `VOICE_STUDIO_WHISPER_MODEL` |
| XTTS-v2 e cache | `synth.XTTS_MODEL`; `trainer/io.py:get_user_data_dir` (do `coqui-tts`): `TTS_HOME`, `XDG_DATA_HOME`, `~/Library/Application Support/tts` (macOS), `~/.local/share/tts` (Linux) |
| Ambiente ~1 GB | `engine/.venv` com o extra `xtts` medido em 990 MB |
| Amostra 6 a 30 s | `audio.extract_sample`: `if not 6.0 <= duration <= 30.0` |
| Consentimento e licença | `cli.py` (`--confirm-own-voice`, `--accept-cpml`), `consent.py` (`VOICE_STUDIO_ACCEPT_CPML`) |
| Perfis | `profile.py`: `VOICE_STUDIO_HOME` ou `~/.voice-studio/perfis` |

## Critérios de Aceitação Executáveis
1. `uv run verificar_readme.py README.md` (readme-studio 0.4.0) imprime `requisitos: ok`.
2. `grep -c '^## Requisitos' README.md` = 1 e `grep -c '^## Antes de começar' README.md` = 0.
3. As fontes batem: `grep -n 'requires-python = ">=3.11,<3.12"' engine/pyproject.toml`, `grep -n '6.0 <= duration <= 30.0' engine/src/voice_studio/audio.py` e `grep -n 'VOICE_STUDIO_WHISPER_MODEL' engine/src/voice_studio/transcribe.py` encontram as linhas.
4. `cd engine && uv run ruff check && uv run pytest -q` passam.

# feat-01-01-modulo-profile — Perfil de voz (criar, listar, carregar, validar)

## Modelo do módulo
completo — módulo novo com persistência em disco, validação de nomes e caminhos e regra de privacidade.

## Decisões do projeto aplicadas
ADR-0001 (voz local; sotaque pela amostra e vocabulário). ADR-0002 (a criar nesta task: formato do perfil e pasta de perfis). Rules: `voz-consentimento-e-privacidade`, `sdd-seguranca`, `sdd-reuso-e-duplicacao`.

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Consentimento | `consent.py` | `require_consent`, `require_license` | reusar | O perfil só é criado depois de `require_consent`; um único dono |
| Amostra limpa a partir de mídia | `audio.extract_sample` | mono 22,05 kHz, 6 a 30 s | reusar | O perfil normaliza qualquer áudio ou vídeo para a amostra |
| Validação de entradas | `vocab.clean` (padrão de erros) | `VoiceError` com mensagem clara | reusar | Mesma exceção e estilo de mensagem |
| Perfil de voz | — | nada | criar | Conceito novo; registrar o dono em `sdd/spec/concepts.md` |

## Dependências novas
Nenhuma (`ARQ-04`): `json`, `pathlib`, `shutil`, `datetime`.

## Rules e IDs da Constituição Aplicáveis
SEG-01, SEG-02, VOZ-01, VOZ-04, ARQ-10, DUP-01, TST-01

## Escopo
- `core/profile.py` (em `engine/src/voice_studio/profile.py`): `create(nome, origem, confirm, base, start, duration, ajustes)`, `load(nome, base)`, `list_profiles(base)`.
- Pasta base: `~/.voice-studio/perfis/` (padrão); `VOICE_STUDIO_HOME` ou `--perfis-dir` sobrescrevem. Se a pasta base estiver dentro de um repositório git (`.git` em algum pai), erro claro (`VOZ-04`).
- Layout: `<base>/<nome>/perfil.json` + `voz-ref.wav` (amostra normalizada). `perfil.json`: `nome`, `criado_em` (ISO 8601), `consentimento` (`confirmado_pelo_usuario: true`, `em`), `amostra`, `ajustes` (`velocidade`, `takes`), `vocabularios` (mapa idioma -> arquivo; preenchido na feat-01-03).
- Nome do perfil: `^[a-z0-9][a-z0-9_-]{0,39}$`; qualquer outro (`..`, barra, controle) é rejeitado na borda (`SEG-01`). Escrita só dentro de `<base>/<nome>/` (`SEG-02`); criar perfil existente é erro (sem sobrescrever).
- CLI: `voice-studio perfil criar NOME ORIGEM --confirm-own-voice [--start --duration]`, `perfil listar`, `perfil mostrar NOME` (nunca imprime o caminho da amostra além do nome do arquivo, `SEG-05`).
- `sdd/spec/adr/adr-0002-perfis-de-voz.md` e a linha de `profile` em `sdd/spec/concepts.md`.

## Critérios de Aceitação Executáveis
- `cd engine && uv run pytest tests/test_profile.py -k criar`: cria o perfil com amostra existente e `confirm=True`; sem confirmar, falha; grava `consentimento` com data; a amostra fica em `<base>/<nome>/voz-ref.wav`.
- `uv run pytest tests/test_profile.py -k seguranca`: nomes `..`, `a/b`, vazio e com caractere de controle são rejeitados; perfil existente não é sobrescrito; perfil inexistente ou com `perfil.json` corrompido dá erro claro; base dentro de repositório git é rejeitada.
- `uv run pytest tests/test_profile.py -k listar`: lista os perfis em ordem e ignora pastas sem `perfil.json`.
- `uv run pytest && uv run ruff check` passam.

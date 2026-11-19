# feat-03-01-prompt-instalacao — Script de requisitos e prompt de instalação para a IA

**Pedido:** é comum os requisitos terem um prompt que fala com a IA para verificar; nesse prompt ela usa um script para checar se tem os requisitos e, se não tem, já considera fazer a instalação. O prompt fica em quote, na instrução inicial, antes do `plugin marketplace add`.
**Branch:** `feat/03-prompt-instalacao`, a partir de `origin/main` (o PR #4, que levou o fix de requisitos para a `main`, já foi mesclado).

## Modelo do módulo
`enxuto`: um script avulso `scripts/requisitos.py` (PEP 723, só biblioteca padrão, roda antes do clone pela URL raw) com dois comandos, `checar` e `instalar`. Cada requisito tem `nome`, `estado` (`ok`, `faltando`, `opcional`), `versao`, `obrigatorio`, `tipo` (`sistema`, `projeto`, `download`, `seu`), `comandos` (listas de argumentos) e `explicacao`. O ambiente (`which`, execução, variáveis, disco) é injetável. Fora do pacote `engine/`, porque precisa rodar antes de qualquer `uv sync`.

## Decisões do projeto aplicadas
`VOZ-10` (nova: o que é determinístico vira script e o prompt usa o script); `VOZ-01` e `VOZ-02` (o script nunca passa `--confirm-own-voice` nem `--accept-cpml`); Regra 7 e ADR-0003 (`uv`, nunca `pip`); Regra 12 e `FLX-07` (README com `## Requisitos`); `TST-04` e `VOZ-09` (testes sem rede, sem instalar nada).

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Doctor ou checagem de ambiente | `engine/src/voice_studio/cli.py` | nenhum comando de diagnóstico | criar | Não há o que reusar; o script nasce fora do pacote para rodar antes do clone. |
| Lista de requisitos | `README.md`, `## Requisitos` (fix 01-01) | tabela de sete pontos | reusar | O script segue a mesma lista e os mesmos comandos; a tabela fica. |
| Caminho do modelo Whisper | `transcribe.resolve_model` | `--model` ou `VOICE_STUDIO_WHISPER_MODEL` | reusar | O check usa a mesma variável e avisa que o padrão não é achado sozinho. |
| Pasta dos perfis | `profile.py` | `VOICE_STUDIO_HOME` ou `~/.voice-studio/perfis` | reusar | O check só conta perfis, sem ler conteúdo. |

## Dependências novas
Nenhuma (só biblioteca padrão; `ARQ-04`).

## Rules e IDs da Constituição Aplicáveis
`VOZ-10`, `VOZ-01`, `VOZ-02`, `VOZ-09`, `TST-04`, `FLX-07`, `ARQ-04`, `ARQ-06`, `SEG-01`.

## Escopo
- `scripts/requisitos.py` com `checar` (tabela ou `--json`, código 1 se faltar obrigatório) e `instalar` (repete o `checar`, pula o que está ok, mostra o comando; sem `--sim` pergunta antes de cada um; sem terminal só mostra; com `--sim` roda sem perguntar; itens `seu` só explicados).
- Itens: sistema, homebrew, uv (>= 0.5), Python 3.11 arm64 no Apple Silicon, ffmpeg, ffprobe, whisper-cli (opcional), modelo Whisper (opcional), motor com o extra xtts (opcional, o uv cria no primeiro uso), modelo XTTS-v2 (seu), perfil de voz (seu), disco.
- README: quote "Cole isto na sua IA antes de instalar" dentro de `## Requisitos`, antes da tabela e da instalação; versão 0.2.1 e tabela de versões.
- Skill: passo 0 "Requisitos" antes do consentimento.
- Constituição: `VOZ-10`, citada nas faixas de IDs (README, AGENTS, GEMINI, CLAUDE, CONTRIBUTING) e em `.agents/rules/voz-multiagente.md`.
- Fora: tirar temas e perfis pessoais do repositório.

## Critérios de Aceitação Executáveis
1. `cd engine && uv run --python cpython-3.11-macos-aarch64-none --group dev pytest -q` passa, incluindo `tests/test_requisitos.py` (checar, JSON, código de saída, instalar sem terminal, com "não", com `--sim` uma vez só e nunca com `--accept-cpml`/`--confirm-own-voice`, nada a instalar quando tudo ok, quote no README antes de `## Instalação`).
2. `uv run --group dev ruff check . ../scripts` sem erros.
3. `uv run scripts/requisitos.py checar` imprime a tabela e sai 0 nesta máquina; `uv run scripts/requisitos.py instalar </dev/null` só mostra comandos.
4. `uv run verificar_readme.py README.md` (readme-studio `main`) imprime `requisitos: ok`.
5. `grep -c 'Cole isto na sua IA antes de instalar' README.md` = 1 e `grep -n 'VOZ-10' sdd/memory/constitution.md` acha a regra.

# Release Notes — voice-studio

Este arquivo registra o histórico de entregas de produto deste projeto.

## Entregas

### Versão 0.2.1 — Requisitos por script e prompt de instalação para a IA

Iniciativa 03 (`feat/03-prompt-instalacao`).

*   **`scripts/requisitos.py`** (só biblioteca padrão, roda antes do clone pela URL raw): `checar` (tabela ou `--json`, código 1 se faltar algo obrigatório) e `instalar [--sim] [item ...]` (só os itens citados ou tudo o que falta; pergunta antes de cada item; `--sim` roda sem perguntar; nome desconhecido sai 2).
*   **Nunca aceita licença nem declaração** pelo usuário: `--accept-cpml` e `--confirm-own-voice` continuam com você; esses itens o script só explica.
*   **README:** prompt "para colar na sua IA" dentro de Requisitos, antes da instalação; a IA pergunta antes do uv e pede o ok item por item.
*   **Skill:** passo 0 de requisitos. **Constitution:** nova regra `VOZ-10` (o que é determinístico vira script e o prompt usa o script).

### Versão 0.2.0 — Perfis de voz, `falar` e `traduzir` (não publicada como tag)

Iniciativa 01 (`feat/01-voz-multilingue-e-sotaque`), já na `main`. Falta o QA manual com voz real (feat-01-08, feito ouvindo).

*   **Perfis de voz:** `perfil criar|listar|mostrar|vocab`. O perfil guarda a amostra normalizada, o consentimento (data e confirmação do usuário) e o vocabulário de pronúncia por idioma, em `~/.voice-studio/perfis/<nome>/`, sempre fora de repositórios git (ADR-0002).
*   **Catálogo único de idiomas:** `pt`, `en`, `es`, `fr`, `de` e `it`. Só `pt` e `en` foram medidos com falas reais; os demais saem `validated: false` e a CLI avisa. A guarda de duração consulta o catálogo.
*   **`falar`:** você digita o texto e a voz do perfil fala no idioma escolhido, com várias versões por fala e relatório (`ok`, `validated`, `falado`). Código de saída `2` quando há fala suspeita.
*   **`traduzir`:** áudio ou vídeo para outro idioma em duas fases (o agente traduz o campo `text` entre elas); áudio entra e sai como áudio, vídeo como vídeo.
*   **Entrada e saída de áudio ou vídeo** na dublagem, com a extensão da saída validada antes de gastar tempo no motor.
*   **Proteção da mídia:** `traduzir` e `dub` recusam `--out` igual à entrada e saída existente, salvo `--sobrescrever`; o `segments.json` é gravado com abertura exclusiva.
*   **Skill única e adaptadores:** `perfil-de-voz`, `falar` e `traduzir` no plugin; `AGENTS.md` (Codex), `GEMINI.md` (agy) e `CLAUDE.md` apontam para a mesma skill. agy e Codex: instruções prontas, ainda não validados.
*   **Projeto:** Forge SDD 4.8.0 instalado, Constitution com os IDs `VOZ-01` a `VOZ-09`, README comercial, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` e template de PR.
*   **Como atualizar:** `git pull` e `uv run --python 3.11 --extra xtts voice-studio --help` em `engine/`. Perfis antigos não existem (a 0.1.0 não tinha perfis).

### Versão 0.1.0 — Voz clonada local (primeira versão)

*   Voz clonada local com XTTS-v2, narração com vocabulário de pronúncia, várias versões por fala com guarda de duração, dublagem por segmento (português para inglês), consentimento explícito e aceite da licença CPML, plugin com skill e os comandos `/clonar-voz` e `/dublar`.

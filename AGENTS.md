# AGENTS.md — voice-studio

Este repositório é o voice-studio: clona a voz do próprio usuário, 100% local, para narrar um texto digitado ou dublar áudio e vídeo para outro idioma, com controle de idioma, sotaque (foco em português do Brasil, incluindo o mineiro) e pronúncia. Veja `README.md`.

## Como operar aqui

Fonte única da skill: `skills/voice-studio/SKILL.md` (e `skills/voice-studio/references/`). Antes de qualquer tarefa de voz (clonar, narrar, dublar, corrigir pronúncia), leia a skill. A CLI é o contrato comum a todos os agentes: `uv run --python 3.11 --extra xtts voice-studio <comando>` em `engine/` (Apple Silicon: `--python cpython-3.11-macos-aarch64-none`).

## Regras do projeto (resumo; texto completo em `sdd/memory/constitution.md`, IDs `VOZ-01` a `VOZ-09`)

- Só clone a voz do próprio usuário ou de quem autorizou. Pergunte uma vez; nunca passe `--confirm-own-voice` por conta própria.
- O modelo XTTS-v2 é CPML (uso não comercial): o usuário aceita explicitamente (`--accept-cpml`). Nunca distribua pesos.
- Local por padrão: você só lê e escreve texto; nunca peça ou anexe áudio à conversa.
- Nunca versione amostras, áudios ou vídeos. Sem dados de cliente em exemplos e testes.
- A pronúncia vem do vocabulário (grafia falada só no texto da voz). A transcrição não prova pronúncia: peça ao usuário para ouvir.
- Não prometa sotaque: ele vem da amostra e do vocabulário.
- Siga o Forge SDD: nunca comite em `main`; uma branch por iniciativa (`sdd/discovery/`); `forge brief` antes de planejar.

## Comandos de voz
`voice-studio perfil|falar|traduzir` (e `sample|speak|transcribe|dub`), em `engine/`; corpo completo só em `skills/voice-studio/SKILL.md`.

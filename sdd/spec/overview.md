# Overview — voice-studio

Motor local e plugin de agente que clona a voz do usuário para (1) narrar um texto digitado e (2) dublar áudio ou vídeo para outro idioma, com perfis de idioma, sotaque e pronúncia. Tudo roda na máquina do usuário.

## Índice
- `stack.md` — tecnologias
- `modules.md` — componentes
- `flows.md` — fluxos principais
- `decisions.md` — decisões de design
- `concepts.md` — conceitos e donos (`DUP-01`)

---

## Arquitetura (C4 Model)

### Nível 1: Contexto
```mermaid
graph TB
  User((Usuário))
  Agent[Claude Code / agy / Codex]
  VS[voice-studio]
  Model[(Modelo XTTS-v2 local)]
  Tools[ffmpeg e whisper.cpp]
  User --> Agent
  Agent --> VS
  VS --> Model
  VS --> Tools
```

### Nível 2: Containers
```mermaid
graph LR
  Skill[Skill única] --> CLI[CLI typer]
  CLI --> Core[Domínio: vocab, guard, synth, dub]
  Core --> Audio[audio e transcribe]
  Core --> Engine[Motor Synth injetável]
  Engine --> XTTS[XTTS-v2]
```

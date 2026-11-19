# Módulos — voice-studio

## `consent`
**Responsabilidade:** consentimento da voz e aceite da licença do modelo (`VOZ-01`, `VOZ-02`).
- [x] `require_consent`, `require_license`

## `vocab`
**Responsabilidade:** vocabulário de pronúncia: carga validada e troca por palavra inteira (`VOZ-05`).
- [x] `load`, `apply_spoken`
- [x] Vocabulário por idioma dentro do perfil (feat 01)

## `profile`
**Responsabilidade:** perfil de voz (amostra normalizada, consentimento, ajustes, vocabulário por idioma) em `VOICE_STUDIO_HOME` ou `~/.voice-studio/perfis`, sempre fora de repositório git (`VOZ-01`, `VOZ-04`, ADR-0002).
- [x] `create`, `load`, `set_vocabulary`

## `languages`
**Responsabilidade:** catálogo único de idiomas (código, caracteres por segundo, `validated`) (`DUP-04`).
- [x] `pt`, `en`, `es`, `fr`, `de`, `it`

## `falar` e `traduzir`
**Responsabilidade:** casos de uso: texto digitado vira fala na voz do perfil; áudio ou vídeo vira outro idioma em duas fases (o agente traduz só texto, `VOZ-03`).
- [x] `falar`, `traduzir` (`prepare`, `render`)

## `guard`
**Responsabilidade:** duração esperada, detecção de fala suspeita e escolha da melhor variação (`VOZ-06`).
- [x] `expected_seconds`, `is_suspect`, `pick`

## `synth`
**Responsabilidade:** interface `Synth`, motor XTTS (import tardio) e `speak` (N variações) (`VOZ-09`).
- [x] `xtts_synth`, `speak`

## `dub`
**Responsabilidade:** segmentos com tempo e texto traduzido, encaixe e mixagem.
- [x] `load_segments`, `dub`

## `audio` e `transcribe`
**Responsabilidade:** ffmpeg (amostra, corte de pontas, `atempo`, mix) e whisper.cpp local; bordas com processos externos (`SEG-03`).

## `cli`
**Responsabilidade:** borda: valida a entrada, aplica consentimento, delega ao domínio (`ARQ-10`).

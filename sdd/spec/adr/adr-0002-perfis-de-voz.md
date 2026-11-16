# ADR-0002: Perfis de voz fora do repositório

- **Data:** 2026-11-16
- **Status:** `aprovado`
- **Regras afetadas (IDs da constitution):** `VOZ-01`, `VOZ-04`, `SEG-01`, `SEG-02`
- **Autor / Responsável:** Builder (feat-01-01-modulo-profile)

## Contexto

A iniciativa 01 (voz multilíngue e sotaque) precisa guardar, por pessoa, a amostra de voz, o consentimento, os ajustes e o vocabulário por idioma. A amostra é dado pessoal e não pode ir parar no repositório nem ser sobrescrita sem aviso. A feat-01-01 cria o módulo `profile`.

## Opções Consideradas

1. **Pasta dentro do projeto (ex.: `perfis/`):** simples de achar, mas arrisca commitar áudio de voz e quebra a privacidade (`VOZ-04`).
2. **Pasta do usuário fora do repositório (`~/.voice-studio/perfis/`):** isola o dado pessoal; exige uma checagem de segurança da pasta base.
3. **Banco de dados local:** mais flexível, mas é dependência e complexidade sem necessidade (`ARQ-04`).

## Decisão

Opção 2. Layout: `<base>/<nome>/perfil.json` + `voz-ref.wav`. A base padrão é `~/.voice-studio/perfis/`, sobrescrita por `VOICE_STUDIO_HOME` ou pelo parâmetro `base` (`--perfis-dir`). Uma base dentro de repositório git (`.git` em qualquer pai) é recusada. O nome segue `^[a-z0-9][a-z0-9_-]{0,39}$` (`SEG-01`), a escrita fica só em `<base>/<nome>/` (`SEG-02`) e perfil existente nunca é sobrescrito.

`perfil.json`: `nome`, `criado_em` (ISO 8601), `consentimento` (`confirmado_pelo_usuario: true`, `em`), `amostra` (`voz-ref.wav`), `ajustes` (`velocidade`, `takes`) e `vocabularios` (mapa idioma -> arquivo; preenchido na feat-01-03). O consentimento é verificado por `consent.require_consent` antes de qualquer escrita (`VOZ-01`); a amostra é normalizada por `audio.extract_sample`.

## Consequências

- **Positivas:** a voz nunca entra no git por engano; um dono único para o perfil; sem dependência nova.
- **Negativas / Trade-offs:** o perfil não viaja com o projeto; o usuário recria ou copia a pasta manualmente.
- **Ações de acompanhamento:** feat-01-03 preenche `vocabularios`; as features seguintes consomem `profile.load`.

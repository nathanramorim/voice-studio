---
description: Como cumprir pronúncia por vocabulário, guarda de qualidade, honestidade sobre sotaque e motor injetável.
globs: ["engine/src/**", "engine/tests/**", "exemplos/**", "skills/**"]
regras: [VOZ-05, VOZ-06, VOZ-07, VOZ-09]
---

# Guia Prático — Pronúncia, Qualidade e Sotaque

Procedimentos para `VOZ-05`, `VOZ-06`, `VOZ-07` e `VOZ-09` de `sdd/memory/constitution.md` (`GOV-04`).

## Pronúncia (`VOZ-05`)
- A troca acontece em `vocab.apply_spoken`, só no texto enviado ao motor. Texto original, legenda e relatórios mantêm a grafia da tela.
- Siglas em maiúsculas só casam em maiúsculas (`IA` não troca o verbo `ia`). Termos comuns ignoram caixa. Uma passada só, palavra inteira.
- Vocabulários vivem em perfis por idioma e sotaque (`exemplos/`), nunca embutidos no código.

## Guarda de qualidade (`VOZ-06`)
- `synth.speak` gera `takes` variações (padrão 3) e `guard.pick` descarta as de duração fora de 0,5x a 1,6x do esperado.
- Se todas forem suspeitas, a linha sai com `ok: false` e o comando avisa; nunca entregue em silêncio.
- Constantes de caracteres por segundo vivem só em `guard.CPS` (`DUP-04`); recalibre com falas reais.

## Sotaque e pronúncia (`VOZ-07`)
- O sotaque vem da amostra e do vocabulário. Para português do Brasil mineiro: amostra de fala natural da própria pessoa, vocabulário com a grafia falada, 3 a 4 variações e escolha ouvindo.
- Não escreva "sotaque garantido". Não use a transcrição (Whisper) como prova: ela reescreve marcas para a grafia padrão. Peça ao humano para ouvir as falas com termos do vocabulário.

## Motor injetável (`VOZ-09`)
- Todo código novo que gera voz recebe `Synth` por parâmetro; testes usam sintetizador simulado (seno) e nunca importam `TTS`.
- `xtts_synth` é o único ponto com import de `TTS`, tardio.

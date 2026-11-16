# ADR-0001: Voz clonada local com XTTS-v2, sotaque pela amostra e vocabulário

- **Data:** 2026-11-16
- **Status:** `aprovado`
- **Regras afetadas (IDs da constitution):** `VOZ-01` a `VOZ-09` (novas), `SEG-05`, `DUP-10`
- **Autor / Responsável:** Nathan Amorim

## Contexto

O autor precisava narrar reels com a própria voz, em português do Brasil com sotaque mineiro, e dublar vídeos para inglês, sem pagar serviço de voz nem enviar a voz para a nuvem. Num experimento real (reel do Forge SDD 4.8), o XTTS-v2 local clonou o timbre a partir de 28 s de gravação, mas: alucinou uma fala (3 s viraram 10 s), errou a pronúncia de siglas e marcas (IA, PR, Gemini, Codex, Copilot, "Forge SDD") e a transcrição automática não serviu para confirmar a pronúncia. O sotaque saiu como o da amostra, não por configuração.

## Opções Consideradas

1. **Serviço de nuvem (ex.: HeyGen):** melhor qualidade e uso comercial, mas envia a voz para fora, custa e depende de login.
2. **Chatterbox (MIT):** licença permissiva e pt-BR, mas não validado na máquina do autor.
3. **XTTS-v2 local:** comprovado, gratuito, multilíngue, CPU. Licença CPML (não comercial) e pronúncia imperfeita.

## Decisão

XTTS-v2 local como motor padrão, atrás da interface `synth.Synth` (trocável). Código MIT; pesos nunca distribuídos; aceite da CPML explícito do usuário. Sotaque definido pela amostra e pelo vocabulário de pronúncia, sem prometer o que o motor não tem. Guarda de duração com N variações. Um corpo de skill com adaptadores finos para Claude Code, agy e Codex. Cria os IDs `VOZ-01` a `VOZ-09` na Constituição.

## Consequências

- **Positivas:** privacidade total, custo zero, motor trocável, qualidade protegida contra falas defeituosas.
- **Negativas / Trade-offs:** uso comercial exige trocar o motor; sotaque depende da amostra; pronúncia exige ouvir e iterar; geração em CPU leva dezenas de segundos por fala.
- **Ações de acompanhamento:** perfis por idioma e sotaque; entrada por áudio com texto digitado e dublagem com idioma escolhido; adaptadores multiagente; avaliar motor alternativo (D6).

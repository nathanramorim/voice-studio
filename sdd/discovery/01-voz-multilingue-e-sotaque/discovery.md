# Discovery — 01 Voz multilíngue, perfis e sotaque

## Problema
Hoje o voice-studio já clona a voz e dubla, mas o uso ainda é de quem leu o código: a amostra, o vocabulário e o consentimento são argumentos soltos a cada comando; a entrada de dublagem é só vídeo; o idioma de destino é só inglês na prática; e o sotaque (português do Brasil mineiro, muito diferente do "neutro") não tem onde morar. No reel do Forge SDD 4.8 foram precisas várias regerações para acertar "IÁ", "PIER" e nomes de marcas.

## Para quem
Criadores de conteúdo e devs que querem narrar e dublar com a **própria voz**, de graça e sem enviar áudio para a nuvem, a partir do agente que já usam (Claude Code, agy ou Codex).

## Jornada
1. **Cria um perfil de voz** uma vez: nome, amostra de áudio, consentimento e vocabulário de pronúncia por idioma (ex.: perfil `mineiro`).
2. **Fala um texto**: "enviei o áudio e digitei o que quero que saia na voz": `falar --perfil mineiro "texto"`.
3. **Traduz um áudio ou vídeo**: "envio o áudio e escolho o idioma": `traduzir entrada --para en --perfil mineiro`. O agente traduz o texto, a voz é a do perfil.
4. **Ouve e aprova**; se uma palavra soar errada, ajusta a grafia falada no perfil e regera.

## Regras de negócio
- Todas as regras `VOZ-01` a `VOZ-09` da Constitution. Em especial: consentimento (`VOZ-01`), local (`VOZ-03`), privacidade (`VOZ-04`), pronúncia por vocabulário (`VOZ-05`), honestidade sobre sotaque (`VOZ-07`).
- Um perfil só nasce com `--confirm-own-voice`; o consentimento fica registrado no perfil (data e quem confirmou: o usuário, nunca o agente).
- A amostra do perfil nunca fica dentro de um repositório: o perfil vive numa pasta do usuário, fora do código (decisão a registrar na ADR-0002).
- O sotaque vem da amostra e do vocabulário do perfil; o produto não promete sotaque que o motor não tem.

## Decisões do Clarify (respondidas pelo usuário)
- **"Regular o sotaque" = perfis de voz** (amostra + vocabulário + ajustes). Sem calibração assistida nesta iniciativa.
- **Idiomas:** os 6 do XTTS (pt, en, es, fr, de, it) disponíveis com `--para`; **inglês é o único validado de ponta a ponta**, os demais saem marcados `validated: false`.

## Escopo
**Dentro**
- Perfil de voz: criar, listar, carregar e validar (nome seguro, amostra existente, consentimento registrado).
- Vocabulário de pronúncia **por idioma** dentro do perfil.
- `falar`: texto digitado + perfil (ou amostra avulsa) -> fala.
- Entrada **áudio ou vídeo** e saída correspondente (áudio -> áudio dublado; vídeo -> vídeo dublado).
- `traduzir ... --para <idioma>`: transcrição local, tradução pelo agente, voz do perfil, encaixe no tempo.
- Guarda de duração para os 6 idiomas, com os de baixa calibragem sinalizados.
- Skill, comandos e adaptadores para Claude Code, agy e Codex com checklist de validação.

**Fora**
- Calibração assistida de sotaque (gerar frases-teste para escolher amostra).
- Motor alternativo de licença permissiva (D6) e medição objetiva de "soa mineiro" (D7).
- Conversão voz-para-voz, sincronia labial, qualquer serviço de nuvem.

## Riscos
| Risco | Mitigação |
|---|---|
| O XTTS não reproduz sotaque que não está na amostra | `VOZ-07`: o perfil documenta que o sotaque é o da amostra; aprovação final ouvindo (C1) |
| Geração em CPU é lenta (20 a 60 s por fala): dublar 1 min pode levar minutos | Relatório de progresso e tempo; `--takes` ajustável |
| Idiomas fora do inglês com qualidade desconhecida | Marcados `validated: false` até haver teste manual |
| A amostra do perfil vazar por commit | Perfil fora do repositório + `.gitignore` + checagem na CLI se a pasta está dentro de um repo git |
| Tradução do agente estoura o tempo do segmento | `overflow` no relatório e pedido de texto mais curto (já existe no `dub`) |
| Licença CPML do modelo | Aceite explícito e aviso mantidos (`VOZ-02`) |

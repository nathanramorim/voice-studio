# Política de segurança

O voice-studio lida com a **voz das pessoas**. Tratamos falhas de segurança e de privacidade como prioridade.

## O que conta como falha de segurança

- Vazamento de amostra, áudio gerado ou perfil de voz (por log, relatório, commit, rede ou anexo à conversa).
- Burla do consentimento (`--confirm-own-voice`) ou do aceite da licença do modelo (`--accept-cpml`), por exemplo um caminho que gere voz sem eles.
- Path traversal ou escrita fora da pasta esperada (nomes de perfil, `--out`, `--perfis-dir`), inclusive sobrescrita da mídia de entrada.
- Execução de comandos por entradas não confiáveis (nomes de arquivo, textos, segmentos).
- Qualquer chamada de rede inesperada no motor.

## Como reportar

**Não abra uma issue pública** com detalhes. Use o relato privado do GitHub: aba **Security** do repositório, **Report a vulnerability**. Se ele não estiver disponível, abra uma issue pedindo um canal privado, **sem** detalhes técnicos e **sem** anexar áudio ou perfis.

Inclua: versão (ou commit), sistema operacional, passos para reproduzir e o impacto. **Não envie amostras de voz reais**; use áudio sintético para demonstrar.

## O que esperar

Este é um projeto mantido por uma pessoa, sem prazo garantido. Procuramos confirmar o recebimento em poucos dias e corrigir falhas de privacidade e de consentimento antes de qualquer funcionalidade nova. Quem reportar com responsabilidade é creditado, se quiser.

## Versões suportadas

Só a versão mais recente da branch principal recebe correções.

## Fora do escopo

- A qualidade ou o sotaque da voz gerada (veja o README, "Status e limites").
- Vulnerabilidades dentro do modelo XTTS-v2, do PyTorch, do ffmpeg ou do whisper.cpp: reporte aos projetos deles.
- Uso indevido da ferramenta para clonar a voz de quem não autorizou: o projeto exige consentimento, mas não consegue impedir uma pessoa de ignorar a regra em uma cópia local.

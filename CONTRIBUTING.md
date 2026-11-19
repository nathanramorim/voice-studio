# Contribuindo com o voice-studio

Obrigado por querer ajudar! Este projeto clona a voz de quem usa, então algumas regras de privacidade e consentimento valem mais do que qualquer funcionalidade. Elas estão na [Constitution](sdd/memory/constitution.md) (IDs `VOZ-01` a `VOZ-10`).

## Antes de tudo

- **Nunca** envie amostras de voz, áudios gerados, vídeos ou perfis (`perfil.json`, `voz-ref.wav`) em issues, PRs, testes ou exemplos. O `.gitignore` já bloqueia `wav`, `mp3`, `m4a`, `mp4` e outros; não o contorne. Testes usam áudio sintético (seno) gerado em `tmp_path`.
- Só use a **sua** voz ou a de quem autorizou. Nada de clonar a voz de terceiros sem permissão.
- Nada de dados de clientes ou de outros projetos em exemplos, testes e logs.
- Nenhuma chamada de rede ou serviço de nuvem de voz no motor (`VOZ-03`).

## Preparar o ambiente

Requisitos: `uv`, `ffmpeg` (com `ffprobe`) e, só para transcrever, `whisper-cpp`. Veja o [README](README.md#antes-de-começar).

```bash
git clone https://github.com/nathanramorim/voice-studio
cd voice-studio/engine
export UV_PROJECT_ENVIRONMENT=$HOME/.cache/voice-studio-venv
uv run --python 3.11 --group dev pytest -q
uv run --python 3.11 --group dev ruff check .
```

- **Ambiente virtual fora do repositório.** O portão `forge gate` (P-13) varre o repositório atrás de segredos e acusa um falso positivo dentro de `engine/.venv` (um bloco base64 de fonte do Pillow). Por isso o ambiente fica em `~/.cache`, e não em `engine/.venv`.
- **Apple Silicon:** se o `uv` escolher x86_64 e o PyTorch não instalar, use `--python cpython-3.11-macos-aarch64-none`.
- O extra `xtts` (motor de voz e PyTorch) **não** é necessário para rodar os testes.

## Como trabalhamos (Forge SDD)

O projeto usa o [Forge SDD](https://forge-sdd.org): spec antes do código.

1. **Nunca commite em `main`.** Uma branch por iniciativa: `feat/<id>-<nome>` (ex.: `feat/01-voz-multilingue-e-sotaque`).
2. Para algo maior, abra uma conversa na issue e escreva o `discovery` em `sdd/discovery/<id>-<nome>/` (`/discovery`, `/split-features`, `/implementar` nos agentes). Cada task tem spec com critérios **executáveis** (`TST-01`).
3. Mudou uma regra da Constitution ou uma decisão estrutural? Registre uma ADR em `sdd/spec/adr/` no mesmo PR (`GOV-01`, `FLX-05`).
4. Antes de abrir o PR: testes e lint passam e `forge gate` passa (`forge doctor` ajuda).
5. Preencha o [template de PR](.github/pull_request_template.md), incluindo o checklist da Constitution.

## Padrões de código

- Português do Brasil em mensagens, docstrings e documentação; nomes de código seguem o estilo existente.
- Domínio em módulos do pacote (`vocab`, `guard`, `synth`, `dub`, `profile`, ...), CLI só delega (`ARQ-10`). Reuse antes de criar (`DUP-03`); um conceito, uma casa (`sdd/spec/concepts.md`).
- O motor de voz entra **por injeção** (`synth.Synth`). Testes nunca baixam modelo, nunca importam `TTS` e nunca usam rede (`VOZ-09`, `TST-04`). Teste que precisa de ffmpeg usa `skipif`.
- Dependência nova só com justificativa na spec (`ARQ-04`, `SEG-07`).
- Chamadas a ffmpeg, ffprobe e whisper sempre com **lista de argumentos**, nunca por shell (`SEG-03`).
- Commits em pt-BR, no formato `tipo(escopo): resumo` (ex.: `feat(01-06): ...`, `fix(01-06): ...`).

## Contribuições comuns

- **Novo idioma ou validação de idioma:** o catálogo único fica em `languages.py`. Só marque `validated: true` depois de medir com falas reais (caracteres por segundo) e ouvir o resultado.
- **Vocabulário de pronúncia:** exemplos em `exemplos/`. Siglas em maiúsculas só casam em maiúsculas. Lembre que a transcrição automática não prova a pronúncia.
- **Outro motor de voz:** implemente `synth.Synth` e respeite a licença do modelo (`VOZ-02`). Os pesos nunca entram no repositório.
- **Outro agente:** adaptador fino que aponta para `skills/voice-studio/SKILL.md`; não copie o corpo da skill (`VOZ-08`).

## Licença das contribuições

Ao contribuir, você concorda que seu código é licenciado sob a [MIT](LICENSE). O modelo XTTS-v2 segue a licença própria dele (Coqui CPML) e não é distribuído aqui; veja o [`NOTICE.md`](NOTICE.md).

## Conduta e segurança

Siga o [Código de Conduta](CODE_OF_CONDUCT.md). Falhas de segurança ou de privacidade da voz: [`SECURITY.md`](SECURITY.md), sem abrir issue pública.

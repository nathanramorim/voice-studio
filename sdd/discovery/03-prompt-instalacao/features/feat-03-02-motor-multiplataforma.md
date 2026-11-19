# feat-03-02-motor-multiplataforma — Requisitos pelo motor multiplataforma (Linux, Windows e macOS)

**Pedido:** o prompt e o script da feat-03-01 são centrados no Mac (Homebrew e `curl … | sh`, que só roda em POSIX). Migrar para o motor `requisitos-para-ia` (receita declarativa por sistema), sem Homebrew como pré-requisito, com CI nos três sistemas.
**Branch:** `feat/03-prompt-instalacao` (mesmo PR #5, sem merge).

## Modelo do módulo
`enxuto`: o motor é vendorizado (cópia exata, `skills.lock` com origem, commit e sha256) e o repositório escreve só o `requisitos.toml` na raiz. Origem: `nathanramorim/requisitos-para-ia`, branch `feat/0001-motor-multiplataforma`, commit `5f63e02` (contrato `sdd/spec/contrato-requisitos.md`). Arquivos: `scripts/requisitos.py`, `scripts/bootstrap.sh`, `scripts/bootstrap.ps1`. O `requisitos.toml` parte do piloto `exemplos/voice-studio/requisitos.toml` do motor, conferido contra o código.

## Decisões do projeto aplicadas
`VOZ-10` (o prompt usa o script); `VOZ-01` e `VOZ-02` (licença CPML e declaração da voz são tipo `pessoa`: o motor só explica); Regra 7 e ADR-0003 (`uv`, nunca `pip`); `FLX-07` (README com `## Requisitos`); `TST-04` e `VOZ-09` (testes sem rede e sem instalar nada); `ARQ-04` (sem dependência nova: o motor só usa a biblioteca padrão).

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Script de requisitos | `scripts/requisitos.py` (feat-03-01) | script próprio, só macOS com brew | substituir | O motor cobre os três sistemas com receita declarativa e trava contra agir pela pessoa. |
| Receita do voice-studio | piloto do motor | 17 itens | reusar e corrigir | Base conferida; faltavam caminhos sem Homebrew e o compilador no Linux arm64 sem gerenciador conhecido. |
| Dispositivo do XTTS | `synth.py` | `TTS(...).to("cpu")` fixo | documentar | CUDA e MPS nunca são usados; a receita diz isso em vez de inventar variante de GPU. |
| Gravação de áudio | `engine/src`, `skills/`, `commands/` | nenhuma (a amostra é um arquivo) | sem item de permissão | O voice-studio não abre o microfone; o app de gravação do sistema é que pede. |
| espeak | `TTS/tts/layers/xtts`, `TTS/tts/models/xtts.py` | sem `espeak` nem `phonemizer` | sem item | O XTTS usa tokenizador próprio. |
| Caminhos | `transcribe.py`, `profile.py` | `VOICE_STUDIO_WHISPER_MODEL`, `VOICE_STUDIO_HOME`, `perfil.json` | reusar | Mesmos nomes nas checagens. |

## Dependências novas
Nenhuma (motor só com biblioteca padrão).

## Rules e IDs da Constituição Aplicáveis
`VOZ-10`, `VOZ-01`, `VOZ-02`, `VOZ-09`, `TST-04`, `FLX-07`, `ARQ-04`, `ARQ-06`, `SEG-01`.

## Escopo
- Vendorizar os três arquivos do motor (cópia exata do commit `5f63e02`), `skills.lock` com sha256, `.gitattributes` para manter os bytes no checkout do Windows; ruff ignora a cópia.
- `requisitos.toml` na raiz com `repo = "nathanramorim/voice-studio"`: uv, Python 3.11 (`--python cpython-3.11-macos-aarch64-none` no Apple Silicon, aviso de Rosetta), ffmpeg e ffprobe, whisper-cli e modelo ggml-small (`VOICE_STUDIO_WHISPER_MODEL`), libsndfile (Linux), compilador (Linux arm64 e Mac Intel), runtime do Visual C++ (Windows, PyTorch), motor com o extra xtts por sistema (CPU em todos; Windows arm64 sem PyTorch: WSL), licença CPML, amostra e consentimento, aprovação da voz, disco e memória; cada sistema com receita, sem Homebrew como único caminho.
- README: o bloco "Cole isto na sua IA" é exatamente a saída de `requisitos.py prompt`; depois dele, o caminho com clone e o caminho sem clone (URLs raw da `main`, válidas após o merge); tabela sem comandos só do Mac; versão 0.3.0 e tabela de versões.
- Skill (passo 0) e documentos que citam o script antigo passam a usar o bootstrap e o motor.
- Testes leves (`engine/tests/test_requisitos.py`): `validar`, `checar --json`, prompt igual ao README, sha256 da cópia igual ao `skills.lock`.
- CI `.github/workflows/requisitos.yml`: ubuntu, windows e macos com `validar`, `checar --json` (falha só se não sair JSON ou código >= 2), bootstrap sem uv (código 4) e `bootstrap … instalar --dry-run`, testes leves.
- Fora: tirar temas e perfis pessoais (follow-up separado); `README.antigo.md` intocado.

## Critérios de Aceitação Executáveis
1. `uv run scripts/requisitos.py validar` sai 0 e `uv run scripts/requisitos.py checar --json` gera JSON válido nesta máquina.
2. `cd engine && uv run --python cpython-3.11-macos-aarch64-none --group dev pytest -q` passa e `uv run --group dev ruff check .` sem erros.
3. `shasum -a 256 scripts/requisitos.py scripts/bootstrap.sh scripts/bootstrap.ps1` bate com o `skills.lock` e com o commit `5f63e02` do motor.
4. O bloco do README é igual à saída de `uv run scripts/requisitos.py prompt`; `grep -c 'brew install uv' README.md` = 0 e `grep -c 'install.sh | sh' README.md` = 0.
5. `uv run verificar_readme.py README.md` (readme-studio mais novo) imprime `requisitos: ok`.
6. CI `requisitos` verde em ubuntu-latest, windows-latest e macos-latest no PR #5.

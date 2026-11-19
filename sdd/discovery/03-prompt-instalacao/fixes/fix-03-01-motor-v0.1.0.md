# Fix 03-01: motor de requisitos fixado na tag v0.1.0

**Relato:** a feat-03-02 vendorizou o motor `requisitos-para-ia` do commit `5f63e02` (branch, sem tag). O motor agora tem a tag `v0.1.0` (commit `93abe08`; código aprovado `13733cf`), com validação mais estrita (contrato `sdd/spec/contrato-requisitos.md`, ADR-0008 do motor). O pin por commit de branch fica sem origem estável e sem as correções da v0.1.0.
**Branch:** `fix/03-01-motor-v0.1.0`, a partir de `origin/main` (PR para `main`, sem empilhar).

## Feature Correlacionada
- **Origem:** `features/feat-03-02-motor-multiplataforma.md` (PR #5, mesclado).
- **Causa-raiz:** o motor ainda não tinha tag quando a 03-02 foi feita; o `skills.lock` registrou `ref: feat/0001-motor-multiplataforma` e `commit: 5f63e02`, com re-pin pendente.
- **Evidência:** `skills.lock` com `"ref": "feat/0001-motor-multiplataforma"`; `git -C requisitos-para-ia rev-parse v0.1.0^{commit}` = `93abe08`; `git diff --stat 5f63e02 v0.1.0 -- scripts` muda `requisitos.py` (177 linhas) e `bootstrap.ps1` (10 linhas).

## Modelo do módulo
`enxuto`: troca de cópia vendorizada. Os três arquivos viram cópia exata dos blobs da tag (`git show v0.1.0:<arquivo>`), o lock ganha `ref`, `commit` e sha256 novos. Nenhum código próprio muda.

## Decisões do projeto aplicadas
`ARQ-04` (sem dependência nova); `VOZ-10` (o prompt continua sendo a saída do motor); `TST-04` (testes sem rede); Regra 7 e ADR-0003 (`uv`).

## O que já existe
| Procurei | Onde | Achei | Decisão | Justificativa |
|---|---|---|---|---|
| Motor vendorizado | `scripts/requisitos.py`, `bootstrap.sh`, `bootstrap.ps1` | cópia do `5f63e02` | substituir | Cópia exata da `v0.1.0`; `bootstrap.sh` é idêntico. |
| Origem e checksum | `skills.lock` | ref de branch e commit `5f63e02` | estender | `ref: v0.1.0`, `commit: 93abe08`, sha256 novos. |
| Receita | `requisitos.toml` | 16 itens | reusar | Passa no `validar` da v0.1.0 sem mudança (nenhum código inline, `{env:}` só em `checar`, nenhum aceite pela pessoa). |
| Bloco do README | `requisitos.py prompt` | bloco da feat-03-02 | reusar | A saída da v0.1.0 é byte a byte igual à do `5f63e02`. |
| Teste do lock | `engine/tests/test_requisitos.py` | confere `commit` `5f63e02` | estender | Passa a conferir `ref` `v0.1.0` e `commit` `93abe08`. |

## Dependências novas
Nenhuma.

## Rules e IDs da Constituição Aplicáveis
`ARQ-04`, `ARQ-06`, `VOZ-10`, `TST-04`, `FLX-07`, `SEG-01`.

## Escopo
- Os três arquivos do motor = blobs da tag `v0.1.0`; `skills.lock` atualizado.
- Cabeçalho do `requisitos.toml`, teste do lock, versão 0.3.1 (plugin, `engine/pyproject.toml`, `__init__.py`, `uv.lock`), linha da 0.3.1 no README e em `sdd/releases/history.md`.
- Fora do escopo: `README.antigo.md` (arquivo do usuário, não versionado).

## Critérios de Aceitação Executáveis
1. Para cada arquivo do motor, `git hash-object scripts/<f>` = `git -C ../requisitos-para-ia rev-parse v0.1.0:scripts/<f>`, e o sha256 bate com o `skills.lock`.
2. `uv run scripts/requisitos.py validar` sai 0 com `macos, linux, windows cobertos`.
3. `uv run scripts/requisitos.py checar --json` sai 0 ou 1 com JSON válido; `uv run scripts/requisitos.py prompt` está literal no README.
4. `cd engine && uv run --python 3.11 --group dev pytest -q tests/test_requisitos.py` passa.
5. CI `requisitos` verde em ubuntu, windows e macos.
6. `git grep -n 5f63e02` só acha histórico (specs, pareceres, status e notas de versão anteriores).

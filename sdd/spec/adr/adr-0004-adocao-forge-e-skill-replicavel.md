# ADR-0004: Forge SDD 4.9.1-beta, fluxo obrigatório e skill replicável

- **Data:** 2026-11-19
- **Status:** `aprovado`
- **Regras afetadas (IDs da constitution):** `FLX-01`, `FLX-02`, `FLX-07`, `ARQ-03`, `GOV-01`, `GOV-02`; Regras 1, 2, 3, 7, 12, 13, 14 e 15
- **Autor / Responsável:** dono do repositório

## Contexto

As skills do autor são produtos de TI e seguem o processo de desenvolvimento Forge SDD: cada skill é um repositório próprio e replicável, com estrutura Forge, `/constitution` alinhada e README pelo readme-studio com `## Requisitos`. O voice-studio já tinha o Forge 4.8.0, mas as regras eram as genéricas do template (1, 2 e 15 repetiam a política de branch) e não diziam que toda feature ou fix passa pelo fluxo, que a skill é replicável nem que o Python é só via `uv`.

## Opções Consideradas

1. **Manter as regras genéricas:** nada obriga o fluxo nem a replicabilidade.
2. **Alinhar a Constituição ao padrão das skills:** consolidar as regras de branch numa só e usar as vagas para fluxo, replicabilidade, `uv`, README e segurança da voz.

## Decisão

Opção 2. Regras alteradas: 1 (branch, consolida as antigas 1, 2 e 15), 2 (toda feature ou fix por `/discovery`, `/nova-feature` ou `/novo-fix`), 3 (replicável, sem nome real), 7 (`uv` sempre), 12 (README com `## Requisitos`), 13 (fixes em `fixes/`), 14 (telemetria fora do git) e 15 (segurança da voz, remete a `VOZ-01..04`). Atualização da estrutura para o Forge 4.9.1-beta.

A Regra 11 (`FLX-07`) proíbe mesclar versão `-beta` na `main`. O Forge instalado é `4.9.1-beta`; a exceção temporária fica registrada (`GOV-02`) em `sdd/discovery/02-adocao-forge/discovery.md` e no PR.

## Consequências

- **Positivas:** histórico e contexto sequencial de toda mudança; skill instalável por qualquer pessoa.
- **Negativas / Trade-offs:** o PR de adoção depende da exceção até o Forge sair da beta.
- **Ações de acompanhamento:** resolver as divergências da Regra 3 (nomes reais em exemplos e testes) por `/novo-fix`.

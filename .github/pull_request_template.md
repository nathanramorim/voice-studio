## Spec / Tarefa (`FLX-01`, `FLX-03`)

- **Feature / Task:** `sdd/discovery/<id>-<nome>/features/feat-XX-...md`
- **Discovery / Criteria (se aplicável):** `sdd/discovery/<id>-<nome>/criteria.md`
- **ADR relacionada (se alterar arquitetura ou a Constitution, `FLX-05`, `GOV-01`):** `N/A`

## O que muda

- [Resumo objetivo das alterações entregues neste Pull Request]

## Impacto

- **Módulos afetados:** [Ex.: `profile`, `synth`, `cli`]
- **Compatibilidade / breaking changes:** [Comandos, opções ou formato de perfil que mudam]
- **Dependências novas (`SEG-07`, `ARQ-04`):** `Nenhuma` (ou pacote, versão e justificativa)
- **Voz e privacidade:** [`Nenhum impacto` ou descreva: onde passa a ficar amostra, áudio ou perfil]

## Como testar (`TST-01`, `TST-05`)

```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.cache/voice-studio-venv
cd engine
uv run --python 3.11 --group dev pytest -q
uv run --python 3.11 --group dev ruff check .
forge gate --dir . --branch <branch> --spec <spec> --mode bloqueio
```

Teste manual (se houver, ouvindo o resultado): [passos e o que foi verificado]

## Rollback

- [Como desfazer: reverter o commit, restaurar o formato anterior do perfil, etc.]

## Checklist da constitution

- [ ] Não commitei em `main`; a branch é `feat/<id>-<nome>` (`FLX-02`).
- [ ] Spec e critérios executáveis existem e passam (`FLX-01`, `TST-01`).
- [ ] Nenhuma amostra, áudio, vídeo ou perfil de voz foi adicionado (`VOZ-04`); testes usam áudio sintético.
- [ ] O consentimento e o aceite da licença continuam sendo do usuário; nada os preenche sozinho (`VOZ-01`, `VOZ-02`).
- [ ] Nada sai da máquina: sem chamada de rede nem serviço de voz na nuvem (`VOZ-03`).
- [ ] O motor entra por injeção e os testes não baixam modelo (`VOZ-09`, `TST-04`).
- [ ] Processos externos com lista de argumentos, sem shell (`SEG-03`); entradas validadas na borda (`SEG-01`).
- [ ] Reusei o que existe e atualizei `sdd/spec/concepts.md` se criei um conceito (`DUP-01`, `DUP-03`).
- [ ] Documentação e notas de versão atualizadas (`sdd/releases/history.md`).

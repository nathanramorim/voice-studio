# Catálogo de Conceitos e Contratos (`DUP-01`) — voice-studio

Regra `DUP-01`: **Um conceito = uma casa.** Antes de criar uma nova entidade, módulo ou utilitário, consulte esta tabela (`DUP-02`).

| Conceito | Pacote/Domínio Dono | Entidade Mestra | Contrato Público | Observação |
| --- | --- | --- | --- | --- |
| Consentimento e licença | `consent` | — | `require_consent`, `require_license` | Nenhum outro módulo decide consentimento |
| Vocabulário de pronúncia | `vocab` | `dict[str, str]` | `load`, `apply_spoken` | Só altera o texto da voz |
| Duração esperada e escolha de variação | `guard` | `Take` | `expected_seconds`, `is_suspect`, `pick` | Constantes de caracteres por segundo vivem aqui |
| Motor de voz | `synth` | `Synth` | `speak`, `xtts_synth` | Motor injetável (`VOZ-09`) |
| Segmento de dublagem | `dub` | `Segment` | `load_segments`, `dub` | |
| Processos externos (ffmpeg, whisper) | `audio`, `transcribe` | — | `run` | Sempre lista de argumentos (`SEG-03`) |

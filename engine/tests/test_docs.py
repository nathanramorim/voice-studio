"""Documentação operacional: skill, adaptadores e plugin coerentes com a CLI."""

import json
from pathlib import Path

from voice_studio import cli

RAIZ = Path(__file__).resolve().parents[2]
SKILL = RAIZ / "skills" / "voice-studio" / "SKILL.md"
CITA_SKILL = "skills/voice-studio/SKILL.md"


def comandos_da_cli() -> set[str]:
    names = {c.name or c.callback.__name__ for c in cli.app.registered_commands}
    names |= {g.name for g in cli.app.registered_groups}
    return names


def test_comandos_todo_comando_da_cli_esta_na_skill():
    esperados = {"perfil", "falar", "traduzir", "sample", "speak", "transcribe", "dub"}
    assert esperados <= comandos_da_cli()
    texto = SKILL.read_text(encoding="utf-8")
    faltando = [c for c in sorted(comandos_da_cli()) if f"voice-studio {c}" not in texto]
    assert faltando == []


def test_adaptadores_citam_a_skill_sem_copiar_o_corpo():
    corpo = [linha.strip() for linha in SKILL.read_text(encoding="utf-8").splitlines()]
    for nome in ("AGENTS.md", "GEMINI.md", "CLAUDE.md"):
        texto = (RAIZ / nome).read_text(encoding="utf-8")
        assert CITA_SKILL in texto, nome
        linhas = [linha.strip() for linha in texto.splitlines()]
        for i in range(len(linhas) - 5):
            janela = linhas[i:i + 6]
            if not any(janela):
                continue
            achou = any(corpo[j:j + 6] == janela for j in range(len(corpo) - 5))
            assert not achou, f"{nome}: trecho de 6 linhas copiado do SKILL.md"


def test_plugin_manifestos_validos_e_comandos_com_description():
    for arq in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        assert isinstance(json.loads((RAIZ / arq).read_text(encoding="utf-8")), dict)
    arquivos = sorted((RAIZ / "commands").glob("*.md"))
    nomes = {a.stem for a in arquivos}
    assert {"perfil-de-voz", "falar", "traduzir", "clonar-voz", "dublar"} <= nomes
    for arq in arquivos:
        texto = arq.read_text(encoding="utf-8")
        assert texto.startswith("---\n"), arq.name
        front = texto.split("---\n")[1]
        assert any(f.startswith("description:") and f[len("description:"):].strip()
                   for f in front.splitlines()), arq.name

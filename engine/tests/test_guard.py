from pathlib import Path

from voice_studio import guard


def test_duracao_esperada_pt_en():
    assert round(guard.expected_seconds("a" * 60, "pt"), 1) == 4.0
    assert guard.expected_seconds("a" * 125, "en") == 10.0


def test_alucinacao_e_suspeita():
    text = "Chegou o Forge SDD quatro ponto oito."  # 37 caracteres, ~2,5 s
    assert guard.is_suspect(10.4, text, "pt")
    assert not guard.is_suspect(2.7, text, "pt")


def test_pick_escolhe_a_mais_proxima_e_ignora_suspeitas():
    text = "a" * 60  # esperado 4,0 s
    takes = [guard.Take(Path("a"), 10.0), guard.Take(Path("b"), 4.6), guard.Take(Path("c"), 3.9)]
    best, ok = guard.pick(takes, text, "pt")
    assert best.path == Path("c") and ok


def test_pick_sinaliza_quando_todas_sao_suspeitas():
    takes = [guard.Take(Path("a"), 12.0), guard.Take(Path("b"), 9.0)]
    best, ok = guard.pick(takes, "a" * 60, "pt")
    assert best.path == Path("b") and not ok

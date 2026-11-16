import json

import pytest

from voice_studio import vocab
from voice_studio.errors import VoiceError

MAP = {"IA": "IÁ", "PR": "PIER", "Gemini": "Geminai", "Forge SDD": "Forge S D D"}


def test_troca_palavra_inteira():
    assert vocab.apply_spoken("O PR da IA", MAP) == "O PIER da IÁ"
    assert vocab.apply_spoken("PRONTO e IAGO", MAP) == "PRONTO e IAGO"


def test_sigla_so_em_maiuscula():
    assert vocab.apply_spoken("ele ia embora", MAP) == "ele ia embora"


def test_palavra_comum_ignora_maiuscula_e_frase():
    assert vocab.apply_spoken("gemini e GEMINI", MAP) == "Geminai e Geminai"
    assert vocab.apply_spoken("Meet Forge SDD.", MAP) == "Meet Forge S D D."


def test_sem_vocabulario_nao_muda():
    assert vocab.apply_spoken("O PR", {}) == "O PR"


def test_arquivo_valido_e_invalido(tmp_path):
    good = tmp_path / "p.json"
    good.write_text(json.dumps({"IA": "IÁ"}), encoding="utf-8")
    assert vocab.load(good) == {"IA": "IÁ"}
    for bad in ("[]", '{"": "x"}', '{"a": 1}', "{nao json"):
        path = tmp_path / "b.json"
        path.write_text(bad, encoding="utf-8")
        with pytest.raises(VoiceError):
            vocab.load(path)
    with pytest.raises(VoiceError):
        vocab.load(tmp_path / "nao-existe.json")

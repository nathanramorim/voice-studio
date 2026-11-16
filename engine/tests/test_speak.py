import pytest
from conftest import write_wav

from voice_studio import audio, synth
from voice_studio.errors import VoiceError


def fake(durations, seen):
    """Sintetizador simulado: grava o texto recebido e devolve áudios das durações dadas."""
    it = iter(durations)

    def run(text, ref, lang, out, temperature):
        seen.append((text, temperature))
        write_wav(out, next(it))

    return run


def test_vocabulario_vai_so_para_a_voz_e_a_melhor_variacao_vence(tmp_path, ref):
    text = "O PR da IA é bom"  # após troca: "O PIER da IÁ é bom" (18 caracteres, ~1,2 s)
    seen = []
    out = synth.speak([text], ref, "pt", tmp_path, fake([4.0, 1.2, 1.4], seen),
                      {"PR": "PIER", "IA": "IÁ"}, takes=3)
    assert [s[0] for s in seen] == ["O PIER da IÁ é bom"] * 3
    assert len({s[1] for s in seen}) == 3  # temperaturas diferentes por variação
    line = out[0]
    assert line.text == text and line.spoken == "O PIER da IÁ é bom"
    assert line.ok and abs(line.seconds - 1.2) < 0.05
    assert not list(tmp_path.glob(".take-*"))  # variações descartadas


def test_todas_suspeitas_marca_ok_falso(tmp_path, ref):
    out = synth.speak(["Oi"], ref, "pt", tmp_path, fake([9.0, 8.0], []), takes=2)
    assert not out[0].ok


def test_entradas_invalidas(tmp_path, ref):
    with pytest.raises(VoiceError, match="Idioma"):
        synth.speak(["a"], ref, "xx", tmp_path, fake([1], []))
    with pytest.raises(VoiceError, match="vazia"):
        synth.speak([" "], ref, "pt", tmp_path, fake([1], []))
    with pytest.raises(VoiceError, match="takes"):
        synth.speak(["a"], ref, "pt", tmp_path, fake([1], []), takes=0)


def test_fit_factor():
    assert audio.fit_factor(2.0, 3.0) == 1.0
    assert audio.fit_factor(3.3, 3.0) == pytest.approx(1.1)
    assert audio.fit_factor(6.0, 3.0) == 1.25
    with pytest.raises(ValueError):
        audio.fit_factor(1.0, 0)

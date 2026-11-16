import pytest

from voice_studio import guard, languages, synth
from voice_studio.errors import VoiceError


def test_catalogo_tem_seis_idiomas_e_estado_de_validacao():
    assert set(languages.CATALOG) == {"pt", "en", "es", "fr", "de", "it"}
    assert languages.CATALOG["pt"].cps == 15.0 and languages.CATALOG["en"].cps == 12.5
    for code in ("pt", "en"):
        assert languages.CATALOG[code].validated is True and languages.is_validated(code)
    for code in ("es", "fr", "de", "it"):
        assert languages.CATALOG[code].validated is False and not languages.is_validated(code)


def test_require_idioma_invalido_lista_os_aceitos():
    assert languages.require("pt").nome == "português"
    with pytest.raises(VoiceError) as err:
        languages.require("xx")
    for code in languages.CATALOG:
        assert code in str(err.value)


def test_catalogo_e_a_unica_fonte_de_cps():
    assert not hasattr(guard, "CPS") and not hasattr(synth, "LANGS")
    assert guard.expected_seconds("a" * 60, "es") == 60 / languages.CATALOG["es"].cps
    with pytest.raises(VoiceError):
        guard.expected_seconds("oi", "xx")

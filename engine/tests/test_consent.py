import pytest

from voice_studio import consent
from voice_studio.errors import VoiceError


def test_sem_referencia_ou_sem_confirmacao(tmp_path, ref):
    with pytest.raises(VoiceError, match="--ref"):
        consent.require_consent(True, None)
    with pytest.raises(VoiceError, match="--ref"):
        consent.require_consent(True, tmp_path / "nao-existe.wav")
    with pytest.raises(VoiceError, match="--confirm-own-voice"):
        consent.require_consent(False, ref)
    assert consent.require_consent(True, ref) == ref


def test_licenca_so_com_aceite_explicito():
    with pytest.raises(VoiceError, match="CPML"):
        consent.require_license(False, env={})
    consent.require_license(True, env={})
    consent.require_license(False, env={consent.LICENSE_ENV: "1"})

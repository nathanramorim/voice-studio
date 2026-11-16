import json
import shutil

import pytest
from conftest import write_wav

from voice_studio import profile
from voice_studio.errors import VoiceError


def fake_extract(origem, destino, start, duration):
    """Cópia no lugar do ffmpeg: o teste de perfil não depende de ferramenta externa."""
    shutil.copyfile(origem, destino)


def make(nome, base, ref, confirm=True):
    return profile.create(nome, ref, confirm, base, extract=fake_extract)


def test_criar_perfil(tmp_path, ref):
    base = tmp_path / "perfis"
    data = make("nathan", base, ref)
    assert (base / "nathan" / "voz-ref.wav").is_file()
    saved = json.loads((base / "nathan" / "perfil.json").read_text(encoding="utf-8"))
    assert saved["consentimento"]["confirmado_pelo_usuario"] is True
    assert saved["consentimento"]["em"].startswith("20") and saved["criado_em"] == data["criado_em"]
    assert saved["amostra"] == "voz-ref.wav" and saved["vocabularios"] == {}
    assert saved["ajustes"] == {"velocidade": 1.08, "takes": 3}
    assert profile.load("nathan", base)["nome"] == "nathan"


def test_criar_sem_confirmar_falha(tmp_path, ref):
    with pytest.raises(VoiceError, match="confirm-own-voice"):
        make("nathan", tmp_path / "perfis", ref, confirm=False)
    assert not (tmp_path / "perfis" / "nathan").exists()


def test_criar_com_ffmpeg_real(tmp_path):
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg ausente")
    src = write_wav(tmp_path / "src.wav", 7.0)
    profile.create("real", src, True, tmp_path / "perfis")
    assert (tmp_path / "perfis" / "real" / "voz-ref.wav").is_file()


@pytest.mark.parametrize("nome", ["..", "a/b", "", "a\x00b", "a\nb", "A", "-x", "x" * 41, ".oculto"])
def test_seguranca_nomes_rejeitados(tmp_path, ref, nome):
    with pytest.raises(VoiceError, match="Nome de perfil"):
        make(nome, tmp_path / "perfis", ref)
    assert not (tmp_path / "perfis").exists()


def test_seguranca_nao_sobrescreve(tmp_path, ref):
    base = tmp_path / "perfis"
    make("nathan", base, ref)
    before = (base / "nathan" / "perfil.json").read_text(encoding="utf-8")
    with pytest.raises(VoiceError, match="já existe"):
        make("nathan", base, ref)
    assert (base / "nathan" / "perfil.json").read_text(encoding="utf-8") == before


def test_seguranca_inexistente_e_corrompido(tmp_path, ref):
    base = tmp_path / "perfis"
    with pytest.raises(VoiceError, match="não encontrado"):
        profile.load("ninguem", base)
    make("nathan", base, ref)
    (base / "nathan" / "perfil.json").write_text("{quebrado", encoding="utf-8")
    with pytest.raises(VoiceError, match="corrompido"):
        profile.load("nathan", base)


def test_seguranca_base_dentro_de_repositorio_git(tmp_path, ref):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    with pytest.raises(VoiceError, match="repositório git"):
        make("nathan", repo / "perfis", ref)
    with pytest.raises(VoiceError, match="repositório git"):
        profile.list_profiles(repo / "perfis")


def test_seguranca_falha_na_amostra_nao_deixa_perfil_pela_metade(tmp_path, ref):
    def boom(*_):
        raise VoiceError("ffmpeg falhou")

    with pytest.raises(VoiceError, match="ffmpeg"):
        profile.create("nathan", ref, True, tmp_path / "perfis", extract=boom)
    assert not (tmp_path / "perfis" / "nathan").exists()


def test_base_pelo_ambiente(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_STUDIO_HOME", str(tmp_path / "casa"))
    assert profile.default_base() == tmp_path / "casa"


def test_listar_em_ordem_e_ignora_pastas_sem_perfil(tmp_path, ref):
    base = tmp_path / "perfis"
    assert profile.list_profiles(base) == []
    make("zeta", base, ref)
    make("alfa", base, ref)
    (base / "lixo").mkdir()
    assert profile.list_profiles(base) == ["alfa", "zeta"]


def test_seguranca_symlink_pendente_vira_erro_claro(tmp_path, ref):
    base = tmp_path / "perfis"
    base.mkdir()
    (base / "nathan").symlink_to(tmp_path / "nao-existe")
    with pytest.raises(VoiceError, match="link quebrado"):
        make("nathan", base, ref)


def write_vocab(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_vocabulario_registra_e_le_por_idioma(tmp_path, ref):
    base = tmp_path / "perfis"
    make("nathan", base, ref)
    profile.set_vocabulary("nathan", "pt", write_vocab(tmp_path / "pt.json", {"IA": "IÁ"}), base)
    perfil = profile.set_vocabulary(
        "nathan", "en", write_vocab(tmp_path / "en.json", {"PR": "pee are"}), base)
    assert perfil["vocabularios"] == {"pt": "vocab.pt.json", "en": "vocab.en.json"}
    assert (base / "nathan" / "vocab.pt.json").is_file()
    assert profile.vocabulary(profile.load("nathan", base), "pt") == {"IA": "IÁ"}
    assert profile.vocabulary(profile.load("nathan", base), "en") == {"PR": "pee are"}
    assert profile.vocabulary(profile.load("nathan", base), "es") == {}


def test_vocabulario_invalido_nao_altera_o_perfil(tmp_path, ref):
    base = tmp_path / "perfis"
    make("nathan", base, ref)
    before = (base / "nathan" / "perfil.json").read_text(encoding="utf-8")
    big = {f"t{i}": "x" for i in range(2001)}
    for bad in ({}, {"a": ""}, {"a": 3}, big, [1]):
        with pytest.raises(VoiceError):
            profile.set_vocabulary("nathan", "pt", write_vocab(tmp_path / "v.json", bad), base)
    with pytest.raises(VoiceError, match="não suportado"):
        profile.set_vocabulary("nathan", "xx", write_vocab(tmp_path / "v.json", {"a": "b"}), base)
    assert (base / "nathan" / "perfil.json").read_text(encoding="utf-8") == before
    assert sorted(p.name for p in (base / "nathan").iterdir()) == ["perfil.json", "voz-ref.wav"]

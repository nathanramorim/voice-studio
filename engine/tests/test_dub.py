import json

import pytest
from conftest import write_wav

from voice_studio import audio, dub
from voice_studio.errors import VoiceError


def seg_file(tmp_path, items):
    path = tmp_path / "s.json"
    path.write_text(json.dumps(items), encoding="utf-8")
    return path


def test_segmentos_validos_e_invalidos(tmp_path):
    ok = seg_file(tmp_path, [{"start": 0, "end": 2, "text": "Hi"},
                             {"start": 2.5, "end": 4, "text": "There"}])
    assert [s.text for s in dub.load_segments(ok)] == ["Hi", "There"]
    for bad in ([], [{"start": 0, "end": 2}], [{"start": 2, "end": 1, "text": "x"}],
                [{"start": 0, "end": 2, "text": ""}],
                [{"start": 0, "end": 3, "text": "a"}, {"start": 2, "end": 4, "text": "b"}]):
        with pytest.raises(VoiceError):
            dub.load_segments(seg_file(tmp_path, bad))


def test_dub_acelera_no_limite_e_aponta_estouro(tmp_path, ref, monkeypatch):
    calls = {}
    monkeypatch.setattr(audio, "speed_up", lambda s, d, f: (write_wav(d, 1.0),
                                                            calls.setdefault("f", []).append(f)))
    monkeypatch.setattr(audio, "mix_dub", lambda v, parts, out, keep: calls.update(
        parts=[(p.name, st) for p, st in parts]))

    def synth(text, r, lang, out, t):
        write_wav(out, 3.0 if text == "long" else 1.0)  # "long": 3 s num espaço de 1 s

    segs = [dub.Segment(0.0, 1.0, "long"), dub.Segment(1.2, 3.2, "short ok text")]
    report = dub.dub(tmp_path / "v.mp4", segs, ref, "en", tmp_path / "o.mp4", synth,
                     tmp_path / "w", takes=1)
    assert calls["f"] == [1.25]  # só o segmento 1 foi acelerado, no limite
    assert report["overflow"] == [1]
    assert [s for _, s in calls["parts"]] == [0.0, 1.2]

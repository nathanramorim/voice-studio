"""CLI na borda: valida a entrada e delega ao domínio."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from . import audio, consent, vocab
from . import dub as dub_mod
from . import profile as profile_mod
from . import synth as synth_mod
from . import transcribe as transcribe_mod
from .errors import VoiceError

app = typer.Typer(add_completion=False, no_args_is_help=True,
                  help="Voz clonada local: narração e dublagem português -> inglês.")

REF = Annotated[Path, typer.Option("--ref", help="Áudio de referência (6 a 30 s da voz).")]
OWN = Annotated[bool, typer.Option("--confirm-own-voice",
                                   help="Confirmo que a voz da amostra é minha ou autorizada.")]
CPML = Annotated[bool, typer.Option("--accept-cpml",
                                    help="Aceito a licença Coqui CPML do modelo XTTS-v2.")]
PERFIS_DIR = Annotated[Path | None, typer.Option(
    "--perfis-dir", help="Pasta dos perfis (padrão: VOICE_STUDIO_HOME ou ~/.voice-studio/perfis).")]
VOCAB = Annotated[Path | None, typer.Option("--vocab", help="pronuncia.json (opcional).")]


perfil_app = typer.Typer(no_args_is_help=True, help="Perfis de voz (amostra + consentimento).")
app.add_typer(perfil_app, name="perfil")


def _fail(exc: VoiceError) -> None:
    typer.secho(f"Erro: {exc}", fg=typer.colors.RED, err=True)
    raise typer.Exit(1)


@app.command()
def sample(video: Path, out: Annotated[Path, typer.Option("--out", "-o")] = Path("voice-ref.wav"),
           start: float = 0.0, duration: float = 28.0) -> None:
    """Extrai e limpa uma amostra de referência de um vídeo ou áudio."""
    try:
        audio.extract_sample(video, out, start, duration)
    except VoiceError as exc:
        _fail(exc)
    typer.echo(f"Amostra salva em {out}. Ouça antes de usar: fala contínua, sem outras vozes.")


@app.command()
def transcribe(video: Path, out: Annotated[Path, typer.Option("--out", "-o")] = Path("segments.json"),
               lang: str = "pt", model: Annotated[Path | None, typer.Option("--model")] = None) -> None:
    """Transcreve com whisper.cpp local e grava os segmentos para traduzir."""
    try:
        segments = transcribe_mod.transcribe(video, model, lang)
    except VoiceError as exc:
        _fail(exc)
    out.write_text(json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(f"{len(segments)} segmentos em {out}. Traduza `source` para o campo `text`.")


@app.command()
def speak(lines: Path, ref: REF, confirm_own_voice: OWN = False, accept_cpml: CPML = False,
          lang: str = "pt", out: Annotated[Path, typer.Option("--out", "-o")] = Path("out"),
          takes: int = 3, vocab_file: VOCAB = None) -> None:
    """Gera uma fala por linha com a voz clonada (lista JSON de textos)."""
    try:
        consent.require_consent(confirm_own_voice, ref)
        consent.require_license(accept_cpml)
        raw = json.loads(lines.read_text(encoding="utf-8"))
        texts = raw["lines"] if isinstance(raw, dict) else raw
        if not isinstance(texts, list) or not all(isinstance(t, str) for t in texts):
            raise VoiceError("O arquivo deve ser uma lista de textos ou {\"lines\": [...]}.")
        mapping = vocab.load(vocab_file) if vocab_file else {}
        result = synth_mod.speak(texts, ref, lang, out, synth_mod.xtts_synth(), mapping, takes)
    except VoiceError as exc:
        _fail(exc)
    report = [{"line": r.index, "seconds": r.seconds, "ok": r.ok, "spoken": r.spoken,
               "file": r.path.name} for r in result]
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    bad = [r["line"] for r in report if not r["ok"]]
    typer.echo(f"{len(report)} falas em {out}/." + (f" Confira as linhas {bad}." if bad else ""))


@app.command()
def dub(video: Path, segments: Path, ref: REF, confirm_own_voice: OWN = False,
        accept_cpml: CPML = False, lang: str = "en",
        out: Annotated[Path, typer.Option("--out", "-o")] = Path("dublado.mp4"),
        takes: int = 3, vocab_file: VOCAB = None, keep_original: float = 0.0) -> None:
    """Dubla o vídeo: segmentos com `start`, `end` e `text` já traduzido."""
    try:
        consent.require_consent(confirm_own_voice, ref)
        consent.require_license(accept_cpml)
        segs = dub_mod.load_segments(segments)
        mapping = vocab.load(vocab_file) if vocab_file else {}
        report = dub_mod.dub(video, segs, ref, lang, out, synth_mod.xtts_synth(speed=1.0),
                             out.parent / f".{out.stem}-work", mapping, takes, keep_original)
    except VoiceError as exc:
        _fail(exc)
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
    if report["overflow"]:
        typer.secho(f"Atenção: segmentos {report['overflow']} ficaram maiores que o tempo "
                    "disponível; encurte o texto traduzido.", fg=typer.colors.YELLOW)


@perfil_app.command("criar")
def perfil_criar(nome: str, origem: Path, confirm_own_voice: OWN = False,
                 start: float = 0.0, duration: float = 28.0,
                 perfis_dir: PERFIS_DIR = None) -> None:
    """Cria um perfil a partir de um áudio ou vídeo da voz (exige consentimento)."""
    try:
        profile_mod.create(nome, origem, confirm_own_voice, perfis_dir, start, duration)
    except VoiceError as exc:
        _fail(exc)
    typer.echo(f"Perfil '{nome}' criado. Ouça {profile_mod.SAMPLE_FILE} antes de usar.")


@perfil_app.command("listar")
def perfil_listar(perfis_dir: PERFIS_DIR = None) -> None:
    """Lista os perfis existentes."""
    try:
        names = profile_mod.list_profiles(perfis_dir)
    except VoiceError as exc:
        _fail(exc)
    typer.echo("\n".join(names) if names else "Nenhum perfil.")


@perfil_app.command("mostrar")
def perfil_mostrar(nome: str, perfis_dir: PERFIS_DIR = None) -> None:
    """Mostra os dados do perfil (sem o caminho da amostra, só o nome do arquivo)."""
    try:
        data = profile_mod.load(nome, perfis_dir)
    except VoiceError as exc:
        _fail(exc)
    data.pop("amostra_path", None)
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


@perfil_app.command("vocab")
def perfil_vocab(nome: str, arquivo: Path,
                 lang: Annotated[str, typer.Option("--lang", help="Idioma do vocabulário.")] = "pt",
                 perfis_dir: PERFIS_DIR = None) -> None:
    """Associa um vocabulário de pronúncia (JSON) a um idioma do perfil."""
    try:
        profile_mod.set_vocabulary(nome, lang, arquivo, perfis_dir)
    except VoiceError as exc:
        _fail(exc)
    typer.echo(f"Vocabulário '{lang}' registrado no perfil '{nome}'.")


def main() -> None:
    app()

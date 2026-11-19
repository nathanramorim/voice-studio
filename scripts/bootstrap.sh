#!/bin/sh
# bootstrap.sh — macOS e Linux: confere o uv; sem ele, mostra e (com o seu ok ou --sim) roda o instalador
# OFICIAL do uv; depois roda `uv run requisitos.py checar` (ou os argumentos que você passar).
# Nunca exige Homebrew, nunca usa sudo, nunca aceita licença por você. Contrato: sdd/spec/contrato-requisitos.md.
# Uso: sh scripts/bootstrap.sh [--sim] [argumentos do requisitos.py]
# Códigos: os do requisitos.py; 4 = falta o uv e não houve ok; 5 = a instalação do uv falhou.
set -u

URL_UV="https://astral.sh/uv/install.sh"
AQUI=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SIM=0
if [ "${1:-}" = "--sim" ]; then SIM=1; shift; fi
[ "$#" -eq 0 ] && set -- checar

achar_uv() {
  command -v uv 2>/dev/null && return 0
  for d in "${XDG_BIN_HOME:-}" "$HOME/.local/bin" "$HOME/.cargo/bin"; do
    [ -n "$d" ] && [ -x "$d/uv" ] && { PATH="$d:$PATH"; export PATH; echo "$d/uv"; return 0; }
  done
  return 1
}

baixar() {
  if command -v curl >/dev/null 2>&1; then curl -LsSf "$1" -o "$2"
  elif command -v wget >/dev/null 2>&1; then wget -q "$1" -O "$2"
  else echo "Não achei curl nem wget: instale um deles pelo gerenciador do seu sistema." >&2; return 1
  fi
}

if ! achar_uv >/dev/null; then
  echo "O uv não está instalado. Ele roda o requisitos.py e gerencia o Python (sem pip)."
  echo "Instalador oficial: $URL_UV (instala em ~/.local/bin, sem sudo, e põe essa pasta no seu perfil do shell)."
  if [ "$SIM" -ne 1 ]; then
    if [ -t 0 ]; then
      printf "Baixar e rodar o instalador oficial agora? [s/N] "
      read -r resp
      case "$resp" in s|S|sim|y|Y) SIM=1 ;; esac
    fi
  fi
  if [ "$SIM" -ne 1 ]; then
    echo "Nada foi instalado. Com o seu ok, rode: sh $0 --sim"
    exit 4
  fi
  tmp=$(mktemp "${TMPDIR:-/tmp}/uv-install.XXXXXX") || exit 5
  baixar "$URL_UV" "$tmp" || { rm -f "$tmp"; echo "O download do instalador falhou." >&2; exit 5; }
  sh "$tmp"; codigo=$?
  rm -f "$tmp"
  [ "$codigo" -eq 0 ] || { echo "O instalador do uv falhou." >&2; exit 5; }
  achar_uv >/dev/null || { echo "O uv foi instalado, mas não está no PATH: abra outro terminal." >&2; exit 5; }
  echo "uv instalado e já no PATH desta sessão."
fi

exec uv run "$AQUI/requisitos.py" "$@"

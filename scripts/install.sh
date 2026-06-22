#!/usr/bin/env bash
set -euo pipefail

PACKAGE="qcp-cli"
BIN_NAME="qcp"

color() { printf "\033[%sm%s\033[0m\n" "$1" "$2"; }
info() { color "34" "$1"; }
ok() { color "32" "$1"; }
err() { color "31" "$1" >&2; }

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi

  info "uv not found. Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh

  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

  if ! command -v uv >/dev/null 2>&1; then
    err "uv installed, but not found on PATH."
    err "Restart your shell or add this to your profile:"
    err 'export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"'
    exit 1
  fi
}

main() {
  ensure_uv

  info "Installing ${PACKAGE}..."
  uv tool install "${PACKAGE}" --upgrade

  if ! command -v "${BIN_NAME}" >/dev/null 2>&1; then
    info "qcp installed, but not found on PATH."
    info "Add this to your shell profile:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
  fi

  ok "qcp installed successfully."
  "${BIN_NAME}" --version || true
}

main "$@"
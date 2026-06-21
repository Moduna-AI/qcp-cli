#!/usr/bin/env bash
# Installer for qcp (Query Companion).
# Usage: curl -fsSL https://raw.githubusercontent.com/your-org/qcp/main/scripts/install.sh | bash
set -euo pipefail

REPO="your-org/qcp"
INSTALL_DIR="${QCP_INSTALL_DIR:-$HOME/.local/bin}"
BIN_NAME="qcp"

color() { printf "\033[%sm%s\033[0m\n" "$1" "$2"; }
info() { color "34" "$1"; }
ok() { color "32" "$1"; }
err() { color "31" "$1" >&2; }

detect_platform() {
  local os arch
  os="$(uname -s)"
  arch="$(uname -m)"
  case "$os" in
    Linux*) os="linux" ;;
    Darwin*) os="macos" ;;
    *) err "Unsupported OS: $os"; exit 1 ;;
  esac
  case "$arch" in
    x86_64|amd64) arch="x86_64" ;;
    arm64|aarch64) arch="arm64" ;;
    *) err "Unsupported architecture: $arch"; exit 1 ;;
  esac
  echo "${os}-${arch}"
}

main() {
  if ! command -v python3 >/dev/null 2>&1; then
    err "python3 is required but was not found on PATH."
    exit 1
  fi

  info "Installing qcp via pip (pipx preferred if available)..."

  if command -v pipx >/dev/null 2>&1; then
    pipx install "qcp"
  else
    python3 -m pip install --user --upgrade "qcp"
  fi

  mkdir -p "$INSTALL_DIR"

  if ! command -v "$BIN_NAME" >/dev/null 2>&1; then
    info "Note: add this to your shell profile if 'qcp' isn't found:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
  fi

  ok "qcp installed! Run 'qcp init' to connect a database, then 'qcp auth' to add your Gemini key."
}

main "$@"

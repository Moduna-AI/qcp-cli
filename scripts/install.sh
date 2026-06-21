#!/usr/bin/env bash
# Installer for qcp (Query Companion).
# Usage: curl -fsSL https://raw.githubusercontent.com/Moduna-AI-cli/main/scripts/install.sh | bash
set -euo pipefail

REPO="Moduna-AI/qcp-cli"
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
  # 1. Detect platform architecture
  local platform
  platform=$(detect_platform)
  
  # 2. Get the latest release tag from GitHub API
  info "Fetching latest version metadata..."
  local tag
  tag=$(curl -fsSL "https://github.com{REPO}/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
  
  info "Downloading qcp (${tag}) for ${platform}..."
  
  # 3. Formulate asset name matching your release naming scheme
  # (e.g., qcp-macos-arm64.tar.gz)
  local asset_name="qcp-${platform}.tar.gz"
  local download_url="https://github.com{REPO}/releases/download/${tag}/${asset_name}"
  
  # 4. Download and unpack directly into the target installation directory
  mkdir -p "$INSTALL_DIR"
  local tmp_dir
  tmp_dir=$(mktemp -d)
  
  # Ensure cleanup of temp files even on script failures
  trap 'rm -rf "$tmp_dir"' EXIT
  
  curl -fsSL "$download_url" -o "${tmp_dir}/${asset_name}"
  tar -xzf "${tmp_dir}/${asset_name}" -C "$tmp_dir"
  
  # Move binary and apply executable permissions
  mv "${tmp_dir}/${BIN_NAME}" "$INSTALL_DIR/${BIN_NAME}"
  chmod +x "$INSTALL_DIR/${BIN_NAME}"

  # 5. Check if the target installation directory is on the system PATH
  if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    info "Note: Add this to your shell profile (~/.zshrc or ~/.bash_profile) if 'qcp' isn't found:"
    echo "  export PATH=\"${INSTALL_DIR}:\$PATH\""
  fi

  ok "qcp installed successfully! Run 'qcp init' to connect a database, then 'qcp auth' to add your Gemini key."
}

main "$@"

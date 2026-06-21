# Homebrew formula for qcp.
# Intended to live in a tap repo, e.g. Moduna-AI/homebrew-qcp/Formula/qcp.rb

class Qcp < Formula
  include Language::Python::Virtualenv

  desc "Query Companion: query Postgres databases in natural language"
  homepage "https://github.com"
  url "https://github.com"
  sha256 "3c441b7ab6998e7658bcb0cc530f95fe7f8e862c2dad908f05850939606bf4e2"
  version "0.1.4"
  license "MIT"

  # Depend on Homebrew's stable python
  depends_on "python@3.14"

  def install
    # 1. Creates an isolated private virtual environment inside the Cellar
    venv = virtualenv_create(libexec, "python3.14")
    
    # 2. Installs your tool and its requirements directly into that environment
    # This automatically reads your pyproject.toml / setup.py entry_points
    # and links the global executable to Homebrew's public bin folder
    venv.pip_install_and_link_binary_sync(buildpath)
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/qcp --version")
  end
end

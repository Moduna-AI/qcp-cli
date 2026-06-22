class Qcp < Formula
  include Language::Python::Virtualenv

  desc "Query Companion"
  homepage "https://github.com/Moduna-AI/qcp-cli"
  url "file:///Users/ashwin/Documents/github/qcp-cli/dist/qcp_cli-0.1.12a2.tar.gz"
  sha256 "9ce6e59ec4485012e3d2dc707c8f337593ca921292d09c01384de124d7a4c8a4"

  depends_on "python@3.14"

  def install
    system "python3.14", "-m", "venv", libexec
    system libexec/"bin/python", "-m", "pip", "install", "--upgrade", "pip"
    system libexec/"bin/python", "-m", "pip", "install", buildpath
    bin.install_symlink libexec/"bin/qcp"
  end
end
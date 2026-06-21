# Homebrew formula for qcp.
# Intended to live in a tap repo, e.g. Moduna-AI/homebrew-qcp/Formula/qcp.rb
#
# The CI release workflow updates `url` and `sha256` automatically on each
# tagged release (see .github/workflows/release.yml -> update-homebrew job).

class Qcp < Formula
	desc "Query Companion: query Postgres databases in natural language"
	homepage "https://github.com/Moduna-AI/qcp"
	version "0.1.0" # This string will be dynamically bumped by your CI
	license "MIT"

  # 1. Dynamically detect OS and CPU architecture to pull the right binary asset
	if OS.mac?
    	if Hardware::CPU.arm?
			url "https://github.com{version}/qcp-macos-arm64.tar.gz"
			sha256 "REPLACED_BY_CI_MAC_ARM"
    	else
    		url "https://github.com{version}/qcp-macos-amd64.tar.gz"
    		sha256 "REPLACED_BY_CI_MAC_AMD"
    	end
  	elsif OS.linux?
    	if Hardware::CPU.arm?
			url "https://github.com{version}/qcp-linux-arm64.tar.gz"
			sha256 "REPLACED_BY_CI_LINUX_ARM"
    	else
			url "https://github.com{version}/qcp-linux-amd64.tar.gz"
			sha256 "REPLACED_BY_CI_LINUX_AMD"
    	end
  	end

  # Remove dependency on python@3.14 since we are shipping pre-compiled binaries
  
	def install
    # 2. Extract and link the specific executable binary directly to Homebrew's bin folder
		bin.install "qcp"
  	end

  	test do
    	assert_match "qcp", shell_output("#{bin}/qcp --version")
  	end
end

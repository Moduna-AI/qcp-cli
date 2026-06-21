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
			url "https://github.com/Moduna-AI/qcp/archive/refs/tags/v0.1.3.tar.gz"
			sha256 "3c441b7ab6998e7658bcb0cc530f95fe7f8e862c2dad908f05850939606bf4e2"
    	else
    		url "https://github.com/Moduna-AI/qcp/archive/refs/tags/v0.1.3.tar.gz"
    		sha256 "3c441b7ab6998e7658bcb0cc530f95fe7f8e862c2dad908f05850939606bf4e2"
    	end
  	elsif OS.linux?
    	if Hardware::CPU.arm?
			url "https://github.com/Moduna-AI/qcp/archive/refs/tags/v0.1.3.tar.gz"
			sha256 "3c441b7ab6998e7658bcb0cc530f95fe7f8e862c2dad908f05850939606bf4e2"
    	else
			url "https://github.com/Moduna-AI/qcp/archive/refs/tags/v0.1.3.tar.gz"
			sha256 "3c441b7ab6998e7658bcb0cc530f95fe7f8e862c2dad908f05850939606bf4e2"
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

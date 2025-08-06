class SpecsmithCli < Formula
  desc "Command line interface for SpecSmith - A conversational AI tool for code generation and documentation"
  homepage "https://github.com/specsmith-ai/specsmith-cli"
  url "https://github.com/specsmith-ai/specsmith-cli/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "SKIP_SHA256_CHECK"
  license "MIT"

  depends_on "python@3.9"

  def install
    system "python3", "-m", "pip", "install", *std_pip_args, "."
  end

  test do
    system "#{bin}/specsmith", "--version"
  end
end

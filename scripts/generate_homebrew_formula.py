#!/usr/bin/env python3
"""Generate Homebrew formula for specsmith-cli."""

import json
import subprocess
import sys
from pathlib import Path


def get_version():
    """Get the current version from pyproject.toml."""
    import tomllib

    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

    return data["tool"]["poetry"]["version"]


def get_sha256(url):
    """Get SHA256 hash of a URL."""
    result = subprocess.run(["curl", "-sL", url], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Failed to download {url}")

    import hashlib

    return hashlib.sha256(result.stdout.encode()).hexdigest()


def generate_formula():
    """Generate the Homebrew formula."""
    version = get_version()

    # GitHub release URL
    github_url = f"https://github.com/specsmith-ai/specsmith-cli/archive/refs/tags/v{version}.tar.gz"

    # PyPI URL
    pypi_url = f"https://files.pythonhosted.org/packages/source/s/specsmith-cli/specsmith-cli-{version}.tar.gz"

    # Get SHA256 for GitHub release
    try:
        sha256 = get_sha256(github_url)
    except Exception as e:
        print(f"Warning: Could not get SHA256 for GitHub release: {e}")
        sha256 = "SKIP_SHA256_CHECK"

    formula = f"""class SpecsmithCli < Formula
  desc "Command line interface for SpecSmith - A conversational AI tool for code generation and documentation"
  homepage "https://github.com/specsmith-ai/specsmith-cli"
  url "{github_url}"
  sha256 "{sha256}"
  license "MIT"

  depends_on "python@3.9"

  def install
    system "python3", "-m", "pip", "install", *std_pip_args, "."
  end

  test do
    system "#{{bin}}/specsmith", "--version"
  end
end
"""

    return formula


if __name__ == "__main__":
    formula = generate_formula()

    if len(sys.argv) > 1 and sys.argv[1] == "--output":
        output_file = sys.argv[2]
        with open(output_file, "w") as f:
            f.write(formula)
        print(f"Formula written to {output_file}")
    else:
        print(formula)

#!/usr/bin/env python3
"""Build and publish the package to PyPI."""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed with return code {result.returncode}")

    return result


def main():
    """Main build and publish process."""
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print(
            "Error: pyproject.toml not found. Please run this script from the project root."
        )
        sys.exit(1)

    # Clean previous builds
    print("Cleaning previous builds...")
    run_command("rm -rf dist/ build/ *.egg-info/")

    # Install build dependencies
    print("Installing build dependencies...")
    run_command("poetry install")

    # Run tests
    print("Running tests...")
    run_command("poetry run pytest tests/ -v")

    # Run linting
    print("Running linting...")
    run_command("poetry run black --check .")
    run_command("poetry run isort --check-only .")

    # Build the package
    print("Building package...")
    run_command("poetry build")

    # Check if we should publish
    if len(sys.argv) > 1 and sys.argv[1] == "--publish":
        if not os.getenv("PYPI_API_TOKEN"):
            print("Error: PYPI_API_TOKEN environment variable not set")
            sys.exit(1)

        print("Publishing to PyPI...")
        run_command("poetry publish")
        print("✅ Successfully published to PyPI!")
    else:
        print("✅ Build completed successfully!")
        print("To publish to PyPI, run: python scripts/build_and_publish.py --publish")


if __name__ == "__main__":
    main()

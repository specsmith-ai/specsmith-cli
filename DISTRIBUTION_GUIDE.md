# Distribution Guide for SpecSmith CLI

This guide covers how to distribute the SpecSmith CLI via PyPI and Homebrew.

## PyPI Distribution

### Prerequisites

1. **PyPI Account**: Create an account on [PyPI](https://pypi.org/)
2. **API Token**: Generate an API token in your PyPI account settings
3. **TestPyPI Account**: Create an account on [TestPyPI](https://test.pypi.org/) for testing

### Local Development Setup

1. **Install build tools**:
   ```bash
   pip install build twine
   ```

2. **Configure Poetry for PyPI**:
   ```bash
   poetry config pypi-token.pypi YOUR_PYPI_API_TOKEN
   poetry config pypi-token.testpypi YOUR_TEST_PYPI_API_TOKEN
   ```

### Building and Publishing

#### Manual Publishing

1. **Build the package**:
   ```bash
   poetry build
   ```

2. **Test on TestPyPI** (recommended):
   ```bash
   poetry publish --repository testpypi
   ```

3. **Publish to PyPI**:
   ```bash
   poetry publish
   ```

#### Automated Publishing

1. **Set up GitHub Secrets**:
   - Go to your GitHub repository settings
   - Add `PYPI_API_TOKEN` secret with your PyPI API token

2. **Create a release**:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. **The GitHub Action will automatically**:
   - Run tests
   - Build the package
   - Publish to PyPI
   - Create a GitHub release

### Version Management

1. **Update version in pyproject.toml**:
   ```toml
   [tool.poetry]
   version = "0.1.1"
   ```

2. **Create a new release**:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.1.1"
   git tag v0.1.1
   git push origin main v0.1.1
   ```

## Homebrew Distribution

### Prerequisites

1. **Homebrew Tap Repository**: Create a repository named `homebrew-specsmith-cli`
2. **GitHub Release**: Ensure your package is released on GitHub

### Setting up Homebrew Tap

1. **Create the tap repository**:
   ```bash
   # Create a new repository on GitHub named "homebrew-specsmith-cli"
   git clone https://github.com/yourusername/homebrew-specsmith-cli.git
   cd homebrew-specsmith-cli
   ```

2. **Generate the formula**:
   ```bash
   cd /path/to/specsmith-cli
   python scripts/generate_homebrew_formula.py --output ../homebrew-specsmith-cli/Formula/specsmith-cli.rb
   ```

3. **Commit and push**:
   ```bash
   cd ../homebrew-specsmith-cli
   git add Formula/specsmith-cli.rb
   git commit -m "Add specsmith-cli formula"
   git push origin main
   ```

### Installing via Homebrew

Users can then install via:
```bash
brew tap yourusername/specsmith-cli
brew install specsmith-cli
```

### Updating the Formula

1. **Update the formula**:
   ```bash
   cd /path/to/specsmith-cli
   python scripts/generate_homebrew_formula.py --output ../homebrew-specsmith-cli/Formula/specsmith-cli.rb
   ```

2. **Commit and push**:
   ```bash
   cd ../homebrew-specsmith-cli
   git add Formula/specsmith-cli.rb
   git commit -m "Update specsmith-cli to v0.1.1"
   git push origin main
   ```

## Testing the Distribution

### Test PyPI Installation

1. **Install from TestPyPI**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ specsmith-cli
   ```

2. **Test the installation**:
   ```bash
   specsmith --version
   ```

### Test Homebrew Installation

1. **Install via Homebrew**:
   ```bash
   brew install yourusername/specsmith-cli/specsmith-cli
   ```

2. **Test the installation**:
   ```bash
   specsmith --version
   ```

## Release Checklist

### Before Release

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` (if applicable)
- [ ] Run tests: `poetry run pytest tests/ -v`
- [ ] Run linting: `poetry run black . && poetry run isort .`
- [ ] Test build: `poetry build`
- [ ] Test installation: `pip install dist/*.whl`

### PyPI Release

- [ ] Create GitHub release tag: `git tag v0.1.0`
- [ ] Push tag: `git push origin v0.1.0`
- [ ] Verify GitHub Action runs successfully
- [ ] Check PyPI for the new release
- [ ] Test installation: `pip install specsmith-cli`

### Homebrew Release

- [ ] Generate new formula: `python scripts/generate_homebrew_formula.py`
- [ ] Update Homebrew tap repository
- [ ] Test installation: `brew install yourusername/specsmith-cli/specsmith-cli`

## Troubleshooting

### PyPI Issues

1. **Authentication Error**:
   - Verify your PyPI API token
   - Check token permissions

2. **Package Already Exists**:
   - Increment version number
   - Ensure unique version

3. **Build Errors**:
   - Check `pyproject.toml` syntax
   - Verify all dependencies are listed

### Homebrew Issues

1. **Formula Not Found**:
   - Check tap repository name
   - Verify formula file exists

2. **Installation Fails**:
   - Check Python dependency
   - Verify SHA256 hash

3. **SHA256 Mismatch**:
   - Regenerate formula with correct hash
   - Check GitHub release URL

## Security Considerations

1. **API Tokens**: Never commit API tokens to version control
2. **Dependencies**: Regularly update dependencies for security patches
3. **Signing**: Consider GPG signing releases for additional security
4. **Vulnerability Scanning**: Use tools like `safety` to check for vulnerabilities

## Monitoring

1. **PyPI Downloads**: Monitor download statistics on PyPI
2. **GitHub Releases**: Track release downloads and issues
3. **User Feedback**: Monitor issues and feature requests
4. **Dependency Updates**: Keep dependencies up to date

## Best Practices

1. **Semantic Versioning**: Follow semantic versioning (MAJOR.MINOR.PATCH)
2. **Release Notes**: Write clear release notes for each version
3. **Testing**: Always test releases before publishing
4. **Documentation**: Keep documentation up to date
5. **Backward Compatibility**: Maintain backward compatibility when possible

# Release Checklist for SpecSmith CLI

This document outlines the steps to prepare and execute a release of the SpecSmith CLI to PyPI.

## ✅ Pre-Release Preparation (Completed)

- [x] **GitHub Actions Workflow**: Created `.github/workflows/release.yml` for automated PyPI publishing
- [x] **Package Metadata**: Updated `pyproject.toml` with correct URLs, authors, and classifiers
- [x] **Documentation**: Created comprehensive `README.md` with marketing copy and quickstart guide
- [x] **Changelog**: Added `CHANGELOG.md` for version tracking
- [x] **Contributing Guidelines**: Added `CONTRIBUTING.md` with development workflow
- [x] **Production Configuration**: Updated default API URL to `https://api.specsmith.ai`
- [x] **Version Management**: Ensured version command works properly

## 🚀 Release Process

### 1. Pre-Release Testing

Before creating a release, test the package locally:

```bash
# Build the package
poetry build

# Test installation from local build
pip install dist/specsmith_cli-*.whl

# Test basic functionality
specsmith --version
specsmith --help
```

### 2. GitHub Repository Setup

Ensure your GitHub repository is properly configured:

1. **Repository Settings**:
   - Repository name: `specsmith-cli`
   - Description: "Command line interface for SpecSmith - AI-powered specification generation"
   - Topics: `cli`, `ai`, `specifications`, `python`, `specsmith`

2. **Required Secrets**:
   - `PYPI_API_TOKEN`: Your PyPI API token for publishing

3. **Branch Protection** (recommended):
   - Protect `main` branch
   - Require pull request reviews
   - Require status checks to pass

### 3. Creating a Release

#### Step 1: Update Version
Update the version in `pyproject.toml`:
```toml
[tool.poetry]
version = "0.1.0"  # Update to your desired version
```

#### Step 2: Update Changelog
Update `CHANGELOG.md` with release notes:
```markdown
## [0.1.0] - 2024-01-XX

### Added
- Initial public release
- Interactive chat interface with streaming responses
- API key management and configuration
- File action handling
- Production-ready documentation
```

#### Step 3: Commit Changes
```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Release v0.1.0"
git push origin main
```

#### Step 4: Create and Push Tag
```bash
git tag v0.1.0
git push origin v0.1.0
```

#### Step 5: Monitor Release
The GitHub Action will automatically:
1. Run tests on multiple Python versions (3.9-3.12)
2. Build the package
3. Publish to PyPI
4. Create a GitHub release with artifacts

### 4. Post-Release Verification

After the release completes:

```bash
# Test installation from PyPI
pip install specsmith-cli

# Verify functionality
specsmith --version
specsmith test  # (requires API credentials)
```

## 🔧 GitHub Secrets Configuration

### Required Secrets

1. **PYPI_API_TOKEN**:
   - Go to [PyPI Account Settings](https://pypi.org/manage/account/)
   - Create a new API token
   - Scope: "Entire account" or specific to "specsmith-cli" project
   - Add to GitHub repository secrets

### Setting Up Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following:
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI API token (starts with `pypi-`)

## 🐛 Troubleshooting

### Common Issues

**Build Failures**:
- Check Python version compatibility
- Verify all dependencies are properly specified
- Ensure tests pass locally first

**PyPI Upload Failures**:
- Verify PYPI_API_TOKEN is correct
- Check if version already exists on PyPI
- Ensure package name is available

**GitHub Action Failures**:
- Check workflow logs in GitHub Actions tab
- Verify all required secrets are set
- Ensure branch protection rules allow the action to run

### Manual Release (Fallback)

If automated release fails, you can publish manually:

```bash
# Install build tools
pip install build twine

# Build package
poetry build

# Upload to PyPI
poetry publish
# OR
twine upload dist/*
```

## 📋 Release Checklist Template

For each release, copy and complete this checklist:

### Pre-Release
- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Run tests locally: `poetry run pytest tests/ -v`
- [ ] Build package locally: `poetry build`
- [ ] Test local installation: `pip install dist/*.whl`
- [ ] Verify CLI functionality works

### Release
- [ ] Commit version changes: `git commit -m "Release vX.Y.Z"`
- [ ] Push to main: `git push origin main`
- [ ] Create tag: `git tag vX.Y.Z`
- [ ] Push tag: `git push origin vX.Y.Z`
- [ ] Monitor GitHub Action completion
- [ ] Verify PyPI upload successful

### Post-Release
- [ ] Test installation from PyPI: `pip install specsmith-cli`
- [ ] Verify GitHub release created
- [ ] Update documentation if needed
- [ ] Announce release (if applicable)

## 🎯 Next Steps

After your first successful release:

1. **Monitor Usage**: Check PyPI download statistics
2. **Gather Feedback**: Monitor GitHub issues and user feedback
3. **Plan Updates**: Use semantic versioning for future releases
4. **Automation**: Consider automating version bumping with tools like `bump2version`

## 📞 Support

If you encounter issues with the release process:
- Check GitHub Actions logs
- Review PyPI project dashboard
- Contact support at [support@specsmith.ai](mailto:support@specsmith.ai)

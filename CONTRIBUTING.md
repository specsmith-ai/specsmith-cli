# Contributing to SpecSmith CLI

Thank you for your interest in contributing to SpecSmith CLI! We welcome contributions from the community and are excited to work with you.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management
- Git for version control

### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/yourusername/specsmith-cli.git
   cd specsmith-cli
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Verify the setup**:
   ```bash
   poetry run specsmith --help
   ```

4. **Run tests**:
   ```bash
   poetry run pytest tests/ -v
   ```

## 🛠️ Development Workflow

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards (see below)

3. **Add tests** for new functionality

4. **Run the test suite**:
   ```bash
   poetry run pytest tests/ -v
   ```

5. **Run code formatting**:
   ```bash
   poetry run black .
   poetry run isort .
   ```

6. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

7. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Submit a pull request**

### Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

**Examples:**
```
feat: add streaming response support
fix: handle connection timeout errors
docs: update installation instructions
test: add unit tests for config validation
```

## 📝 Coding Standards

### Python Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **pytest** for testing

### Code Quality Guidelines

1. **Type Hints**: Use type hints for all function parameters and return values
   ```python
   def process_message(message: str, timeout: int = 30) -> dict[str, Any]:
       pass
   ```

2. **Docstrings**: Add docstrings for all public functions and classes
   ```python
   def validate_credentials(config: Config) -> bool:
       """Validate API credentials format and basic structure.
       
       Args:
           config: Configuration object containing credentials
           
       Returns:
           True if credentials are valid format, False otherwise
       """
   ```

3. **Error Handling**: Use specific exception types and provide helpful error messages
   ```python
   if not config.access_key_id:
       raise ValueError("Access key ID is required. Run 'specsmith setup' to configure.")
   ```

4. **Testing**: Write tests for new functionality
   ```python
   def test_config_validation():
       config = Config(access_key_id="", access_key_token="valid-token")
       assert not validate_credentials(config)
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/test_config.py -v

# Run with coverage
poetry run pytest tests/ --cov=specsmith_cli --cov-report=html
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names: `test_config_validation_with_missing_key_id`
- Test both success and failure cases
- Mock external dependencies (API calls, file operations)

**Example test:**
```python
import pytest
from specsmith_cli.config import Config, validate_credentials

def test_validate_credentials_with_valid_config():
    config = Config(
        access_key_id="valid-key-id",
        access_key_token="valid-token",
        api_url="https://api.specsmith.ai"
    )
    assert validate_credentials(config) is True

def test_validate_credentials_with_missing_token():
    config = Config(
        access_key_id="valid-key-id",
        access_key_token="",
        api_url="https://api.specsmith.ai"
    )
    assert validate_credentials(config) is False
```

## 📚 Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Include type hints for better IDE support
- Document complex algorithms or business logic

### README Updates

When adding new features:
- Update usage examples in README.md
- Add new command-line options to the documentation
- Include troubleshooting information for common issues

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment information**:
   - Python version
   - Operating system
   - CLI version (`specsmith --version`)

2. **Steps to reproduce**:
   ```
   1. Run `specsmith chat "test message"`
   2. See error message
   ```

3. **Expected vs actual behavior**

4. **Error messages or logs** (with sensitive information removed)

5. **Additional context** that might be relevant

## 💡 Feature Requests

When suggesting new features:

1. **Describe the problem** you're trying to solve
2. **Explain your proposed solution**
3. **Consider alternatives** you've thought about
4. **Provide use cases** where this would be helpful

## 🔒 Security

### Reporting Security Issues

**Do not report security vulnerabilities through public GitHub issues.**

Instead, please email us at [security@specsmith.ai](mailto:security@specsmith.ai) with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes

### Security Best Practices

When contributing:
- Never commit API keys, tokens, or other secrets
- Validate all user inputs
- Use secure defaults for configuration options
- Follow principle of least privilege

## 📋 Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally (`poetry run pytest tests/ -v`)
- [ ] Code is formatted (`poetry run black . && poetry run isort .`)
- [ ] Documentation is updated if needed
- [ ] Commit messages follow conventional format
- [ ] No sensitive information in commits

### Pull Request Template

When submitting a PR, please include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Added/updated tests
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

## 🎯 Areas for Contribution

We especially welcome contributions in these areas:

### High Priority
- **Error handling improvements** - Better error messages and recovery
- **Performance optimizations** - Faster startup, reduced memory usage
- **Cross-platform compatibility** - Windows, macOS, Linux testing
- **Documentation** - Examples, tutorials, troubleshooting guides

### Medium Priority
- **Configuration enhancements** - More flexible config options
- **Testing** - Increase test coverage, integration tests
- **CLI UX improvements** - Better prompts, progress indicators
- **Logging** - Structured logging, better debug information

### Future Features
- **Plugin system** - Extensible architecture for custom tools
- **Offline mode** - Local processing capabilities
- **Shell completions** - Bash, Zsh, Fish completion scripts
- **Configuration validation** - Better config file validation

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone, regardless of:
- Age, body size, disability, ethnicity, gender identity and expression
- Level of experience, education, socio-economic status
- Nationality, personal appearance, race, religion
- Sexual identity and orientation

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Harassment, trolling, or discriminatory comments
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting [conduct@specsmith.ai](mailto:conduct@specsmith.ai). All complaints will be reviewed and investigated promptly and fairly.

## 📞 Getting Help

- **Documentation**: [GitHub README](https://github.com/specsmith-ai/specsmith-cli#readme)
- **Discussions**: [GitHub Discussions](https://github.com/specsmith-ai/specsmith-cli/discussions)
- **Issues**: [GitHub Issues](https://github.com/specsmith-ai/specsmith-cli/issues)
- **Email**: [support@specsmith.ai](mailto:support@specsmith.ai)

## 🙏 Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Special thanks in documentation

Thank you for contributing to SpecSmith CLI! 🚀

# SpecSmith CLI

A command line interface for the SpecSmith application that provides a chat client for interacting with the SpecSmith Agent API.

## Features

- **Streaming Chat Interface**: Real-time streaming of API responses to the terminal
- **Session Management**: Persistent conversation sessions
- **File Actions**: Handle file creation and overwrite prompts
- **API Key Management**: Support for environment variables and config files
- **Rich Terminal Output**: Beautiful terminal interface with Rich

## Installation

### From PyPI (Recommended)

```bash
pip install specsmith-cli
```

### From Homebrew

```bash
# Add the tap (once)
brew tap yourusername/specsmith-cli

# Install the CLI
brew install specsmith-cli
```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/specsmith-ai/specsmith-cli.git
cd specsmith-cli

# Install dependencies
poetry install

# Run the CLI
poetry run specsmith --help
```

## Configuration

### API Keys

The CLI supports API key configuration through:

1. **Environment Variables**:
   ```bash
   export SPECSMITH_ACCESS_KEY_ID="your-access-key-id"
   export SPECSMITH_ACCESS_KEY_TOKEN="your-access-key-token"
   ```

2. **Config File** (Recommended):
   ```bash
   # Create config directory
   mkdir -p ~/.specsmith

   # Create credentials file
   cat > ~/.specsmith/credentials << EOF
   access_key_id=your-access-key-id
   access_key_token=your-access-key-token
   EOF
   ```

3. **Command Line**:
   ```bash
   specsmith --access-key-id your-id --access-key-token your-token
   ```

### API URL

Configure the API URL:

```bash
export SPECSMITH_API_URL="http://localhost:8000"
```

## Usage

### Basic Chat

```bash
# Start a chat session
specsmith chat

# Send a message
specsmith chat "Create a Python function to calculate fibonacci numbers"
```

### Interactive Mode

```bash
# Start interactive chat
specsmith chat --interactive
```

### File Actions

When the API returns file actions, the CLI will:

1. Check if the file already exists in the current directory
2. Prompt for overwrite confirmation if the file exists
3. Prompt for save confirmation if the file is new
4. Save the file with the specified content

## Development

### Project Structure

```
specsmith-cli/
├── specsmith_cli/
│   ├── __init__.py
│   ├── main.py              # Main CLI entry point
│   ├── api_client.py        # HTTP client for API communication
│   ├── config.py            # Configuration management
│   ├── chat.py              # Chat interface implementation
│   └── utils.py             # Utility functions
├── pyproject.toml           # Poetry configuration
└── README.md               # This file
```

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black .
poetry run isort .
```

## API Integration

The CLI integrates with the SpecSmith Agent API:

- **Session Management**: Creates and manages conversation sessions
- **Streaming Responses**: Handles real-time streaming of API responses
- **Action Types**: Supports message and file actions from the API
- **Authentication**: Uses Basic Auth with API keys

## Troubleshooting

### Common Issues

1. **API Connection Failed**:
   - Check if the SpecSmith API is running
   - Verify the API URL configuration
   - Ensure API keys are correctly set

2. **Authentication Errors**:
   - Verify API key credentials
   - Check that the API key is not revoked
   - Ensure proper encoding of credentials

3. **File Save Issues**:
   - Check write permissions in the current directory
   - Verify file paths are valid
   - Ensure sufficient disk space

### Debug Mode

Enable debug logging:

```bash
export SPECSMITH_DEBUG=1
specsmith chat
```

## Contributing

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

3. **Run tests**:
   ```bash
   poetry run pytest tests/ -v
   ```

4. **Run linting**:
   ```bash
   poetry run black .
   poetry run isort .
   ```

### Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Add tests for new functionality
4. Run the test suite: `poetry run pytest tests/ -v`
5. Run linting: `poetry run black . && poetry run isort .`
6. Commit your changes: `git commit -m "Add your feature"`
7. Push to your fork: `git push origin feature/your-feature`
8. Submit a pull request

### Release Process

See [DISTRIBUTION_GUIDE.md](DISTRIBUTION_GUIDE.md) for detailed instructions on releasing to PyPI and Homebrew.

## License

This project is licensed under the MIT License.

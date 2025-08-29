# Specsmith CLI

> **Forge clear specifications from product ideas.**
> *AI-powered agent for developers and builders.*

[![PyPI version](https://badge.fury.io/py/specsmith-cli.svg)](https://badge.fury.io/py/specsmith-cli)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The Specsmith CLI is a thin client for AI-powered specification generation using the Specsmith platform. Run `specsmith`, describe what you need, and get structured, implementation-ready technical specs.

## 🚀 What is Specsmith?

Specsmith helps engineers move from rough ideas to actionable specifications. It asks clarifying questions, identifies ambiguities, and produces detailed specs designed to feed directly into AI coding agents or human implementation.

### ✨ Key Capabilities

* **🧠 Structured Specs**: From natural language to clear acceptance criteria & Definition of Done
* **💬 Clarifying Conversations**: Interactive chat that refines requirements before finalizing
* **📁 File Handling**: Create and update spec files right from the CLI
* **⚡ Streaming Responses**: Real-time feedback as the AI reasons through your request
* **🎯 Simple Entry Point**: Just run `specsmith` — no flags required

## 🎯 Perfect For

* Product managers defining features
* Engineers planning implementations
* Architects documenting systems
* DevOps & infra teams writing technical runbooks

## 📦 Installation

```bash
pip install specsmith-cli
specsmith --version
```

## ⚡ Quickstart

### 1. Get Your API Keys

Learn more at [specsmith.ai](https://specsmith.ai) or go straight to [signup](https://app.specsmith.ai/signup) → **Settings** → **API Keys** → generate a new key pair.

### 2. Configure Authentication

Recommended:

```bash
specsmith setup
```

Advanced alternatives:

* **Env vars**

  ```bash
  export SPECSMITH_ACCESS_KEY_ID="your-access-key-id"
  export SPECSMITH_ACCESS_KEY_TOKEN="your-access-key-token"
  ```
* **Config file**

  ```bash
  mkdir -p ~/.specsmith
  cat > ~/.specsmith/credentials << EOF
  access_key_id=your-access-key-id
  access_key_token=your-access-key-token
  EOF
  ```

### 3. Test

```bash
specsmith test
```

### 4. Start Workinggit add 0p


```bash
specsmith
```

That’s it — describe what you need, and specsmith will generate detailed specifications.

## 🎨 Usage Examples

Interactive session:

```bash
specsmith
```

Example:

```
You: I need a real-time chat app

specsmith: Let’s cover scale, features, tech stack, and platforms.
...
```

File management:

```bash
# Inside a chat session
# ✓ Create new file: database-schema.sql? (y/n): y
```

Configuration:

```bash
specsmith config
```

## 🛠️ Advanced Features

* **Custom API Endpoint**

  ```bash
  export SPECSMITH_API_URL="https://your.company/api"
  ```

* **Debug Mode**

  ```bash
  specsmith --debug
  ```

* **Available Commands**

  ```bash
  specsmith chat      # start chat (default)
  specsmith setup     # configure credentials
  specsmith test      # test connection
  specsmith config    # show current config
  specsmith version   # version info
  specsmith --help    # all options
  ```

## 🔧 Configuration Options

| Variable                     | Description          | Default                    |
| ---------------------------- | -------------------- | -------------------------- |
| `SPECSMITH_ACCESS_KEY_ID`    | API key ID           | required                   |
| `SPECSMITH_ACCESS_KEY_TOKEN` | API key token        | required                   |
| `SPECSMITH_API_URL`          | API endpoint         | `https://api.specsmith.ai` |
| `SPECSMITH_DEBUG`            | Enable debug logging | `false`                    |

Config sources (priority order):

1. `~/.specsmith/credentials`
2. Env vars
3. CLI args

## 🚀 Real-World Use Cases

```bash
specsmith
# "Plan a notification system for a mobile app with push + email"
```

```bash
specsmith
# "Design a REST API for a multi-tenant SaaS with RBAC"
```

```bash
specsmith
# "Specify a CI/CD pipeline for microservices on Kubernetes"
```

```bash
specsmith
# "Create a database schema for a social app with posts, comments, likes"
```

## 🔍 Troubleshooting

**Auth Errors**

```bash
specsmith test
specsmith setup
```

**Connection Issues**

```bash
curl -I https://api.specsmith.ai/health
specsmith test --debug
```

**File Permissions**

```bash
chmod 755 .
```

More help:

* Docs: [README](https://github.com/specsmith-ai/specsmith-cli#readme)
* Issues: [GitHub](https://github.com/specsmith-ai/specsmith-cli/issues)
* Website: [specsmith.ai](https://specsmith.ai)
* Signup: [app.specsmith.ai/signup](https://app.specsmith.ai/signup)
* Support: [support@specsmith.ai](mailto:support@specsmith.ai)

## 📄 License

MIT License — see [LICENSE](LICENSE)

## 🌟 Why specsmith?

Good code starts with good specs. specsmith makes your requirements:

* **Complete**: No missing edge cases
* **Actionable**: Ready for humans or AI agents
* **Consistent**: Following best practices & standards
* **Contextual**: Informed by your repo & architecture

**Transform your workflow. Start with better specs.**

---

<div align="center">

**[Get Started](https://specsmith.ai)** • **[Signup](https://app.specsmith.ai/signup)** • **[Docs](https://github.com/specsmith-ai/specsmith-cli#readme)**

Made with ❤️ by specsmith

</div>

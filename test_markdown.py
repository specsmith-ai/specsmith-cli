#!/usr/bin/env python3
"""Test script to debug Rich Markdown rendering issues."""

import time

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text


def test_basic_markdown():
    """Test basic markdown rendering."""
    console = Console()

    print("=== Test 1: Basic Markdown Rendering ===")
    markdown_content = """
# Test Header

This is a **bold** text and this is *italic* text.

## Code Block

```python
def hello():
    print("Hello, World!")
```

## List

- Item 1
- Item 2
- Item 3

## Link

[Rich Documentation](https://rich.readthedocs.io/)
"""

    md = Markdown(markdown_content)
    console.print(md)
    print("\n" + "=" * 50 + "\n")


def test_streaming_markdown():
    """Test streaming markdown with Live updates."""
    console = Console()

    print("=== Test 2: Streaming Markdown with Live ===")

    # Simulate streaming content
    content_parts = [
        "# Streaming Test\n\n",
        "This is **streaming** content.\n\n",
        "## Code Example\n\n",
        "```python\n",
        "def stream():\n",
        "    return 'data'\n",
        "```\n\n",
        "- First item\n",
        "- Second item\n",
        "- Third item\n",
    ]

    response_text = ""

    with Live(Text("Starting..."), refresh_per_second=10, console=console) as live:
        for part in content_parts:
            response_text += part
            # Try updating with Markdown
            live.update(Markdown(response_text))
            time.sleep(0.5)  # Simulate streaming delay

    print("\n" + "=" * 50 + "\n")


def test_partial_markdown():
    """Test how Rich handles partial/incomplete markdown."""
    console = Console()

    print("=== Test 3: Partial Markdown Content ===")

    # Test incomplete markdown structures
    partial_contents = [
        "# Header",
        "# Header\n\nSome **bold",
        "# Header\n\nSome **bold** text",
        "# Header\n\nSome **bold** text\n\n```python",
        "# Header\n\nSome **bold** text\n\n```python\ndef test():",
        "# Header\n\nSome **bold** text\n\n```python\ndef test():\n    pass\n```",
    ]

    for i, content in enumerate(partial_contents):
        print(f"--- Partial Content {i+1} ---")
        try:
            md = Markdown(content)
            console.print(md)
        except Exception as e:
            print(f"Error rendering: {e}")
        print()

    print("=" * 50 + "\n")


def test_live_with_text_vs_markdown():
    """Compare Live updates with Text vs Markdown."""
    console = Console()

    print("=== Test 4: Live Text vs Markdown Comparison ===")

    content = "# Header\n\nThis is **bold** text with `code`."

    print("--- Live with Text ---")
    with Live(Text("Starting..."), refresh_per_second=10, console=console) as live:
        for i in range(len(content)):
            partial = content[: i + 1]
            live.update(Text(partial))
            time.sleep(0.05)

    print("\n--- Live with Markdown ---")
    with Live(Text("Starting..."), refresh_per_second=10, console=console) as live:
        for i in range(len(content)):
            partial = content[: i + 1]
            try:
                live.update(Markdown(partial))
            except Exception as e:
                live.update(Text(f"Error: {e}"))
            time.sleep(0.05)

    print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    test_basic_markdown()
    test_streaming_markdown()
    test_partial_markdown()
    test_live_with_text_vs_markdown()

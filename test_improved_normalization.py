#!/usr/bin/env python3
"""Test the improved markdown normalization function."""

from rich.console import Console
from rich.markdown import Markdown


def normalize_markdown_alignment(content: str) -> str:
    """Normalize excessive left-padding outside fenced code blocks for better rendering.

    Keeps fenced code blocks verbatim; preserves proper markdown indentation;
    only removes excessive leading spaces that would cause unintended code blocks.
    """
    lines = content.splitlines()
    normalized = []
    in_code = False

    for line in lines:
        rline = line.rstrip()
        lstripped = rline.lstrip()

        # Handle fenced code blocks
        if lstripped.startswith("```"):
            in_code = not in_code
            normalized.append(rline)
            continue

        # Preserve content inside fenced code blocks
        if in_code:
            normalized.append(rline)
            continue

        # For non-code content, be more careful about preserving markdown structure
        leading_spaces = len(rline) - len(lstripped)

        # Preserve proper markdown indentation (2-3 spaces for nested lists, blockquotes)
        if leading_spaces <= 3:
            normalized.append(rline)
        # Only strip when we have excessive indentation (4+ spaces) that would trigger code blocks
        elif leading_spaces >= 4:
            # Check if this might be intentional indentation for nested elements
            if lstripped.startswith(("-", "*", "+")) and leading_spaces <= 6:
                # Preserve reasonable list indentation (up to 6 spaces)
                normalized.append(rline)
            elif lstripped.startswith(">") and leading_spaces <= 6:
                # Preserve reasonable blockquote indentation
                normalized.append(rline)
            else:
                # Strip excessive indentation that would cause code blocks
                normalized.append(lstripped)
        else:
            normalized.append(rline)

    return "\n".join(normalized)


def main():
    console = Console()

    # Test with the actual content from the debug files
    test_content = """Here's some sample markdown to demonstrate formatting:

# Main Heading

## Subheading

### Smaller Heading

**Bold text** and *italic text* and ***bold italic***

`Inline code` and here's a code block:

```javascript
function greetUser(name) {
    return `Hello, ${name}!`;
}
```

- Bullet point one
- Bullet point two
  - Nested bullet
  - Another nested item

1. Numbered list
2. Second item
3. Third item

> This is a blockquote
> It can span multiple lines

[Link text](https://example.com)

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| More     | Data     | Here     |

---

Horizontal rule above, and here's some `inline code` mixed with regular text.

~~Strikethrough text~~"""

    print("=== Original Content ===")
    print("Raw content:")
    print(repr(test_content))
    print()

    normalized = normalize_markdown_alignment(test_content)
    print("=== After Normalization ===")
    print("Raw normalized:")
    print(repr(normalized))
    print()

    print("=== Rendered ===")
    md = Markdown(normalized)
    console.print(md)


if __name__ == "__main__":
    main()

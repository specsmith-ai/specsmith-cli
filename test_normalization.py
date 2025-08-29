#!/usr/bin/env python3
"""Test the improved markdown normalization function."""

from rich.console import Console
from rich.markdown import Markdown


def normalize_markdown_alignment(content: str) -> str:
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

        # For non-code content, be more aggressive about removing leading spaces
        # to prevent markdown from treating content as code blocks
        leading_spaces = len(rline) - len(lstripped)

        # Always strip leading spaces from markdown headers
        if lstripped.startswith(("#", "-", "*", ">", "|")) or lstripped.startswith(
            ("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")
        ):
            normalized.append(lstripped)
        # Strip excessive leading spaces (4+ spaces trigger code blocks in markdown)
        elif leading_spaces >= 4:
            normalized.append(lstripped)
        else:
            normalized.append(rline)

    return "\n".join(normalized)


def main():
    console = Console()

    # Test problematic content with leading spaces
    problematic_content = """Here's a sample of markdown formatting:

    ## Overview
    Brief description of what we're building.

    ## Requirements
    ### Functional Requirements
    - **FR1**: User must be able to create an account
    - **FR2**: System shall validate email addresses

    Some regular text with leading spaces.

    ```python
    def example():
        # This should preserve indentation
        return 'code'
    ```
"""

    print("=== Before normalization ===")
    print("Raw content:")
    print(repr(problematic_content))
    print()

    normalized = normalize_markdown_alignment(problematic_content)
    print("=== After normalization ===")
    print("Raw normalized:")
    print(repr(normalized))
    print()

    print("=== Rendered ===")
    md = Markdown(normalized)
    console.print(md)


if __name__ == "__main__":
    main()

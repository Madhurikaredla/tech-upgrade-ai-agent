#!/usr/bin/env python3
"""
extract-file-headings.py

Reads a markdown file and writes a compact heading-only index to stdout or a file.
Useful for giving an LLM the shape of a large doc (e.g. glossary.md) without
the full content — so it knows what terms exist and their anchor names for linking.

Usage:
    python extract-file-headings.py <input.md>                  # prints to stdout
    python extract-file-headings.py <input.md> <output.md>      # writes to file
"""

import sys
import re


def extract_headings(text: str) -> list[str]:
    headings = []
    in_code_block = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_code_block = not in_code_block
        if in_code_block:
            continue
        if re.match(r"^#{1,6} ", line):
            headings.append(line.rstrip())
    return headings


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input.md> [output.md]", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    with open(input_path, encoding="utf-8") as f:
        text = f.read()

    headings = extract_headings(text)
    result = "\n".join(headings) + "\n"

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Written to {output_path}", file=sys.stderr)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()

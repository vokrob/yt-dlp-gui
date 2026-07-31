#!/usr/bin/env python3
"""Render the current CHANGELOG.md section as collapsible release notes (mirrors make_changelog.py of yt-dlp)."""

import argparse
import re
import sys


def extract_current_section(content):
    """Return the first version block (everything up to the next `### ` heading)."""
    match = re.search(r'(?m)^(### .*?)(?=^### |\Z)', content, re.DOTALL)
    return match.group(1).strip() if match else ''


def render_collapsible(section):
    """Wrap each `#### Category` of the section in a `<details>` block."""
    parts = re.split(r'(?m)^#### ', section)
    header = parts[0].rstrip()
    rendered = [header, ''] if header.strip() else []
    for part in parts[1:]:
        lines = part.splitlines()
        name = lines[0].strip()
        items = [line.rstrip() for line in lines[1:] if line.strip()]
        rendered.append('<details>')
        rendered.append(f'<summary><h4>{name}</h4></summary>')
        rendered.append('')
        rendered.extend(items)
        rendered.append('')
        rendered.append('</details>')
        rendered.append('')
    return '\n'.join(rendered).rstrip() + '\n'


def main():
    parser = argparse.ArgumentParser(description='Render changelog as release notes')
    parser.add_argument('--collapsible', action='store_true')
    args = parser.parse_args()

    with open('CHANGELOG.md', encoding='utf-8') as f:
        content = f.read()

    section = extract_current_section(content)
    if not section:
        return

    if args.collapsible:
        section = render_collapsible(section)
    sys.stdout.write(section)


if __name__ == '__main__':
    main()

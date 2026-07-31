#!/usr/bin/env python3
"""Generate CHANGELOG.md from git history (mirrors update_changelog.py of yt-dlp)."""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from devscripts.utils import run_process, write_file

CHANGELOG_FILE = 'CHANGELOG.md'

TYPES = [
    ('feat', 'Features'),
    ('fix', 'Bug fixes'),
    ('perf', 'Performance'),
    ('refactor', 'Refactoring'),
    ('docs', 'Documentation'),
    ('test', 'Tests'),
    ('ci', 'CI changes'),
    ('chore', 'Chores'),
    ('style', 'Code style'),
    ('other', 'Other'),
]

COMMIT_RE = re.compile(r'^([a-z]+)(?:\(([^)]+)\))?: (.+)$')


def get_previous_version(content):
    match = re.search(r'(?m)^### (.+)$', content)
    return match.group(1).strip() if match else None


def tag_exists(name):
    return run_process('git', 'rev-parse', '--verify', name, check=False).returncode == 0


def get_commits(prev_version):
    args = ['git', 'log', '--pretty=%s%x09%b', '--no-merges']
    if prev_version and tag_exists('latest'):
        args.append('latest..HEAD')
    proc = run_process(*args)
    commits = []
    for line in proc.stdout.strip().splitlines():
        subject, _, body = line.partition('\t')
        if ':ci skip all' in body:
            continue
        commits.append(subject.strip())
    return commits


def categorize(subject):
    match = COMMIT_RE.match(subject)
    if match:
        commit_type, scope, text = match.groups()
        prefix = f'[{scope}] ' if scope else ''
        return commit_type, f'{prefix}{text}'
    return 'other', subject


def group_commits(commits):
    sections = {name: [] for _, name in TYPES}
    for subject in commits:
        commit_type, text = categorize(subject)
        for type_, name in TYPES:
            if type_ == commit_type:
                sections[name].append(text)
                break
        else:
            sections['Other'].append(subject)
    return [(name, items) for name, items in sections.items() if items]


def render_section(version, sections, collapsible=False):
    lines = [f'### {version}', '']
    for name, items in sections:
        if collapsible:
            lines.append('<details>')
            lines.append(f'<summary><h4>{name}</h4></summary>')
            lines.append('')
        else:
            lines.append(f'#### {name}')
            lines.append('')
        lines.extend(f'- {" ".join(item.split())}' for item in items)
        lines.append('')
        if collapsible:
            lines.append('</details>')
            lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def main():
    parser = argparse.ArgumentParser(description='Update CHANGELOG.md')
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='Increase verbosity')
    parser.add_argument('version', nargs='?', default=None)
    args = parser.parse_args()

    previous = None
    previous_content = ''
    if os.path.exists(CHANGELOG_FILE):
        with open(CHANGELOG_FILE, encoding='utf-8') as f:
            previous_content = f.read()
        previous = get_previous_version(previous_content)

    commits = get_commits(previous)
    if not commits:
        print('No new commits')
        return

    version = args.version or os.environ.get('VERSION') or '???'
    sections = group_commits(commits)
    new_block = render_section(version, sections)

    if previous_content:
        previous_block = previous_content.rstrip()
        body = (
            f'{new_block}'
            f'<details>\n<summary>Previous versions</summary>\n\n'
            f'{previous_block}\n</details>\n'
        )
    else:
        body = new_block

    write_file(CHANGELOG_FILE, body)
    print(f'Updated: {CHANGELOG_FILE} ({version})')


if __name__ == '__main__':
    main()

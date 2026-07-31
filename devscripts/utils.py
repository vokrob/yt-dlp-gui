#!/usr/bin/env python3
"""Shared helpers for release devscripts (mirrors devscripts/utils.py of yt-dlp)."""

import datetime as dt
import re
import subprocess


def run_process(*args, **kwargs):
    kwargs.setdefault('check', True)
    kwargs.setdefault('text', True)
    kwargs.setdefault('stdout', subprocess.PIPE)
    kwargs.setdefault('stderr', subprocess.PIPE)
    return subprocess.run(args, **kwargs)


def write_file(path, content):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)


def calculate_version(version=None, prev_version=None):
    """Generate a yyyy.mm.dd[.rev] version, mirroring yt-dlp's scheme."""
    if version:
        return version
    date_str = dt.datetime.now(dt.timezone.utc).strftime('%Y.%m.%d')
    if prev_version and prev_version.startswith(date_str):
        parts = prev_version.split('.')
        if len(parts) >= 4:
            return f'{date_str}.{int(parts[3]) + 1}'
        return f'{date_str}.1'
    return date_str


VERSION_RE = re.compile(r'\b(\d{4}\.\d{2}\.\d{2}(?:\.\d+)?)\b')


def get_latest_release_version():
    """Parse the version from the current `latest` release title."""
    out = run_process(
        'gh', 'release', 'view', 'latest', '--json', 'title', '-q', '.title',
        check=False,
    ).stdout or ''
    match = VERSION_RE.search(out)
    return match.group(1) if match else None

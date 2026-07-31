#!/usr/bin/env python3
"""Shared helpers for release devscripts."""

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


def validate_version(version):
    """Validate a yyyy.mm.dd[.rev] version and return it."""
    assert version, 'Version must be specified'
    assert all(
        re.fullmatch(r'[0-9]+', part) for part in version.split('.')
    ), 'Version must be numeric'
    return version

#!/usr/bin/env python3
"""Update the version in __init__.py and pyproject.toml for a release."""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from devscripts.utils import validate_version, write_file

VERSION_FILES = (
    ('src/ytdlp_gui/__init__.py', r'(?m)^__version__\s*=\s*"[^"]*"',
     lambda v: f'__version__ = "{v}"'),
    ('pyproject.toml', r'(?m)^version\s*=\s*"[^"]*"',
     lambda v: f'version = "{v}"'),
)


def main():
    parser = argparse.ArgumentParser(description='Update the version files')
    parser.add_argument('version', help='Version: yyyy.mm.dd[.rev]')
    args = parser.parse_args()

    version = validate_version(args.version)
    for path, pattern, new_value in VERSION_FILES:
        with open(path, encoding='utf-8') as f:
            content = f.read()
        content = re.sub(pattern, new_value(version), content, count=1)
        write_file(path, content)
        print(f'Updated: {path}')

    print(f'version={version}')


if __name__ == '__main__':
    main()

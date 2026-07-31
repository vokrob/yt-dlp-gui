#!/usr/bin/env python3
"""Resolve the release version and write it to GITHUB_OUTPUT (mirrors setup_variables of yt-dlp)."""

import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from devscripts.utils import calculate_version, get_latest_release_version


def main():
    inputs = json.loads(os.environ['INPUTS'])
    version = (inputs.get('version') or '').strip()
    today = dt.datetime.now(dt.timezone.utc).strftime('%Y.%m.%d')

    if version:
        if '.' not in version:
            assert re.fullmatch(r'[0-9]+', version), 'Revision must be numeric'
            version = f'{today}.{version}'
        else:
            assert all(
                re.fullmatch(r'[0-9]+', part) for part in version.split('.')
            ), 'Version must be numeric'
    else:
        version = calculate_version(prev_version=get_latest_release_version())

    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f'version={version}\n')
    print(f'version={version}')


if __name__ == '__main__':
    main()

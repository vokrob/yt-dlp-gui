"""
yt-dlp CLI wrapper — subprocess calls instead of Python API
"""

import subprocess
import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional, Callable, List

from . import binary_manager

logger = logging.getLogger(__name__)


def find_ytdlp() -> str:
    """Locate yt-dlp executable. Checks AppData bin first, then PATH."""
    # 1. Check AppData bin (downloaded by binary_manager on first run)
    appdata_exe = binary_manager.get_bin_dir() / 'yt-dlp.exe'
    if appdata_exe.exists():
        return str(appdata_exe)
    # 2. Frozen: next to the GUI exe (legacy/fallback)
    if getattr(sys, 'frozen', False):
        candidate = Path(sys.executable).parent / 'yt-dlp.exe'
        if candidate.exists():
            return str(candidate)
    # 3. PATH
    return 'yt-dlp'


def _ffmpeg_args() -> List[str]:
    loc = binary_manager.get_ffmpeg_location()
    return ['--ffmpeg-location', loc] if loc else []


def extract_info(url: str, extra_args: List[str] = None, timeout: int = 30) -> Optional[dict]:
    """Run yt-dlp --dump-json and return parsed info. Returns None on failure."""
    cmd = [find_ytdlp(), '--dump-json', '--no-playlist', '--no-warnings', '--quiet',
           '--no-check-certificate']
    cmd.extend(_ffmpeg_args())
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            logger.warning(f"yt-dlp extract_info failed: {result.stderr[:300]}")
            return None
        return json.loads(result.stdout) if result.stdout.strip() else None
    except subprocess.TimeoutExpired:
        logger.warning(f"yt-dlp extract_info timed out for {url}")
        return None
    except Exception as e:
        logger.warning(f"yt-dlp extract_info error: {e}")
        return None


def extract_info_flat(url: str, extra_args: List[str] = None) -> Optional[dict]:
    """Extract flat info (for playlists)."""
    args = ['--extract-flat'] + (extra_args or [])
    return extract_info(url, extra_args=args, timeout=15)


def get_formats(url: str, extra_args: List[str] = None) -> Optional[list]:
    """Get available formats for a URL."""
    info = extract_info(url, extra_args)
    return info.get('formats', []) if info else None


def is_playlist(url: str, extra_args: List[str] = None) -> bool:
    """Check if URL is a playlist."""
    info = extract_info_flat(url, extra_args)
    return info is not None and info.get('_type') == 'playlist'


def get_playlist_info(url: str, extra_args: List[str] = None) -> dict:
    """Get playlist metadata."""
    info = extract_info_flat(url, extra_args)
    if info and info.get('_type') == 'playlist':
        return {
            'title': info.get('title', 'Unknown Playlist'),
            'uploader': info.get('uploader', 'Unknown'),
            'entry_count': len(info.get('entries', [])),
            'entries': info.get('entries', []),
        }
    return {}


_PROGRESS_RE = re.compile(r'\[download\]\s+([\d.]+)%')


def _parse_progress(line: str) -> Optional[dict]:
    """Parse yt-dlp progress line. Returns None if no progress found."""
    m = _PROGRESS_RE.search(line)
    if m:
        return {'percent': float(m.group(1)), 'speed': '', 'eta': ''}
    return None


def download(url: str, output_path: str, format_spec: str,
             extra_args: List[str] = None,
             progress_callback: Callable = None) -> int:
    """
    Download video using yt-dlp subprocess.
    Parses stdout for progress updates.
    Returns exit code (0 = success).
    """
    cmd = [find_ytdlp(), '--newline', '--no-warnings',
           '--no-check-certificate',
           '-o', output_path, '-f', format_spec]
    cmd.extend(_ffmpeg_args())
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(url)

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        for raw_line in iter(proc.stdout.readline, b''):
            try:
                line = raw_line.decode('utf-8').strip()
            except UnicodeDecodeError:
                line = raw_line.decode('cp1251', errors='replace').strip()
            if not line:
                continue

            if 'ERROR:' in line:
                logger.error(f"yt-dlp: {line[:300]}")

            progress = _parse_progress(line)
            if progress:
                if progress_callback:
                    progress_callback(progress)

        proc.wait()
        if progress_callback:
            progress_callback({'percent': 100.0 if proc.returncode == 0 else 0})
        return proc.returncode

    except Exception as e:
        logger.error(f"yt-dlp download failed: {e}")
        if progress_callback:
            progress_callback({'error': str(e)})
        return -1


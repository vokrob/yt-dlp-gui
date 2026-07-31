"""
yt-dlp CLI wrapper — subprocess calls instead of Python API
"""

import subprocess
import json
import logging
import re
import sys
import platform
import threading
import requests
from pathlib import Path
from typing import Optional, Callable, List

from . import binary_manager

logger = logging.getLogger(__name__)

# Thread-local storage for last yt-dlp error message
_last_error = threading.local()


def _set_last_error(msg: str):
    _last_error.msg = msg


def get_last_error() -> str:
    """Get the last yt-dlp error message from current thread."""
    return getattr(_last_error, 'msg', '')


def _create_no_window_flag() -> int:
    """Return CREATE_NO_WINDOW flag on Windows, 0 otherwise."""
    if platform.system() == 'Windows':
        return subprocess.CREATE_NO_WINDOW
    return 0


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


def _cmd_str(cmd: List[str]) -> str:
    """Format command list as a shell command string for logging."""
    return ' '.join(f'"{c}"' if ' ' in c else c for c in cmd)


def extract_info(url: str, extra_args: List[str] = None, timeout: int = 30) -> Optional[dict]:
    """Run yt-dlp --dump-json and return parsed info. Returns None on failure."""
    cmd = [find_ytdlp(), '--dump-json', '--no-playlist', '--no-warnings', '--quiet',
           '--no-check-certificate']
    cmd.extend(_ffmpeg_args())
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(url)

    logger.debug(f"Running: {_cmd_str(cmd)}")

    flags = _create_no_window_flag()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                                creationflags=flags)
        if result.returncode != 0:
            msg = result.stderr[:500].strip()
            _set_last_error(msg)
            logger.warning(f"yt-dlp extract_info failed: {msg}")
            logger.debug(f"Full stderr: {result.stderr[:1000]}")
            return None
        _set_last_error('')
        return json.loads(result.stdout) if result.stdout.strip() else None
    except subprocess.TimeoutExpired:
        msg = f"yt-dlp timed out after {timeout}s"
        _set_last_error(msg)
        logger.warning(f"{msg} for {url}")
        return None
    except Exception as e:
        msg = str(e)
        _set_last_error(msg)
        logger.warning(f"yt-dlp extract_info error: {e}")
        return None


def extract_info_flat(url: str, extra_args: List[str] = None) -> Optional[dict]:
    """Extract flat info (for playlists)."""
    args = ['--extract-flat'] + (extra_args or [])
    return extract_info(url, extra_args=args, timeout=15)


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


def extract_title_from_html(url: str) -> Optional[str]:
    """Extract video title directly from YouTube HTML page."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            # Omit Accept-Language to get original video version
            # Don't specify Accept-Encoding to let requests handle it properly
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text

        # Try multiple patterns to extract title with priorities
        patterns = [
            (r'<title>([^<]+)</title>', "HTML title tag", 10),
            (r'<meta name="title" content="([^"]+)"', "meta title", 9),
            (r'<meta property="og:title" content="([^"]+)"', "og:title meta", 9),
            (r'"videoDetails":{"videoId":"[^"]+","title":"([^"]+)"', "videoDetails object", 8),
            (r'<meta name="twitter:title" content="([^"]+)"', "twitter:title", 7),
            (r'"og:title" content="([^"]+)"', "og:title content", 6),
            (r'"title":"([^"]+)"', "JSON title field", 1),
        ]

        found_titles = []

        for pattern, description, priority in patterns:
            try:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    title = match.group(1)
                    # Clean up title
                    title = title.replace('\\u0026', '&').replace('\\', '').replace('\\"', '"')
                    # Remove " - YouTube" suffix if present
                    if title.endswith(' - YouTube'):
                        title = title[:-10]

                    # Skip obviously bad titles
                    if title.lower() in ['download unavailable', 'unavailable', 'error', 'blocked']:
                        continue

                    # Check if it's a valid title (not generic)
                    if title and len(title) > 5 and 'youtube video #' not in title.lower():
                        found_titles.append((priority, description, title))
                        logger.info(f"Found title via {description}: {title}")
            except Exception as e:
                logger.warning(f"Error with pattern {description}: {e}")

        # Sort by priority and return the best one
        if found_titles:
            found_titles.sort(key=lambda x: x[0], reverse=True)
            _, best_desc, best_title = found_titles[0]
            logger.info(f"Selected best title via {best_desc}: {best_title}")
            return best_title

        return None

    except Exception as e:
        logger.warning(f"Failed to extract title from HTML: {e}")
        return None


_PROGRESS_RE = re.compile(
    r'\[download\]\s+(\d+(?:\.\d+)?)%'                       # 1: percent
    r'(?:\s+of\s+~?\s*(\d+(?:\.\d+)?\s*[KMGTP]?i?B))?'      # 2: total size (optional)
    r'(?:\s+at\s+([\d.]+\s*[KMGTP]?i?B/s))?'                 # 3: speed (optional)
    r'(?:\s+ETA\s+(\S+))?'                                    # 4: ETA (optional)
)

_SIZE_UNITS = {
    'B': 1, 'KiB': 1024, 'MiB': 1024**2, 'GiB': 1024**3, 'TiB': 1024**4,
    'KB': 1000, 'MB': 1000**2, 'GB': 1000**3, 'TB': 1000**4,
}


def _parse_size_to_bytes(size_str: str) -> int:
    """Parse a size string like '15.8MiB' to bytes."""
    if not size_str:
        return 0
    m = re.match(r'([\d.]+)\s*([KMGTP]?i?B)', size_str.strip())
    if not m:
        return 0
    value = float(m.group(1))
    unit = m.group(2)
    return int(value * _SIZE_UNITS.get(unit, 1))


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable string"""
    if bytes_value == 0:
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0

    return f"{bytes_value:.1f} PB"


def _parse_progress(line: str) -> Optional[dict]:
    """Parse yt-dlp progress line. Returns None if no progress found."""
    m = _PROGRESS_RE.search(line)
    if not m:
        return None

    result = {'percent': float(m.group(1)), 'speed': '', 'eta': ''}

    total_size_str = m.group(2)
    if total_size_str:
        result['total_bytes'] = _parse_size_to_bytes(total_size_str)

    speed = m.group(3)
    if speed:
        result['speed'] = speed

    eta = m.group(4)
    if eta:
        result['eta'] = eta

    return result


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

    logger.debug(f"Download command: {_cmd_str(cmd)}")
    flags = _create_no_window_flag()
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                creationflags=flags)
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


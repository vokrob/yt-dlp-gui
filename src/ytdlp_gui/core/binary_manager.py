r"""
Binary Manager — downloads yt-dlp.exe and ffmpeg.exe on first run.
Stores binaries in %LOCALAPPDATA%\yt-dlp-gui\bin\
"""

import os
import sys
import urllib.request
import zipfile
import shutil
import logging
import subprocess
import platform
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

YTDLP_EXE_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
YTDLP_NIGHTLY_URL = "https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/yt-dlp.exe"
FFMPEG_ZIP_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def get_bin_dir() -> Path:
    if getattr(sys, 'frozen', False):
        bin_dir = Path(os.environ['LOCALAPPDATA']) / 'yt-dlp-gui' / 'bin'
    else:
        bin_dir = Path(__file__).resolve().parent.parent.parent.parent / 'bin_dev'
    bin_dir.mkdir(parents=True, exist_ok=True)
    return bin_dir


def get_ffmpeg_location() -> Optional[str]:
    ffmpeg = get_bin_dir() / 'ffmpeg.exe'
    return str(ffmpeg.parent) if ffmpeg.exists() else None


def ensure_binaries(progress_callback: Callable[[str, int], None] = None) -> bool:
    bin_dir = get_bin_dir()
    ytdlp_path = bin_dir / 'yt-dlp.exe'
    ffmpeg_path = bin_dir / 'ffmpeg.exe'
    ffprobe_path = bin_dir / 'ffprobe.exe'

    def report(msg, pct):
        if progress_callback:
            progress_callback(msg, pct)
        logger.info("[binaries] %s", msg)

    if not ytdlp_path.exists():
        report("Downloading yt-dlp.exe...", 0)
        try:
            urllib.request.urlretrieve(YTDLP_EXE_URL, ytdlp_path)
            size = ytdlp_path.stat().st_size
            report("yt-dlp.exe downloaded (%d MB)" % (size // 1024 // 1024), 40)
        except Exception as e:
            report("yt-dlp.exe download failed: %s" % e, 0)
            return False
    else:
        report("yt-dlp.exe OK", 40)

    if not ffmpeg_path.exists() or not ffprobe_path.exists():
        report("Downloading FFmpeg...", 45)
        zip_path = bin_dir / 'ffmpeg.zip'
        try:
            urllib.request.urlretrieve(FFMPEG_ZIP_URL, zip_path)
            report("Extracting FFmpeg...", 70)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for member in zf.namelist():
                    name = Path(member).name
                    if name in ('ffmpeg.exe', 'ffprobe.exe'):
                        with zf.open(member) as src, open(bin_dir / name, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                        report("Extracted %s" % name, 80)
            zip_path.unlink()
            report("FFmpeg ready", 90)
        except Exception as e:
            report("FFmpeg download failed: %s" % e, 0)
            return False
    else:
        report("FFmpeg OK", 90)

    report("All binaries ready", 100)
    return True


def update_ytdlp() -> None:
    """Download the latest yt-dlp binary from GitHub (nightly first, then stable)."""
    try:
        exe = get_bin_dir() / 'yt-dlp.exe'
        if not exe.exists():
            return

        tmp = exe.with_suffix('.exe.tmp')
        downloaded = None

        # 1. Try nightly builds (yt-dlp/yt-dlp-nightly-builds)
        logger.info("Downloading latest yt-dlp nightly build...")
        try:
            urllib.request.urlretrieve(YTDLP_NIGHTLY_URL, tmp)
            tmp.replace(exe)
            downloaded = "nightly"
            logger.info("yt-dlp updated to latest nightly build")
        except Exception as e:
            logger.warning("Nightly download failed: %s", e)

        # 2. Fallback to stable (yt-dlp/yt-dlp)
        if not downloaded:
            logger.info("Downloading latest yt-dlp stable build...")
            try:
                urllib.request.urlretrieve(YTDLP_EXE_URL, tmp)
                tmp.replace(exe)
                downloaded = "stable"
                logger.info("yt-dlp updated to latest stable build")
            except Exception as e:
                logger.warning("Stable download failed: %s", e)

        # 3. Last resort: built-in --update
        if not downloaded:
            logger.info("Trying yt-dlp --update...")
            flags = subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            result = subprocess.run(
                [str(exe), '--update'],
                capture_output=True, text=True, timeout=60,
                creationflags=flags
            )
            if result.returncode == 0:
                msg = result.stdout.strip() or result.stderr.strip() or "updated"
                logger.info("yt-dlp auto-update: %s", msg)
                downloaded = "update"
            else:
                logger.warning("yt-dlp --update failed: %s", result.stderr.strip()[:200])

        if not downloaded:
            logger.warning("All yt-dlp update methods failed")
            return

        # Clean up ffmpeg zip if present
        zip_path = get_bin_dir() / 'ffmpeg.zip'
        if zip_path.exists():
            zip_path.unlink()

    except Exception as e:
        logger.debug("yt-dlp update skipped: %s", e)

r"""
Binary Manager - downloads yt-dlp.exe and ffmpeg.exe on first run.
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
FFMPEG_ZIP_BACKUP_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-win64-gpl.zip"
YTDLP_PENDING_NAME = "yt-dlp-pending.exe"


def _download_file(url: str, dest: Path, timeout: int = 60) -> None:
    """Download a file with a per-request timeout. Raises on failure."""
    with urllib.request.urlopen(url, timeout=timeout) as resp, open(dest, 'wb') as f:
        shutil.copyfileobj(resp, f)


def _check_executable(path: Path, version_flag: str = '-version') -> bool:
    """Verify a binary actually runs (detects corrupt or incompatible builds).

    On Windows, suppress loader error dialogs (e.g. "entry point not found")
    so incompatible builds fail silently instead of scaring the user.
    """
    flags = subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
    if platform.system() == 'Windows':
        try:
            import ctypes
            # SEM_FAILCRITICALERRORS | SEM_NOOPENFILEERRORBOX - inherited by children
            ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x8000)
        except Exception:
            pass
    try:
        result = subprocess.run(
            [str(path), version_flag],
            capture_output=True, timeout=30, creationflags=flags
        )
        return result.returncode == 0
    except Exception:
        return False


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


def _validate_ytdlp(path: Path) -> None:
    """Raise if a downloaded yt-dlp binary is truncated or cannot run."""
    size = path.stat().st_size
    if size < 1_000_000:
        raise RuntimeError(f"{path.name} is truncated ({size} bytes)")
    if not _check_executable(path, version_flag='--version'):
        raise RuntimeError(f"{path.name} does not run on this system")


def _download_ytdlp(url: str, pending_path: Path) -> None:
    """Download yt-dlp to a pending file and validate it before use."""
    tmp_path = pending_path.with_name(pending_path.name + '.tmp')
    try:
        _download_file(url, tmp_path)
        tmp_path.replace(pending_path)
        _validate_ytdlp(pending_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        pending_path.unlink(missing_ok=True)
        raise


def apply_pending_update() -> bool:
    """Apply yt-dlp-pending.exe if present.

    Runs on startup before any yt-dlp process is launched, so replacing the
    executable is safe. If the file is still in use, it is kept for the next
    launch.
    """
    bin_dir = get_bin_dir()
    exe = bin_dir / 'yt-dlp.exe'
    pending = bin_dir / YTDLP_PENDING_NAME
    if not pending.exists():
        return False

    try:
        _validate_ytdlp(pending)
    except Exception as e:
        logger.warning("Discarding invalid pending yt-dlp update: %s", e)
        pending.unlink(missing_ok=True)
        return False

    try:
        os.replace(pending, exe)
        logger.info("Applied pending yt-dlp update")
        return True
    except OSError:
        logger.info("Pending yt-dlp update is locked; will retry on next launch")
        return False


def ensure_binaries(progress_callback: Callable[[str, int], None] = None) -> bool:
    bin_dir = get_bin_dir()
    ytdlp_path = bin_dir / 'yt-dlp.exe'
    ffmpeg_path = bin_dir / 'ffmpeg.exe'
    ffprobe_path = bin_dir / 'ffprobe.exe'

    def report(msg, pct):
        if progress_callback:
            progress_callback(msg, pct)
        logger.info("[binaries] %s", msg)

    apply_pending_update()

    if not ytdlp_path.exists():
        report("Downloading yt-dlp.exe...", 0)
        try:
            _download_file(YTDLP_EXE_URL, ytdlp_path)
            size = ytdlp_path.stat().st_size
            if size < 1_000_000:
                raise RuntimeError(f"yt-dlp.exe is truncated ({size} bytes)")
            if not _check_executable(ytdlp_path, version_flag='--version'):
                raise RuntimeError("yt-dlp.exe does not run on this system")
            report("yt-dlp.exe downloaded (%d MB)" % (size // 1024 // 1024), 40)
        except Exception as e:
            ytdlp_path.unlink(missing_ok=True)
            report("yt-dlp.exe download failed: %s" % e, 0)
            return False
    else:
        report("yt-dlp.exe OK", 40)

    if not ffmpeg_path.exists() or not ffprobe_path.exists():
        report("Downloading FFmpeg...", 45)
        zip_path = bin_dir / 'ffmpeg.zip'
        created = []
        extracted = False
        # GitHub (BtbN) first: reliable CDN, fast in most regions;
        # gyan.dev (static build, runs on old Windows) is the fallback.
        # BtbN's recent builds require Windows 10 2004+ (build 19041);
        # on older Windows skip straight to gyan.dev to save a download and
        # avoid a loader error dialog when the incompatible build is validated.
        sources = [("GitHub (BtbN)", FFMPEG_ZIP_BACKUP_URL)]
        if platform.system() == 'Windows' and sys.getwindowsversion().build < 19041:
            sources = []
        sources.append(("gyan.dev", FFMPEG_ZIP_URL))
        for source, url in sources:
            try:
                report("Downloading FFmpeg from %s..." % source, 45)
                _download_file(url, zip_path)
                zip_size = zip_path.stat().st_size
                if zip_size < 20_000_000:
                    raise RuntimeError(f"ffmpeg.zip is truncated ({zip_size} bytes)")
                report("Extracting FFmpeg...", 70)
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    for member in zf.namelist():
                        name = Path(member).name
                        if name in ('ffmpeg.exe', 'ffprobe.exe'):
                            with zf.open(member) as src, open(bin_dir / name, 'wb') as dst:
                                shutil.copyfileobj(src, dst)
                            created.append(bin_dir / name)
                            report("Extracted %s" % name, 80)
                zip_path.unlink()
                for path in created:
                    if path.stat().st_size < 1_000_000:
                        raise RuntimeError(
                            f"{path.name} is truncated ({path.stat().st_size} bytes)")
                if not _check_executable(ffmpeg_path):
                    raise RuntimeError("ffmpeg.exe does not run on this system")
                report("FFmpeg ready", 90)
                extracted = True
                break
            except Exception as e:
                logger.warning("FFmpeg download failed from %s: %s", source, e)
                zip_path.unlink(missing_ok=True)
                for path in created:
                    path.unlink(missing_ok=True)
                created.clear()
        if not extracted:
            report("FFmpeg download failed", 0)
            return False
    else:
        report("FFmpeg OK", 90)

    report("All binaries ready", 100)
    return True


def update_ytdlp(is_busy: Optional[Callable[[], bool]] = None) -> None:
    """Download the latest yt-dlp binary for the next launch.

    Updates are skipped while downloads are active. The new binary is kept as
    yt-dlp-pending.exe and applied on the next startup, before any yt-dlp
    process runs.
    """
    try:
        if is_busy and is_busy():
            logger.info("Skipping yt-dlp update: downloads are active")
            return

        bin_dir = get_bin_dir()
        exe = bin_dir / 'yt-dlp.exe'
        if not exe.exists():
            return

        pending = bin_dir / YTDLP_PENDING_NAME
        pending.with_name(pending.name + '.tmp').unlink(missing_ok=True)

        downloaded = None
        for source, url in (("nightly", YTDLP_NIGHTLY_URL), ("stable", YTDLP_EXE_URL)):
            logger.info("Downloading latest yt-dlp %s build...", source)
            try:
                _download_ytdlp(url, pending)
                downloaded = source
                logger.info("yt-dlp %s build downloaded and verified", source)
                break
            except Exception as e:
                logger.warning("%s yt-dlp download failed: %s", source, e)

        if not downloaded:
            logger.warning("All yt-dlp update downloads failed")
            return

        logger.info("yt-dlp update saved as %s and will be applied on next launch", pending.name)

        # Clean up ffmpeg zip if present
        zip_path = bin_dir / 'ffmpeg.zip'
        if zip_path.exists():
            zip_path.unlink()

    except Exception as e:
        logger.debug("yt-dlp update skipped: %s", e)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YT-DLP GUI - Video & Audio Downloader
"""

import sys
import os
import logging
import threading
from pathlib import Path

# Set to True right before the GUI mainloop starts. The watchdog timer below
# checks it so a hang during startup (e.g. stuck filesystem I/O or Tk init)
# shows a native message box instead of a silent zombie process.
STARTUP_COMPLETE = False
STARTUP_TIMEOUT_S = 15

def setup_paths():
    """Setup module paths and bundled binaries"""
    if getattr(sys, 'frozen', False):
        app_path = Path(sys.executable).parent
        meipass = Path(sys._MEIPASS)
        os.environ['PATH'] = str(meipass) + os.pathsep + os.environ.get('PATH', '')
    else:
        app_path = Path(__file__).parent
        for cachedir in [app_path / 'ffmpeg_cache', app_path / 'deno_cache']:
            if cachedir.exists():
                os.environ['PATH'] = str(cachedir) + os.pathsep + os.environ.get('PATH', '')

    src_path = app_path / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
    else:
        sys.path.insert(0, str(app_path))

setup_paths()

try:
    from ytdlp_gui.gui.main_window import YTDLPGUIApp
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def watchdog():
    """Show a native message box if the GUI did not appear in time.

    Uses Windows MessageBoxW (via ctypes) so it works even from a background
    thread and without a Tk window - which is exactly the case it guards against.
    """
    global STARTUP_COMPLETE
    if STARTUP_COMPLETE:
        return
    log_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'yt-dlp-gui', 'logs')
    message = (
        "The window did not appear after {} seconds.\n\n"
        "The app may be stuck during startup (often a slow or redirected AppData folder, "
        "OneDrive, network drive, or an antivirus).\n\n"
        "Logs: {}\n\n"
        "You can kill it from Task Manager."
    ).format(STARTUP_TIMEOUT_S, log_dir)
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            None, message, "yt-dlp GUI - startup problem",
            0x10 | 0x1000  # MB_ICONERROR | MB_SYSTEMMODAL
        )
    except Exception:
        pass


def main():
    """Start the application"""
    try:
        # Unified logging (AppData\yt-dlp-gui\logs) - must run before bootstrap
        from ytdlp_gui.utils.logger import get_log_manager
        get_log_manager()

        # Download missing binaries (yt-dlp, ffmpeg) before starting the GUI
        from ytdlp_gui.main import _ensure_binaries
        if not _ensure_binaries():
            sys.exit(1)

        global STARTUP_COMPLETE
        threading.Timer(STARTUP_TIMEOUT_S, watchdog).start()

        app = YTDLPGUIApp()

        # Auto-update yt-dlp in the background so a slow or blocked GitHub
        # doesn't leave the process running with no visible window at startup.
        def _update_ytdlp():
            try:
                from ytdlp_gui.core import binary_manager
                binary_manager.update_ytdlp()
            except Exception:
                pass

        threading.Thread(target=_update_ytdlp, daemon=True).start()

        STARTUP_COMPLETE = True
        app.run()
    except Exception as e:
        logging.error(f"App failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

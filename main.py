#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YT-DLP GUI - Video & Audio Downloader
"""

import sys
import os
import logging
from pathlib import Path

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

def main():
    """Start the application"""
    try:
        # Unified logging (AppData\yt-dlp-gui\logs) — must run before bootstrap
        from ytdlp_gui.utils.logger import get_log_manager
        get_log_manager()

        # Download missing binaries (yt-dlp, ffmpeg) before starting the GUI
        from ytdlp_gui.main import _ensure_binaries
        if not _ensure_binaries():
            sys.exit(1)

        # Auto-update yt-dlp before launching GUI (synchronous)
        try:
            from ytdlp_gui.core import binary_manager
            binary_manager.update_ytdlp()
        except Exception:
            pass

        app = YTDLPGUIApp()
        app.run()
    except Exception as e:
        logging.error(f"App failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

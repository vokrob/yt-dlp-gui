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
    """Setup module paths"""
    if getattr(sys, 'frozen', False):
        app_path = Path(sys.executable).parent
    else:
        app_path = Path(__file__).parent

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

def setup_logging():
    """Setup basic logging"""
    log_dir = Path.home() / ".yt-dlp-gui" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """Start the application"""
    try:
        setup_logging()
        app = YTDLPGUIApp()
        app.run()
    except Exception as e:
        logging.error(f"App failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

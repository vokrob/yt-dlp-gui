# -*- coding: utf-8 -*-
"""
Main Entry Point
Author: vokrob (Данил Борков)
Date: 18.07.2025
"""

import sys
import logging
from pathlib import Path

from .gui.main_window import YTDLPGUIApp

def setup_logging():
    """Setup logging"""
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
    """Main entry point"""
    try:
        setup_logging()
        app = YTDLPGUIApp()
        app.run()
    except Exception as e:
        logging.error(f"Failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

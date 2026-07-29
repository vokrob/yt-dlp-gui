# -*- coding: utf-8 -*-
"""
Main Entry Point
Author: vokrob (Данил Борков)
Date: 18.07.2025
"""

import sys
import logging
import threading
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


def _ensure_binaries():
    """Download missing binaries with a simple splash window."""
    try:
        from .core import binary_manager
        bin_dir = binary_manager.get_bin_dir()
        ytdlp_ok = (bin_dir / 'yt-dlp.exe').exists()
        ffmpeg_ok = (bin_dir / 'ffmpeg.exe').exists() and (bin_dir / 'ffprobe.exe').exists()

        if ytdlp_ok and ffmpeg_ok:
            return

        import tkinter as tk
        from tkinter import ttk, messagebox

        root = tk.Tk()
        root.title("YT-DLP GUI")
        root.geometry("420x140")
        root.resizable(False, False)
        root.configure(bg='#1a1a2e')

        try:
            root.iconbitmap(Path(__file__).parent.parent / 'assets' / 'icon.ico')
        except:
            pass

        tk.Label(root, text="First launch — downloading components...",
                 fg='#e0e0e0', bg='#1a1a2e', font=('Segoe UI', 12)).pack(pady=(20, 5))
        status = tk.Label(root, text="", fg='#a0a0a0', bg='#1a1a2e', font=('Segoe UI', 9))
        status.pack(pady=(0, 10))
        progress = ttk.Progressbar(root, mode='determinate', length=350)
        progress.pack(pady=(0, 15))

        result = [False]

        def update_status(msg, pct):
            status.config(text=msg)
            progress['value'] = pct
            root.update()

        def do_download():
            result[0] = binary_manager.ensure_binaries(progress_callback=update_status)
            root.after(0, root.destroy)

        threading.Thread(target=do_download, daemon=True).start()
        root.mainloop()

        if not result[0]:
            messagebox.showerror(
                "Download failed",
                "Could not download required components.\n"
                "Check your internet connection and try again."
            )
            return False
    except Exception as e:
        logging.error("Binary download failed: %s", e)
        return False
    return True


def main():
    """Main entry point"""
    try:
        setup_logging()
        if not _ensure_binaries():
            sys.exit(1)

        # Auto-update yt-dlp in background after launch
        def _auto_update():
            try:
                from .core import binary_manager
                binary_manager.update_ytdlp()
            except Exception:
                pass
        threading.Thread(target=_auto_update, daemon=True).start()

        app = YTDLPGUIApp()
        app.run()
    except Exception as e:
        logging.error("Failed to start: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

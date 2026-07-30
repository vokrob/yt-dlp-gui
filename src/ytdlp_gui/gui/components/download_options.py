# -*- coding: utf-8 -*-
"""
Download Options Component
Author: vokrob
Date: 18.07.2025
"""

import customtkinter as ctk
import tkinter as tk
import logging
import threading
from pathlib import Path
from typing import Dict, Optional, Callable, List
from ytdlp_gui.core.format_detector import FormatDetector
from tkinter import filedialog

class DownloadOptionsFrame(ctk.CTkFrame):
    """Frame for download options - format and quality (saves to Desktop by default)"""

    def __init__(self, parent, settings_manager, on_download_click: Optional[Callable] = None):
        super().__init__(parent, fg_color="transparent")
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager
        self.on_download_click = on_download_click

        # Format detection
        self.format_detector = FormatDetector(settings_manager)
        self.available_qualities = []
        self.current_url = None
        self.best_quality = None
        self._output_path = None

        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)

        # Clean, modern options frame
        options_frame = ctk.CTkFrame(self, corner_radius=12)
        options_frame.grid(row=0, column=0, sticky="ew", pady=10)
        options_frame.grid_columnconfigure(0, weight=1)

        # Centered controls layout - compact and balanced
        controls_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=0, pady=(15, 15))

        # Format Selection - centered
        self.format_var = ctk.StringVar(value="Video")
        self.format_selector = ctk.CTkSegmentedButton(
            controls_frame,
            values=["Video", "Audio"],
            variable=self.format_var,
            command=self.on_format_change,
            height=32,
            width=160
        )
        self.format_selector.grid(row=0, column=0, padx=(0, 15))

        # Quality Selection - close to format
        self.quality_var = ctk.StringVar(value="Loading...")
        self.quality_dropdown = ctk.CTkComboBox(
            controls_frame,
            variable=self.quality_var,
            values=["Loading..."],
            command=self.on_quality_change,
            state="readonly",
            height=32,
            width=140
        )
        self.quality_dropdown.grid(row=0, column=1)

        # Save path row — centered under options
        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.grid(row=1, column=0, pady=(0, 10))

        path_label = ctk.CTkLabel(path_frame, text="Save to:", font=ctk.CTkFont(size=12))
        path_label.grid(row=0, column=0, padx=(0, 8))

        self.path_entry = ctk.CTkEntry(path_frame, height=32, width=250)
        self.path_entry.grid(row=0, column=1, padx=(0, 8))
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, self.settings_manager.get_output_directory())

        self.browse_btn = ctk.CTkButton(
            path_frame,
            text="Browse...",
            command=self.browse_directory,
            height=32,
            width=100
        )
        self.browse_btn.grid(row=0, column=2)

    def browse_directory(self):
        """Open directory browser dialog"""
        initial = self._output_path or self.settings_manager.get_output_directory()
        selected = filedialog.askdirectory(
            title="Select Download Directory",
            initialdir=initial
        )
        if selected:
            self._output_path = selected
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, selected)

    def load_video_qualities(self, url: str):
        """Load available qualities for the video URL"""
        if url == self.current_url and self.available_qualities:
            self.logger.info(f"Using cached qualities for URL: {url}")
            self.after(0, self._update_quality_dropdown)
            return

        self.current_url = url
        self.quality_var.set("Loading...")
        self.quality_dropdown.configure(values=["Loading..."])

        # Load qualities in background thread
        threading.Thread(target=self._fetch_video_qualities, args=(url,), daemon=True).start()

    def _fetch_video_qualities(self, url: str):
        """Fetch available video qualities (runs in background thread)"""
        try:
            video_formats, _, _ = self.format_detector.get_available_formats(url)

            # Extract unique resolutions from video formats
            resolutions = set()
            for fmt in video_formats:
                if fmt.vcodec != 'none':  # Only video formats
                    # Extract height from resolution
                    if 'x' in fmt.resolution:
                        height = fmt.resolution.split('x')[1]
                        if height.isdigit():
                            resolutions.add(int(height))
                    elif fmt.resolution.endswith('p'):
                        height = fmt.resolution[:-1]
                        if height.isdigit():
                            resolutions.add(int(height))

            # Convert to sorted list of quality options
            available_heights = sorted(resolutions, reverse=True)
            quality_options = []

            for height in available_heights:
                if height >= 2160:
                    quality_options.append("2160p (4K)")
                elif height >= 1440:
                    quality_options.append("1440p (2K)")
                elif height >= 1080:
                    quality_options.append("1080p")
                elif height >= 720:
                    quality_options.append("720p")
                elif height >= 480:
                    quality_options.append("480p")
                elif height >= 360:
                    quality_options.append("360p")
                elif height >= 240:
                    quality_options.append("240p")
                elif height >= 144:
                    quality_options.append("144p")

            # Remove duplicates while preserving order
            seen = set()
            unique_qualities = []
            for quality in quality_options:
                if quality not in seen:
                    unique_qualities.append(quality)
                    seen.add(quality)

            self.available_qualities = unique_qualities
            self.best_quality = unique_qualities[0] if unique_qualities else "720p"

            # Update UI on main thread
            self.after(0, self._update_quality_dropdown)

        except Exception as e:
            self.logger.error(f"Failed to fetch video qualities: {e}")
            # Fallback to default qualities
            self.available_qualities = ["1080p", "720p", "480p", "360p"]
            self.best_quality = "1080p"
            self.after(0, self._update_quality_dropdown)

    def _update_quality_dropdown(self):
        """Update quality dropdown with available options (runs on main thread)"""
        if self.available_qualities:
            self.quality_dropdown.configure(values=self.available_qualities)
            # Set to best available quality
            self.quality_var.set(self.best_quality)
        else:
            # Fallback
            self.quality_dropdown.configure(values=["720p", "480p", "360p"])
            self.quality_var.set("720p")

    def on_format_change(self, value):
        """Handle format change"""
        # Update the variable if called manually
        if self.format_var.get() != value:
            self.format_var.set(value)

        # Show/hide quality selection based on type
        if value == "Audio":
            self.quality_dropdown.grid_remove()
        else:
            self.quality_dropdown.grid(row=0, column=1)
            
    def on_quality_change(self, value):
        """Handle quality change"""
        pass  # Quality is handled when getting format info
        

            
    def start_download(self):
        """Start download with current options"""
        if self.on_download_click:
            format_info = self.get_format_info()

            output_path = self._output_path or self.settings_manager.get_output_directory()

            self.on_download_click(format_info, output_path)
            
    def get_format_info(self) -> Dict:
        """Get current format information"""
        format_info = {
            'audio_only': self.format_var.get() == "Audio",
            'quality': self.quality_var.get() if self.format_var.get() == "Video" else None
        }
        
        # Use correct selectors from FORMAT_SELECTOR
        if format_info['audio_only']:
            format_info['format_id'] = 'bestaudio/best'
            self.logger.info(f"Audio format selected: {format_info['format_id']}")
        else:
            quality = format_info['quality']
            self.logger.info(f"Video quality selected: {quality}")

            # Selectors based on bestvideo+bestaudio
            if quality == "Best":
                format_info['format_id'] = 'bestvideo+bestaudio/best'
            else:
                # Extract height from quality string
                import re
                height_match = re.search(r'(\d+)p', quality) if quality else None
                height = int(height_match.group(1)) if height_match else None

                if height:
                    # Selectors based on bestvideo+bestaudio with quality limit
                    format_info['format_id'] = f'bestvideo[height<={height}]+bestaudio/bestvideo+bestaudio/best'
                else:
                    # Fallback to best quality
                    format_info['format_id'] = 'bestvideo+bestaudio/best'

            self.logger.info(f"Generated format_id: {format_info['format_id']}")

        return format_info
        
    def set_format(self, format_info: Dict):
        """Set the format selection"""
        if format_info.get('audio_only', False):
            self.format_var.set("Audio")
            self.on_format_change("Audio")
        else:
            self.format_var.set("Video")
            self.on_format_change("Video")

        if 'quality' in format_info and self.format_var.get() == "Video":
            self.quality_var.set(format_info['quality'])
            
    def get_output_path(self) -> str:
        """Get current output path"""
        return self.settings_manager.get_output_directory()

    def set_output_path(self, path: str):
        """Set output path in settings"""
        self.settings_manager.set('output_directory', path)
        self.settings_manager.save_settings()

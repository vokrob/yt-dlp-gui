# -*- coding: utf-8 -*-
"""
Format Selector Component
Author: vokrob (Данил Борков)
Date: 18.07.2025
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable, Dict, List, Optional
import threading

class FormatSelectorFrame(ctk.CTkFrame):
    """Frame for selecting video/audio formats"""
    
    def __init__(self, parent, on_format_change: Callable = None):
        super().__init__(parent)
        
        self.on_format_change = on_format_change
        self.available_formats = []
        self.current_url = ""
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Format Selection",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")
        
        # Download Type Selection
        type_label = ctk.CTkLabel(self, text="Type:")
        type_label.grid(row=1, column=0, padx=(20, 10), pady=5, sticky="w")
        
        self.type_var = ctk.StringVar(value="video")
        self.type_selector = ctk.CTkSegmentedButton(
            self,
            values=["video", "audio"],
            variable=self.type_var,
            command=self.on_type_change
        )
        self.type_selector.grid(row=1, column=1, padx=(0, 20), pady=5, sticky="ew")
        
        # Quality Selection
        self.quality_label = ctk.CTkLabel(self, text="Quality:")
        self.quality_label.grid(row=2, column=0, padx=(20, 10), pady=5, sticky="w")

        self.quality_var = ctk.StringVar(value="2160p (4K)")
        self.quality_dropdown = ctk.CTkComboBox(
            self,
            variable=self.quality_var,
            values=["Best", "2160p (4K)", "1440p (2K)", "1080p", "720p", "480p", "360p", "240p", "144p"],
            command=self.on_quality_change,
            state="readonly"
        )
        self.quality_dropdown.grid(row=2, column=1, padx=(0, 20), pady=(5, 20), sticky="ew")
        

    def on_type_change(self, value):
        """Handle download type change"""
        # Update the variable if called manually
        if self.type_var.get() != value:
            self.type_var.set(value)

        # Show/hide quality selection based on type
        if value == "audio":
            # Hide quality selection for audio
            self.quality_label.grid_remove()
            self.quality_dropdown.grid_remove()
        else:
            # Show quality selection for video
            self.quality_label.grid(row=2, column=0, padx=(20, 10), pady=5, sticky="w")
            self.quality_dropdown.grid(row=2, column=1, padx=(0, 20), pady=(5, 20), sticky="ew")

        self.notify_format_change()
            
    def on_quality_change(self, value):
        """Handle quality selection change"""
        self.notify_format_change()
        
    def notify_format_change(self):
        """Notify parent of format change"""
        if self.on_format_change:
            format_info = self.get_selected_format()
            self.on_format_change(format_info)
            
    def get_selected_format(self) -> Dict:
        """Get the currently selected format information"""
        is_audio = self.type_var.get() == "audio"
        quality = self.quality_var.get()

        # AGGRESSIVE DIAGNOSTICS
        print(f"FORMAT_SELECTOR DEBUG:")
        print(f"   type_var.get() = {self.type_var.get()}")
        print(f"   quality_var.get() = {quality}")
        print(f"   is_audio = {is_audio}")

        format_info = {
            'type': self.type_var.get(),
            'quality': quality,
            'audio_only': is_audio,
        }

        if is_audio:
            format_info['format_id'] = 'bestaudio/best'
        else:
            # БЫСТРЫЕ СЕЛЕКТОРЫ - ПРИОРИТЕТ ГОТОВЫМ MP4
            if quality == "Best":
                # Приоритет готовым MP4, потом FFmpeg объединение
                format_info['format_id'] = 'best[ext=mp4]/bestvideo+bestaudio/best'
            else:
                # Извлекаем высоту из строки качества (например, "1080p" -> 1080)
                height = self.get_quality_height(quality)
                if height:
                    # ИСПРАВЛЕНИЕ ДЛЯ НИЗКИХ КАЧЕСТВ: 480p и ниже - правильные селекторы
                    if height <= 480:
                        # Для низких качеств сначала пробуем готовые файлы, потом объединение с H.264
                        # Приоритет H.264 кодеку для избежания серого фильтра
                        format_info['format_id'] = f'best[height<={height}][ext=mp4][vcodec!=none][acodec!=none]/bestvideo[height<={height}][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}]'
                        print(f"   📱 {height}p → Приоритет H.264 кодеку (избегаем серый фильтр)")
                    else:
                        # Для высоких качеств - приоритет готовым MP4, потом FFmpeg объединение
                        format_info['format_id'] = f'best[height<={height}][ext=mp4]/bestvideo[height<={height}]+bestaudio/best'
                else:
                    # Fallback на лучшее качество
                    format_info['format_id'] = 'best[ext=mp4]/bestvideo+bestaudio/best'

        # ДИАГНОСТИКА РЕЗУЛЬТАТА
        print(f"FORMAT_SELECTOR RESULT:")
        print(f"   Generated format_id = {format_info['format_id']}")
        print(f"   Final format_info = {format_info}")

        return format_info
        
    def set_format(self, format_info: Dict):
        """Set the format selection"""
        if format_info.get('audio_only', False):
            self.type_var.set("audio")
            self.on_type_change("audio")
        else:
            self.type_var.set("video")
            self.on_type_change("video")

        if 'quality' in format_info and self.type_var.get() == "video":
            self.quality_var.set(format_info['quality'])
            
    def update_available_formats(self, url: str, formats: List = None):
        """Update available formats for a URL"""
        self.current_url = url
        
        if formats:
            self.available_formats = formats
            # Could update dropdown options based on available formats
            # For now, we'll keep the standard options
            
    def get_quality_height(self, quality: str) -> Optional[int]:
        """Extract height value from quality string"""
        if quality == "Best":
            return None  # No specific height limit

        # Extract number from quality string (e.g., "1080p" -> 1080)
        import re
        match = re.search(r'(\d+)p', quality)
        if match:
            return int(match.group(1))
        return None

    def get_format_string(self) -> str:
        """Get the yt-dlp format string"""
        format_info = self.get_selected_format()

        if format_info['audio_only']:
            return 'bestaudio/best'
        else:
            return format_info['format_id']
            
    def reset_to_defaults(self):
        """Reset to default format selection"""
        self.type_var.set("video")
        self.quality_var.set("2160p (4K)")
        self.on_type_change("video")

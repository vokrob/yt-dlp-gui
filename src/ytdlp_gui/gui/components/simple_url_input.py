# -*- coding: utf-8 -*-
"""
URL Input Component
Author: vokrob
Date: 18.07.2025
"""

import customtkinter as ctk
import tkinter as tk
import threading
import logging
import re
import sys
from pathlib import Path
from typing import Optional, Callable
from PIL import Image

class SimpleURLInputFrame(ctk.CTkFrame):
    """URL input frame"""

    def __init__(self, parent, on_url_submit: Optional[Callable] = None):
        super().__init__(parent, fg_color="transparent")
        self.logger = logging.getLogger(__name__)
        self.on_url_submit = on_url_submit
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="").grid(row=0, column=0)

        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=1, column=0, padx=50, pady=50)
        content_frame.grid_columnconfigure(0, weight=1)

        self.logo_image = self._load_logo_image()
        if self.logo_image:
            logo_label = ctk.CTkLabel(content_frame, image=self.logo_image, text="")
            logo_label.grid(row=0, column=0, pady=(40, 10))

        title_label = ctk.CTkLabel(
            content_frame,
            text="yt-dlp GUI",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.grid(row=1, column=0, padx=40, pady=(0, 20))

        input_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        input_frame.grid(row=2, column=0, sticky="ew", padx=40, pady=(0, 20))
        input_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter video URL",
            height=50,
            font=ctk.CTkFont(size=14),
            width=500
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.url_entry.bind("<KeyRelease>", self.on_url_entry_change)
        self.url_entry.bind("<Return>", self.on_enter_pressed)

        # Paste support - catch Ctrl+V by physical keycode (works on any layout)
        self.url_entry.bind("<KeyPress>", self._on_key_press)
        self.url_entry.bind("<Button-2>", self.on_paste)
        self.url_entry.bind("<Button-3>", self.show_context_menu)
        
        # Continue Button
        self.continue_btn = ctk.CTkButton(
            input_frame,
            text="Continue",
            width=150,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.submit_url,
            state="disabled"
        )
        self.continue_btn.grid(row=1, column=0, pady=(10, 0))
        
        # Status Label
        self.status_label = ctk.CTkLabel(
            content_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.grid(row=3, column=0, padx=40, pady=(0, 40))
        
        # Empty space below
        ctk.CTkLabel(self, text="").grid(row=2, column=0)
        
        # Focus on URL entry
        self.after(100, lambda: self.url_entry.focus())

    def _load_logo_image(self):
        """Load the app logo shown above the title."""
        try:
            if getattr(sys, "frozen", False):
                logo_path = Path(sys._MEIPASS) / "assets" / "logo.png"
            else:
                logo_path = Path(__file__).resolve().parents[4] / "assets" / "logo.png"

            if not logo_path.exists():
                self.logger.warning(f"Logo not found: {logo_path}")
                return None

            image = Image.open(logo_path)
            return ctk.CTkImage(light_image=image, dark_image=image, size=(96, 96))
        except Exception as e:
            self.logger.warning(f"Failed to load logo: {e}")
            return None

    def on_url_entry_change(self, event=None):
        """Handle URL entry changes"""
        url = self.url_entry.get().strip()
        
        if url:
            # Validate URL in a separate thread to avoid blocking UI
            threading.Thread(target=self.validate_url, args=(url,), daemon=True).start()
        else:
            self.update_status("", is_valid=False)
            
    def validate_url(self, url: str):
        """Validate URL"""
        try:
            url_pattern = re.compile(r'^https?://\S+', re.IGNORECASE)
            if url_pattern.match(url):
                self.update_status("", is_valid=True, color="gray")
            else:
                self.update_status("", is_valid=False, color="gray")
        except Exception as e:
            self.logger.error(f"URL validation error: {e}")
            self.update_status("", is_valid=False, color="gray")
            
    def update_status(self, message: str, is_valid: bool, color: str = "gray"):
        """Update status"""
        def update():
            self.status_label.configure(text=message, text_color=color)
            self.continue_btn.configure(state="normal" if is_valid else "disabled")
        self.after(0, update)
        
    def _on_key_press(self, event):
        """Handle Ctrl shortcuts by physical keycode (same on all keyboard layouts)"""
        if not (event.state & 0x4):
            return None
        if event.keycode == 65:  # Physical A key + Ctrl
            self.url_entry.select_range(0, "end")
            self.url_entry.icursor("end")
            return "break"
        if event.keycode == 86:  # Physical V key + Ctrl
            return self.on_paste()
        return None

    def submit_url(self):
        """Submit the URL"""
        url = self.url_entry.get().strip()
        if url and self.on_url_submit:
            self.on_url_submit(url)
            
    def on_paste(self, event=None):
        """Handle paste"""
        try:
            clipboard_content = self.url_entry.clipboard_get()
            if clipboard_content and clipboard_content.strip():
                self.url_entry.delete(0, 'end')
                self.url_entry.insert(0, clipboard_content.strip())
                self.on_url_entry_change()
                return "break"
        except:
            pass
        return None

    def show_context_menu(self, event):
        """Show context menu"""
        try:
            import tkinter as tk
            context_menu = tk.Menu(self, tearoff=0)
            context_menu.add_command(label="Paste URL", command=self.on_paste)
            context_menu.add_command(label="Clear", command=lambda: self.url_entry.delete(0, 'end'))
            context_menu.tk_popup(event.x_root, event.y_root)
        except:
            pass

    def on_enter_pressed(self, event=None):
        """Handle Enter key press"""
        if self.continue_btn.cget("state") == "normal":
            self.submit_url()
            
    def clear_url(self):
        """Clear the URL entry"""
        self.url_entry.delete(0, tk.END)
        self.update_status("", is_valid=False)



"""
Update Banner Component - Shows when an update is available
"""

import customtkinter as ctk
import logging
from typing import Optional, Callable


class UpdateBanner(ctk.CTkFrame):
    """Banner shown at top of window when an update is available"""

    def __init__(
        self,
        parent,
        on_update: Optional[Callable] = None,
        on_dismiss: Optional[Callable] = None
    ):
        super().__init__(parent, fg_color="#333333", corner_radius=0)
        self.logger = logging.getLogger(__name__)
        self.on_update = on_update
        self.on_dismiss = on_dismiss
        self._updating = False
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)

        self.label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="white"
        )
        self.label.grid(row=0, column=0, padx=(20, 10), pady=6, sticky="w")

        self.update_btn = ctk.CTkButton(
            self,
            text="Download & Restart",
            width=150,
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#F1F1F1",
            hover_color="#D0D0D0",
            text_color="#0F0F0F",
            command=self._on_update_click
        )

        self.dismiss_btn = ctk.CTkButton(
            self,
            text="Later",
            width=70,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#F1F1F1",
            hover_color="#D0D0D0",
            text_color="#0F0F0F",
            command=self._on_dismiss_click
        )

        self.progress_bar = ctk.CTkProgressBar(self, height=6)
        self.progress_bar.set(0)

    def show(self, version: str):
        self.label.configure(text=f"Update v{version} available")
        self.update_btn.grid(row=0, column=1, padx=5, pady=6)
        self.dismiss_btn.grid(row=0, column=2, padx=(5, 20), pady=6)
        self.grid(row=0, column=0, sticky="ew")
        self.lift()

    def hide(self):
        self.grid_remove()
        self.update_btn.grid_remove()
        self.dismiss_btn.grid_remove()
        self.progress_bar.grid_remove()

    def show_downloading(self):
        self._updating = True
        self.update_btn.grid_remove()
        self.dismiss_btn.grid_remove()
        self.label.configure(text="Downloading update...")
        self.progress_bar.grid(row=0, column=1, padx=20, pady=6, sticky="ew")
        self.progress_bar.set(0)

    def set_progress(self, value: float):
        self.progress_bar.set(value)

    def show_error(self, message: str):
        self._updating = False
        self.progress_bar.grid_remove()
        self.label.configure(text=f"Update failed: {message}")
        self.update_btn.configure(text="Retry")
        self.update_btn.grid(row=0, column=1, padx=5, pady=6)
        self.dismiss_btn.grid(row=0, column=2, padx=(5, 20), pady=6)

    def show_applying(self):
        self.progress_bar.grid_remove()
        self.label.configure(text="Applying update...")

    def _on_update_click(self):
        if self.on_update and not self._updating:
            self.on_update()

    def _on_dismiss_click(self):
        if self.on_dismiss:
            self.on_dismiss()

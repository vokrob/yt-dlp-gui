# -*- coding: utf-8 -*-
"""
Download Queue Component
Author: vokrob (Данил Борков)
Date: 18.07.2025
"""

import customtkinter as ctk
import threading
from typing import Callable, Optional, List
from ytdlp_gui.core.download_manager import DownloadItem, DownloadStatus

class DownloadQueueFrame(ctk.CTkFrame):
    """Frame for displaying download queue as simple rows"""

    def __init__(self, parent, download_manager=None, on_back_click: Callable = None, on_home_click: Callable = None):
        super().__init__(parent)

        self.download_manager = download_manager
        self.on_back_click = on_back_click
        self.on_home_click = on_home_click

        # Store queue item widgets and their data
        self.queue_items = []
        self.queue_item_data = {}  # Track data for each item to avoid unnecessary updates

        self.setup_ui()

        # Set up periodic refresh
        self.refresh_queue()
        
    def setup_ui(self):
        """Set up the user interface"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Title
        self.grid_rowconfigure(1, weight=1)  # Queue list
        self.grid_rowconfigure(2, weight=0)  # Buttons

        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Downloads",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(15, 20))

        # Scrollable frame for queue items
        self.scrollable_frame = ctk.CTkScrollableFrame(self, corner_radius=8)
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        # Empty state label
        self.empty_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="Empty",
            font=ctk.CTkFont(size=14),
            text_color=("gray60", "gray40")
        )
        self.empty_label.grid(row=0, column=0, pady=50)

        # Buttons frame
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        buttons_frame.grid_columnconfigure(1, weight=1)  # Expand middle space

        # Clear Downloads button (left aligned)
        self.clear_button = ctk.CTkButton(
            buttons_frame,
            text="Clear",
            width=120,
            height=36,
            font=ctk.CTkFont(size=13),
            command=self.clear_downloads
        )
        self.clear_button.grid(row=0, column=0, sticky="w")

        # Home button (right aligned)
        self.home_button = ctk.CTkButton(
            buttons_frame,
            text="Home",
            width=120,
            height=36,
            font=ctk.CTkFont(size=13),
            command=self.go_home
        )
        self.home_button.grid(row=0, column=2, sticky="e")
    def go_home(self):
        """Handle home button click"""
        if self.on_home_click:
            self.on_home_click()

    def clear_downloads(self):
        """Handle clear downloads button click"""
        if self.download_manager:
            # Disable button to prevent multiple clicks
            self.clear_button.configure(state="disabled", text="Clearing...")

            # Use a simpler approach - schedule clearing in main thread with delay
            self.after(100, self._do_clear_downloads)

    def _do_clear_downloads(self):
        """Actually perform the clearing operation"""
        try:
            if self.download_manager:
                # Use the simple version that doesn't trigger callbacks
                cleared_count = self.download_manager.clear_completed_downloads_simple()

                # Re-enable button
                self.clear_button.configure(state="normal", text="Clear")

                # Force immediate refresh
                self.refresh_queue()

                # Optional feedback
                if cleared_count > 0:
                    print(f"Cleared {cleared_count} downloads")

        except Exception as e:
            # Re-enable button on error
            self.clear_button.configure(state="normal", text="Clear")
            print(f"Error clearing downloads: {e}")

    def create_queue_item(self, download_item: DownloadItem, row: int):
        """Create a download item that looks like Current Download"""
        # Main item frame (same style as ProgressDisplayFrame)
        item_frame = ctk.CTkFrame(self.scrollable_frame)
        item_frame.grid(row=row, column=0, sticky="ew", pady=5)
        item_frame.grid_columnconfigure(1, weight=1)

        # Download Title (same as ProgressDisplayFrame)
        title_text = download_item.title or "Loading..."

        title_label = ctk.CTkLabel(
            item_frame,
            text=title_text,
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="ew")

        # Progress Bar (same as ProgressDisplayFrame)
        progress_bar = ctk.CTkProgressBar(item_frame)
        progress_bar.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        progress_value = download_item.progress / 100.0 if download_item.progress else 0
        progress_bar.set(progress_value)

        # Progress Info Frame (same structure as ProgressDisplayFrame)
        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)
        info_frame.grid_columnconfigure(2, weight=1)

        # Progress Percentage (same as ProgressDisplayFrame)
        percentage_text = f"{download_item.progress:.1f}%" if download_item.progress else "0%"
        percentage_label = ctk.CTkLabel(
            info_frame,
            text=percentage_text,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        percentage_label.grid(row=0, column=0, padx=5, sticky="w")

        # Download Speed (same as ProgressDisplayFrame)
        speed_label = ctk.CTkLabel(
            info_frame,
            text=download_item.speed or "",
            font=ctk.CTkFont(size=11)
        )
        speed_label.grid(row=0, column=1, padx=5)

        # ETA (same as ProgressDisplayFrame)
        eta_label = ctk.CTkLabel(
            info_frame,
            text=download_item.eta or "",
            font=ctk.CTkFont(size=11)
        )
        eta_label.grid(row=0, column=2, padx=5, sticky="e")

        # File Size Info Frame (same as ProgressDisplayFrame)
        size_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        size_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 15), sticky="ew")
        size_frame.grid_columnconfigure(0, weight=1)
        size_frame.grid_columnconfigure(1, weight=1)

        # Size info (same as ProgressDisplayFrame)
        size_text = ""
        if download_item.total_bytes > 0:
            downloaded = int(download_item.total_bytes * (download_item.progress / 100.0)) if download_item.progress else 0
            size_text = f"{self.format_bytes(downloaded)} / {self.format_bytes(download_item.total_bytes)}"

        size_label = ctk.CTkLabel(
            size_frame,
            text=size_text,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        size_label.grid(row=0, column=0, padx=5, sticky="w")

        # Status (same as ProgressDisplayFrame)
        status_text = self.get_status_text(download_item.status)
        status_label = ctk.CTkLabel(
            size_frame,
            text=status_text,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        status_label.grid(row=0, column=1, padx=5, sticky="e")

        return item_frame

    def update_queue_item(self, index: int, download_item: DownloadItem):
        """Update existing queue item without recreating it"""
        if index >= len(self.queue_items):
            return

        item_frame = self.queue_items[index]

        # Store references to widgets for easier updating
        title_label = None
        progress_bar = None
        percentage_label = None
        speed_label = None
        eta_label = None
        size_label = None
        status_label = None

        # Find all widgets in the item frame
        for widget in item_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                grid_info = widget.grid_info()
                if grid_info.get('row') == 0:  # Title label
                    title_label = widget
            elif isinstance(widget, ctk.CTkProgressBar):
                progress_bar = widget
            elif isinstance(widget, ctk.CTkFrame) and widget.cget('fg_color') == 'transparent':
                # This is info_frame or size_frame
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        grid_info = child.grid_info()
                        if grid_info.get('row') == 0:
                            col = grid_info.get('column', 0)
                            # Determine widget type by position and content
                            current_text = child.cget('text')
                            if col == 0:
                                if '%' in current_text or current_text == "0%":
                                    percentage_label = child
                                else:
                                    size_label = child
                            elif col == 1:
                                if any(word in current_text.lower() for word in ['speed', 'kb/s', 'mb/s', 'gb/s']) or current_text == "":
                                    speed_label = child
                                else:
                                    status_label = child
                            elif col == 2:
                                eta_label = child

        # Update widgets if found
        if title_label:
            title_text = download_item.title or "Loading..."
            title_label.configure(text=title_text)

        if progress_bar:
            progress_value = download_item.progress / 100.0 if download_item.progress else 0
            progress_bar.set(progress_value)

        if percentage_label:
            percentage_text = f"{download_item.progress:.1f}%" if download_item.progress else "0%"
            percentage_label.configure(text=percentage_text)

        if speed_label:
            speed_label.configure(text=download_item.speed or "")

        if eta_label:
            eta_label.configure(text=download_item.eta or "")

        if size_label:
            size_text = ""
            if download_item.total_bytes > 0:
                downloaded = int(download_item.total_bytes * (download_item.progress / 100.0)) if download_item.progress else 0
                size_text = f"{self.format_bytes(downloaded)} / {self.format_bytes(download_item.total_bytes)}"
            size_label.configure(text=size_text)

        if status_label:
            status_text = self.get_status_text(download_item.status)
            status_label.configure(text=status_text)

    def get_status_text(self, status: DownloadStatus) -> str:
        """Get text for status"""
        texts = {
            DownloadStatus.PENDING: "Waiting...",
            DownloadStatus.DOWNLOADING: "Downloading",
            DownloadStatus.COMPLETED: "Completed",
            DownloadStatus.FAILED: "Failed",
            DownloadStatus.CANCELLED: "Cancelled"
        }
        return texts.get(status, "Unknown")

    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human readable string"""
        if bytes_value == 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0

        return f"{bytes_value:.1f} PB"
    def refresh_queue(self):
        """Refresh the queue display"""
        if not self.download_manager:
            self.after(2000, self.refresh_queue)  # Slower refresh when no manager
            return

        # Get current queue
        queue = self.download_manager.get_queue()

        if not queue:
            # Show empty state
            self.empty_label.grid(row=0, column=0, pady=50)
            # Clear existing items
            for item_frame in self.queue_items:
                item_frame.destroy()
            self.queue_items.clear()
            self.queue_item_data.clear()
        else:
            # Hide empty state
            self.empty_label.grid_remove()

            # Check if queue structure changed (items added/removed)
            current_ids = [item.id for item in queue]
            existing_ids = list(self.queue_item_data.keys())

            if current_ids != existing_ids:
                # Queue structure changed, recreate all items
                for item_frame in self.queue_items:
                    item_frame.destroy()
                self.queue_items.clear()
                self.queue_item_data.clear()

                # Create new items
                for i, item in enumerate(queue):
                    item_frame = self.create_queue_item(item, i)
                    self.queue_items.append(item_frame)
                    self.queue_item_data[item.id] = {
                        'progress': item.progress,
                        'speed': item.speed,
                        'eta': item.eta,
                        'status': item.status.value
                    }
            else:
                # Queue structure same, just update data if changed
                for i, item in enumerate(queue):
                    old_data = self.queue_item_data.get(item.id, {})
                    new_data = {
                        'progress': item.progress,
                        'speed': item.speed,
                        'eta': item.eta,
                        'status': item.status.value
                    }

                    # Only update if data actually changed
                    if old_data != new_data:
                        self.update_queue_item(i, item)
                        self.queue_item_data[item.id] = new_data

        # Schedule next refresh (1 second for active downloads, 2 seconds when idle)
        has_active_downloads = queue and any(item.status.value in ['downloading', 'pending'] for item in queue)
        refresh_interval = 1000 if has_active_downloads else 2000
        self.after(refresh_interval, self.refresh_queue)



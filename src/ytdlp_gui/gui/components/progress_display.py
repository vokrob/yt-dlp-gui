"""
Progress Display Component - Shows download progress information
"""

import customtkinter as ctk
import tkinter as tk
from typing import Dict, Optional

class ProgressDisplayFrame(ctk.CTkFrame):
    """Frame for displaying download progress"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.current_download = None
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Current Download",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")
        
        # Download Title
        self.title_label = ctk.CTkLabel(
            self,
            text="No active download",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.title_label.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)
        
        # Progress Info Frame
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)
        info_frame.grid_columnconfigure(2, weight=1)
        
        # Progress Percentage
        self.percentage_label = ctk.CTkLabel(
            info_frame,
            text="0%",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.percentage_label.grid(row=0, column=0, padx=5, sticky="w")
        
        # Download Speed
        self.speed_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.speed_label.grid(row=0, column=1, padx=5)
        
        # ETA
        self.eta_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.eta_label.grid(row=0, column=2, padx=5, sticky="e")
        
        # File Size Info
        size_frame = ctk.CTkFrame(self, fg_color="transparent")
        size_frame.grid(row=4, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        size_frame.grid_columnconfigure(0, weight=1)
        size_frame.grid_columnconfigure(1, weight=1)
        
        # Downloaded / Total Size
        self.size_label = ctk.CTkLabel(
            size_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.size_label.grid(row=0, column=0, padx=5, sticky="w")
        
        # Status
        self.status_label = ctk.CTkLabel(
            size_frame,
            text="Ready",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.status_label.grid(row=0, column=1, padx=5, sticky="e")

        # Clear errors button (initially hidden)
        self.clear_errors_button = ctk.CTkButton(
            self,
            text="Clear Errors",
            width=100,
            height=24,
            font=ctk.CTkFont(size=10),
            command=self._on_clear_errors
        )
        # Don't grid it initially - will be shown when there are errors
        self.clear_errors_callback = None

        # New Download button (shown after completion)
        self.new_download_button = ctk.CTkButton(
            self,
            text="New Download",
            width=150,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_new_download
        )
        self.new_download_callback = None
        

        
    def update_progress(self, download_item):
        """Update progress display with download item information"""
        self.current_download = download_item

        if download_item:
            # Check for merger indication early
            should_show_merger = False
            if (download_item.progress >= 99 and
                download_item.status.value == 'downloading'):

                format_info = getattr(download_item, 'format_info', {})
                quality = format_info.get('quality', '')

                # Show merger for high quality videos
                if quality in ['720p', '1080p', '1440p', '2160p', '4K']:
                    should_show_merger = True
                    print(f"Early merger detection for {download_item.title} ({quality})")
            # Update title
            title_text = download_item.title or "Downloading..."
            if len(title_text) > 80:
                title_text = title_text[:77] + "..."
            self.title_label.configure(text=title_text)

            # Update progress bar and percentage
            progress = download_item.progress / 100.0 if download_item.progress else 0
            self.progress_bar.set(progress)
            self.percentage_label.configure(text=f"{download_item.progress:.1f}%")

            # Update speed with better formatting
            if should_show_merger:
                speed_text = "Merging formats..."
            elif download_item.speed:
                # Special handling for merger process
                if any(keyword in download_item.speed.lower() for keyword in ['merging', 'processing', 'finalizing']):
                    speed_text = f"{download_item.speed}"
                else:
                    speed_text = f"Speed: {download_item.speed}"
            else:
                speed_text = "Speed: Calculating..."
            self.speed_label.configure(text=speed_text)

            # Update ETA with better formatting
            if should_show_merger:
                eta_text = "Processing"
            elif download_item.eta:
                # Special handling for merger process
                if any(keyword in download_item.eta.lower() for keyword in ['processing', 'merging', 'completing']):
                    eta_text = f"{download_item.eta}"
                else:
                    eta_text = f"ETA: {download_item.eta}"
            else:
                eta_text = "ETA: Calculating..."
            self.eta_label.configure(text=eta_text)

            # Additional check for merger indication when progress is 100% but download not completed
            if (download_item.progress >= 100 and
                download_item.status.value == 'downloading'):

                # Check if this might be a format that needs merging
                format_info = getattr(download_item, 'format_info', {})
                quality = format_info.get('quality', '')

                # High quality videos usually need merging
                if quality in ['720p', '1080p', '1440p', '2160p', '4K'] or not download_item.speed:
                    self.speed_label.configure(text="Merging formats...")
                    self.eta_label.configure(text="Processing")

                    # Log for debugging
                    print(f"GUI: Showing merger indicator for {download_item.title} ({quality})")

            # Update size info with better formatting
            if download_item.total_bytes > 0:
                downloaded = self._format_bytes(download_item.downloaded_bytes)
                total = self._format_bytes(download_item.total_bytes)
                size_text = f"{downloaded} / {total}"
            elif download_item.downloaded_bytes > 0:
                downloaded = self._format_bytes(download_item.downloaded_bytes)
                size_text = f"{downloaded} downloaded"
            else:
                size_text = "Preparing download..."
            self.size_label.configure(text=size_text)

            # Update status with color coding
            status_text = download_item.status.value.title()
            status_color = "gray"

            # Don't show error messages in status anymore
            if download_item.status.value == 'failed':
                status_text = "Download Failed"
                status_color = "red"
            elif download_item.status.value == 'downloading':
                status_color = "green"
            elif download_item.status.value == 'completed':
                status_color = "blue"
                status_text = "Download Completed"
            elif download_item.status.value == 'pending':
                status_text = "Waiting to start..."

            self.status_label.configure(text=status_text, text_color=status_color)

            # Add visual feedback for active downloading
            if download_item.status.value == 'downloading':
                self.progress_bar.configure(progress_color="green")
            else:
                self.progress_bar.configure(progress_color="blue")  # Default color


        else:
            self.clear_progress()
            
    def clear_progress(self):
        """Clear the progress display"""
        self.current_download = None
        self.title_label.configure(text="No active download")
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color="blue")  # Reset to default color
        self.percentage_label.configure(text="0%")
        self.speed_label.configure(text="")
        self.eta_label.configure(text="")
        self.size_label.configure(text="")
        self.status_label.configure(text="Ready", text_color="gray")
        # Hide clear errors button
        self.clear_errors_button.grid_remove()
        

        

        
    def show_error(self, message: str):
        """Show an error message"""
        self.status_label.configure(text=f"Error: {message}", text_color="red")
        # Don't show clear errors button anymore since we don't show errors
        # self.clear_errors_button.grid(row=5, column=0, columnspan=2, padx=20, pady=(5, 10))

    def show_success(self, message: str):
        """Show a success message"""
        self.status_label.configure(text=message, text_color="green")
        # Hide clear errors button
        self.clear_errors_button.grid_remove()
        # Show new download button
        self.new_download_button.grid(row=6, column=0, columnspan=2, padx=20, pady=(10, 20))

    def show_info(self, message: str):
        """Show an info message"""
        self.status_label.configure(text=message, text_color="gray")
        # Hide clear errors button
        self.clear_errors_button.grid_remove()
        # Hide new download button
        self.new_download_button.grid_remove()

    def show_preparing(self, title: str = ""):
        """Show preparing download state"""
        self.current_download = None
        display_title = title if title else "Preparing download..."
        if len(display_title) > 80:
            display_title = display_title[:77] + "..."

        self.title_label.configure(text=display_title)
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color="orange")
        self.percentage_label.configure(text="0%")
        self.speed_label.configure(text="Initializing...")
        self.eta_label.configure(text="")
        self.size_label.configure(text="Getting file info...")
        self.status_label.configure(text="Preparing...", text_color="orange")
        # Hide buttons during preparation
        self.clear_errors_button.grid_remove()
        self.new_download_button.grid_remove()

    def set_clear_errors_callback(self, callback):
        """Set callback function for clear errors button"""
        self.clear_errors_callback = callback

    def set_new_download_callback(self, callback):
        """Set callback function for new download button"""
        self.new_download_callback = callback

    def _on_clear_errors(self):
        """Handle clear errors button click"""
        if self.clear_errors_callback:
            self.clear_errors_callback()

    def _on_new_download(self):
        """Handle new download button click"""
        if self.new_download_callback:
            self.new_download_callback()
        self.clear_progress()

    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """Format bytes to human readable string"""
        if bytes_value == 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0

        return f"{bytes_value:.1f} PB"

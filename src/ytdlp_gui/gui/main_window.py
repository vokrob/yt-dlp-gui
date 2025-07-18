# -*- coding: utf-8 -*-
"""
Main GUI window
Author: vokrob (Данил Борков)
Date: 18.07.2025
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import logging
from pathlib import Path
import time

from ytdlp_gui.core.download_manager import DownloadManager
from ytdlp_gui.core.settings_manager import SettingsManager
from ytdlp_gui.gui.components.url_input import URLInputFrame
from ytdlp_gui.gui.components.format_selector import FormatSelectorFrame
from ytdlp_gui.gui.components.output_selector import OutputSelectorFrame
from ytdlp_gui.gui.components.progress_display import ProgressDisplayFrame
from ytdlp_gui.gui.components.download_queue import DownloadQueueFrame
from ytdlp_gui.gui.components.simple_url_input import SimpleURLInputFrame
from ytdlp_gui.gui.components.video_preview import VideoPreviewFrame
from ytdlp_gui.gui.components.download_options import DownloadOptionsFrame
from ytdlp_gui.utils.notifications import init_notifications, get_notification_manager, get_error_handler
from ytdlp_gui.utils.logger import init_logging, get_logger

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class YTDLPGUIApp:
    """Main app class"""

    def __init__(self):
        self.log_manager = init_logging()
        self.logger = get_logger(__name__)

        self.settings_manager = SettingsManager()
        self.download_manager = DownloadManager(self.settings_manager)

        self.notification_manager = None
        self.error_handler = None

        self.startup_time = time.time()
        self.startup_grace_period = 3.0
        self.startup_failed_ids = set()

        # UI state
        self.current_state = "url_input"
        self.current_url = ""
        self.current_video_info = None
        self.preview_container = None

        # Main window
        self.root = ctk.CTk()
        self.root.title("YT-DLP GUI")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 650)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Try to set icon
        try:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass

        self.setup_ui()
        self.setup_bindings()

        self.notification_manager = init_notifications(self.root)
        self.error_handler = get_error_handler()

        notifications_enabled = self.settings_manager.get('notification_enabled', True)
        self.notification_manager.enable_notifications(notifications_enabled)

        self._mark_existing_failed_downloads()
        
    def setup_ui(self):
        """Setup UI"""
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.create_all_components()
        self.show_url_input_state()

    def create_all_components(self):
        """Create UI components"""
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.simple_url_input = SimpleURLInputFrame(
            self.main_frame,
            on_url_submit=self.on_url_submitted
        )

        self.video_preview_frame = VideoPreviewFrame(
            self.main_frame,
            on_download_click=self.on_preview_download_click,
            settings_manager=self.settings_manager
        )

        self.download_options_frame = DownloadOptionsFrame(
            self.main_frame,
            settings_manager=self.settings_manager,
            on_download_click=self.on_options_download_click
        )

        self.fixed_buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.fixed_buttons_frame.grid_columnconfigure(1, weight=1)

        self.back_button = ctk.CTkButton(
            self.fixed_buttons_frame,
            text="Back",
            width=120,
            height=36,
            font=ctk.CTkFont(size=13),
            command=self.show_url_input
        )
        self.back_button.grid(row=0, column=0, sticky="w")

        self.start_button = ctk.CTkButton(
            self.fixed_buttons_frame,
            text="Start",
            width=120,
            height=36,
            font=ctk.CTkFont(size=13),
            command=self.on_start_download_click
        )
        self.start_button.grid(row=0, column=2, sticky="e")

        # 4. Progress Display Frame
        self.progress_frame = ProgressDisplayFrame(self.main_frame)

        # Set up clear errors callback
        self.progress_frame.set_clear_errors_callback(self.clear_failed_downloads)

        # Set up new download callback
        self.progress_frame.set_new_download_callback(self.show_url_input)

        # 5. Download Queue Frame
        self.download_queue_frame = DownloadQueueFrame(
            self.main_frame,
            download_manager=self.download_manager,
            on_home_click=self.show_url_input
        )

        # Setup progress tracking
        self.setup_progress_tracking()

        # Keep old components for compatibility (hidden)
        self.create_legacy_components()

    def create_legacy_components(self):
        """Create legacy components for compatibility (hidden by default)"""
        # Create a hidden frame for legacy components
        self.legacy_frame = ctk.CTkFrame(self.main_frame)
        # Don't grid it - keep it hidden

        # URL Input Frame (legacy)
        self.url_input_frame = URLInputFrame(
            self.legacy_frame,
            on_url_change=self.on_url_change,
            on_add_to_queue=self.add_to_queue
        )

        # Format Selector (legacy)
        self.format_selector_frame = FormatSelectorFrame(
            self.legacy_frame,
            on_format_change=self.on_format_change
        )

        # Output Directory Selector (legacy)
        self.output_selector_frame = OutputSelectorFrame(
            self.legacy_frame,
            settings_manager=self.settings_manager,
            on_output_change=self.on_output_change
        )

    def setup_bindings(self):
        """Set up event bindings"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # State Management Methods
    def show_url_input_state(self):
        """Show only the URL input (initial state)"""
        self.logger.info("Switching to URL input state")
        self.current_state = "url_input"
        self.hide_all_frames()

        # Configure main frame for single component
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=0)

        self.simple_url_input.grid(row=0, column=0, sticky="nsew")

        # Force update and refresh
        self.main_frame.update_idletasks()
        self.logger.info("URL input state shown")

    def show_preview_state(self, url: str):
        """Show video preview with download options"""
        self.logger.info(f"Switching to preview state for URL: {url}")
        self.current_state = "preview"
        self.current_url = url
        self.hide_all_frames()

        # Simple, clean layout - three rows with proper spacing
        self.main_frame.grid_rowconfigure(0, weight=1)  # Video preview - takes most space
        self.main_frame.grid_rowconfigure(1, weight=0)  # Download options - compact
        self.main_frame.grid_rowconfigure(2, weight=0)  # Buttons - fixed at bottom
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Show video preview frame - clean and spacious
        self.video_preview_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))

        # Show download options frame - centered and compact
        self.download_options_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        # Show buttons frame - clean bottom placement
        self.fixed_buttons_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))

        # Force update and refresh
        self.main_frame.update_idletasks()

        # Load video info
        self.video_preview_frame.load_video_info(url)

        # Load available video qualities
        self.download_options_frame.load_video_qualities(url)

        self.logger.info("Preview state setup complete")

    def show_download_state(self):
        """Show download queue only"""
        self.logger.info("Switching to download state")
        self.current_state = "download"
        self.hide_all_frames()

        # Configure main frame for single component: download queue only
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Show only download queue (no Current Download)
        self.download_queue_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        # Force update
        self.main_frame.update_idletasks()
        self.logger.info("Download state shown")

    def hide_all_frames(self):
        """Hide all main frames"""
        self.logger.info("Hiding all frames")
        self.simple_url_input.grid_remove()
        self.video_preview_frame.grid_remove()
        self.download_options_frame.grid_remove()
        self.progress_frame.grid_remove()
        self.download_queue_frame.grid_remove()
        self.fixed_buttons_frame.grid_remove()

        # Remove preview container if it exists
        if hasattr(self, 'preview_container') and self.preview_container:
            self.preview_container.destroy()
            self.preview_container = None

        # Also remove any other containers
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and widget not in [
                self.simple_url_input, self.video_preview_frame,
                self.download_options_frame, self.progress_frame, self.download_queue_frame,
                self.legacy_frame, self.fixed_buttons_frame
            ]:
                widget.destroy()
        self.logger.info("All frames hidden")

    # Event Handlers for New UI
    def on_url_submitted(self, url: str):
        """Handle URL submission from simple input"""
        self.logger.info(f"URL submitted: {url}")
        try:
            self.show_preview_state(url)
        except Exception as e:
            self.logger.error(f"Failed to show preview state: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    def on_preview_download_click(self, url: str):
        """Handle download click from video preview"""
        # This should not be used - download options are separate
        pass

    def on_options_download_click(self, format_info: dict, output_path: str):
        """Handle download click from options"""
        self.logger.info(f"Starting download with format: {format_info}")

        # Get video title from preview component
        video_info = self.video_preview_frame.get_video_info()
        video_title = None
        if video_info and video_info.get('title'):
            video_title = video_info['title']
            self.logger.info(f"Using title from preview: '{video_title}'")



        self.show_download_state()

        # Start the actual download
        try:
            download_id = self.download_manager.add_download(
                self.current_url, format_info, output_path, video_title
            )
            self.logger.info(f"Download started with ID: {download_id}")
        except Exception as e:
            self.logger.error(f"Failed to start download: {e}")
            self.progress_frame.show_error(f"Failed to start download: {str(e)}")

    def on_start_download_click(self):
        """Handle start download click from fixed button"""
        self.logger.info("Start button clicked")
        # Get format info from download options and start download
        self.download_options_frame.start_download()

    def go_back_from_downloads(self):
        """Go back from downloads page"""
        if self.current_url:
            # If we have a current URL, go back to preview
            self.show_preview_state(self.current_url)
        else:
            # Otherwise go to URL input
            self.show_url_input()

    def show_url_input(self):
        """Return to URL input state (called by back button)"""
        self.logger.info("show_url_input called (back button)")
        self.show_url_input_state()
        self.simple_url_input.clear_url()

    def return_to_start(self):
        """Return to initial URL input state after download completion"""
        if self.current_state == "download":
            self.show_url_input_state()
            self.simple_url_input.clear_url()
            self.current_url = ""
            self.current_video_info = None

    def _mark_existing_failed_downloads(self):
        """Mark all existing failed downloads as 'old' to avoid showing them"""
        try:
            for item in self.download_manager.get_queue():
                if item.status.value == 'failed':
                    self.startup_failed_ids.add(item.id)

            self.logger.info(f"Marked {len(self.startup_failed_ids)} existing failed downloads as old")
        except Exception as e:
            self.logger.error(f"Error marking existing failed downloads: {e}")

    def setup_progress_tracking(self):
        """Setup progress tracking for downloads"""
        # Add callback for queue changes to track active downloads
        self.download_manager.add_queue_callback(self.on_queue_change)

        # Start periodic progress updates
        self.update_progress_display()

    def update_progress_display(self):
        """Update progress display with current active download"""
        try:
            # Get current active download (prioritize downloading status)
            active_download = None
            pending_download = None

            for item in self.download_manager.get_queue():
                if item.status.value == 'downloading':
                    active_download = item
                    break
                elif item.status.value == 'pending' and pending_download is None:
                    pending_download = item

            # Update progress display
            if active_download:
                self.progress_frame.update_progress(active_download)
            elif pending_download:
                # Show pending download with preparing state
                self.progress_frame.show_preparing(pending_download.title or "Preparing download...")
            else:
                # Check if any downloads completed recently
                completed_downloads = [
                    item for item in self.download_manager.get_queue()
                    if item.status.value == 'completed'
                ]

                # Check for failed downloads - but don't show them in UI anymore
                # (Failed downloads are still tracked in the queue and can be cleared manually)

                if completed_downloads:
                    # Show the most recently completed download briefly
                    latest_completed = max(completed_downloads, key=lambda x: x.completed_at or 0)
                    if not hasattr(self, '_last_completed_id') or self._last_completed_id != latest_completed.id:
                        self.progress_frame.show_success(f"Download completed: {latest_completed.title}")
                        self._last_completed_id = latest_completed.id

                        # If we're in download state, show completion but don't auto-return
                        # User can manually click "New Download" button if they want to start over
                        # Clear after 3 seconds
                        self.root.after(3000, lambda: self.progress_frame.clear_progress())
                    else:
                        self.progress_frame.clear_progress()
                else:
                    self.progress_frame.clear_progress()

        except Exception as e:
            self.logger.error(f"Error updating progress display: {e}")

        # Schedule next update
        self.root.after(1000, self.update_progress_display)  # Update every 1000ms (1 second)
        
    def on_url_change(self, url):
        """Handle URL input change"""
        # URL change handling simplified
        pass
            
    def on_format_change(self, format_info):
        """Handle format selection change"""
        self.logger.info(f"Format changed: {format_info}")
        
    def on_output_change(self, output_path):
        """Handle output directory change"""
        self.logger.info(f"Output directory changed: {output_path}")
        
    def on_queue_change(self):
        """Handle download queue changes"""
        # Queue change handling simplified
        pass

    def clear_failed_downloads(self):
        """Clear all failed downloads from the queue"""
        try:
            cleared_count = self.download_manager.clear_failed_downloads()
            if cleared_count > 0:
                self.logger.info(f"Cleared {cleared_count} failed downloads")
                # Clear the startup failed IDs as well
                self.startup_failed_ids.clear()
                # Show success notification
                if self.notification_manager:
                    self.notification_manager.show_success(
                        "Errors Cleared",
                        f"Cleared {cleared_count} failed download(s)"
                    )
        except Exception as e:
            self.logger.error(f"Failed to clear failed downloads: {e}")
            if self.error_handler:
                self.error_handler.handle_unexpected_error(e, "clearing failed downloads")
            
    def add_to_queue(self, url, format_info=None, output_path=None):
        """Add a download to the queue"""
        try:
            # Validate URL
            if not url or not url.strip():
                self.error_handler.handle_validation_error("URL", "Please enter a valid URL")
                return

            # Get current selections if not provided
            if format_info is None:
                format_info = self.format_selector_frame.get_selected_format()
            if output_path is None:
                output_path = self.output_selector_frame.get_output_path()

            # Validate output path
            if not output_path:
                self.error_handler.handle_validation_error("Output Directory", "Please select an output directory")
                return

            # Show preparing state immediately
            self.progress_frame.show_preparing("Preparing download...")

            # Start download immediately
            download_id = self.download_manager.add_download(url, format_info, output_path)

            # Show success notification
            self.notification_manager.show_success(
                "Download Started",
                f"Download started"
            )

            # Clear URL input
            self.url_input_frame.set_url("")

        except Exception as e:
            self.logger.error(f"Failed to add to queue: {e}")
            # Don't show error in progress display anymore - just log it
            # self.progress_frame.show_error(f"Failed to start download: {str(e)}")
            self.error_handler.handle_download_error(e, url)
            

        
    def on_closing(self):
        """Handle app closing"""
        try:
            active_downloads = len([
                item for item in self.download_manager.get_queue()
                if item.status.value == 'downloading'
            ])

            if active_downloads > 0:
                result = messagebox.askyesno(
                    "Active Downloads",
                    f"There are {active_downloads} active download(s).\n\n"
                    "Do you want to stop them and exit?",
                    parent=self.root
                )
                if not result:
                    return

            self.download_manager.stop_all_downloads()
            self.settings_manager.save_settings()
            self.root.destroy()

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            self.root.destroy()



    def run(self):
        """Start the application"""
        self.logger.info("Starting GUI application")
        self.root.mainloop()

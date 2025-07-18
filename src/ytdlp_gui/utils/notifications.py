# -*- coding: utf-8 -*-
"""
Notifications
Author: vokrob (Данил Борков)
Date: 18.07.2025
"""

import logging
import threading
import time
from typing import Optional, Callable
from enum import Enum
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

class NotificationType(Enum):
    """Types of notifications"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class NotificationManager:
    """Manages application notifications"""
    
    def __init__(self, parent_window=None):
        self.logger = logging.getLogger(__name__)
        self.parent_window = parent_window
        self.notifications_enabled = True
        self.toast_notifications = []
        
    def set_parent_window(self, parent_window):
        """Set the parent window for notifications"""
        self.parent_window = parent_window
        
    def enable_notifications(self, enabled: bool):
        """Enable or disable notifications"""
        self.notifications_enabled = enabled
        
    def show_info(self, title: str, message: str, show_toast: bool = True):
        """Show info notification"""
        self._show_notification(NotificationType.INFO, title, message, show_toast)
        
    def show_success(self, title: str, message: str, show_toast: bool = True):
        """Show success notification"""
        self._show_notification(NotificationType.SUCCESS, title, message, show_toast)
        
    def show_warning(self, title: str, message: str, show_toast: bool = True):
        """Show warning notification"""
        self._show_notification(NotificationType.WARNING, title, message, show_toast)
        
    def show_error(self, title: str, message: str, show_toast: bool = True, show_dialog: bool = False):
        """Show error notification"""
        self._show_notification(NotificationType.ERROR, title, message, show_toast)
        
        if show_dialog and self.parent_window:
            messagebox.showerror(title, message, parent=self.parent_window)
            
    def _show_notification(self, notification_type: NotificationType, title: str, message: str, show_toast: bool):
        """Internal method to show notifications"""
        if not self.notifications_enabled:
            return
            
        # Log the notification
        log_message = f"{title}: {message}"
        if notification_type == NotificationType.ERROR:
            self.logger.error(log_message)
        elif notification_type == NotificationType.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
            
        # Show toast notification if requested and parent window exists
        if show_toast and self.parent_window:
            self._show_toast(notification_type, title, message)
            
    def _show_toast(self, notification_type: NotificationType, title: str, message: str):
        """Show a toast notification"""
        try:
            toast = ToastNotification(self.parent_window, notification_type, title, message)
            self.toast_notifications.append(toast)
            
            # Remove toast after it's closed
            def cleanup():
                if toast in self.toast_notifications:
                    self.toast_notifications.remove(toast)
                    
            toast.on_close = cleanup
            
        except Exception as e:
            self.logger.error(f"Failed to show toast notification: {e}")

class ToastNotification(ctk.CTkToplevel):
    """Toast notification window"""
    
    def __init__(self, parent, notification_type: NotificationType, title: str, message: str):
        super().__init__(parent)
        
        self.notification_type = notification_type
        self.on_close = None
        
        self.setup_window()
        self.setup_ui(title, message)
        self.show_animation()
        
        # Auto-close after 5 seconds
        self.after(5000, self.close_notification)
        
    def setup_window(self):
        """Set up the toast window"""
        self.title("")
        self.geometry("350x100")
        self.resizable(False, False)
        
        # Remove window decorations
        self.overrideredirect(True)
        
        # Position at top-right of screen
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        x = screen_width - 370
        y = 20
        self.geometry(f"350x100+{x}+{y}")
        
        # Always on top
        self.attributes("-topmost", True)
        
    def setup_ui(self, title: str, message: str):
        """Set up the toast UI"""
        # Color scheme based on notification type
        colors = {
            NotificationType.INFO: ("#1f538d", "#ffffff"),
            NotificationType.SUCCESS: ("#28a745", "#ffffff"),
            NotificationType.WARNING: ("#fd7e14", "#ffffff"),
            NotificationType.ERROR: ("#dc3545", "#ffffff"),
        }
        
        bg_color, text_color = colors.get(self.notification_type, ("#1f538d", "#ffffff"))
        
        # Main frame
        main_frame = ctk.CTkFrame(self, fg_color=bg_color, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Icon and content frame
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=10)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Icon
        icons = {
            NotificationType.INFO: "i",
            NotificationType.SUCCESS: "OK",
            NotificationType.WARNING: "!",
            NotificationType.ERROR: "X",
        }
        
        icon_label = ctk.CTkLabel(
            content_frame,
            text=icons.get(self.notification_type, "i"),
            font=ctk.CTkFont(size=20),
            text_color=text_color
        )
        icon_label.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="n")
        
        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=text_color,
            anchor="w"
        )
        title_label.grid(row=0, column=1, sticky="ew")
        
        # Message
        message_label = ctk.CTkLabel(
            content_frame,
            text=message,
            font=ctk.CTkFont(size=10),
            text_color=text_color,
            anchor="w",
            wraplength=250
        )
        message_label.grid(row=1, column=1, sticky="ew")
        
        # Close button
        close_btn = ctk.CTkButton(
            content_frame,
            text="×",
            width=20,
            height=20,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent",
            text_color=text_color,
            hover_color=bg_color,
            command=self.close_notification
        )
        close_btn.grid(row=0, column=2, sticky="ne")
        
        # Bind click to close
        main_frame.bind("<Button-1>", lambda e: self.close_notification())
        
    def show_animation(self):
        """Show the toast with animation"""
        # Start off-screen
        screen_width = self.winfo_screenwidth()
        start_x = screen_width
        end_x = screen_width - 370
        
        # Animate slide-in
        def animate(step=0):
            if step <= 20:
                current_x = start_x - (start_x - end_x) * (step / 20)
                self.geometry(f"350x100+{int(current_x)}+20")
                self.after(10, lambda: animate(step + 1))
                
        animate()
        
    def close_notification(self):
        """Close the toast notification"""
        # Animate slide-out
        screen_width = self.winfo_screenwidth()
        start_x = screen_width - 370
        end_x = screen_width
        
        def animate(step=0):
            if step <= 10:
                current_x = start_x + (end_x - start_x) * (step / 10)
                self.geometry(f"350x100+{int(current_x)}+20")
                self.after(10, lambda: animate(step + 1))
            else:
                if self.on_close:
                    self.on_close()
                self.destroy()
                
        animate()

class ErrorHandler:
    """Centralized error handling"""
    
    def __init__(self, notification_manager: NotificationManager):
        self.logger = logging.getLogger(__name__)
        self.notification_manager = notification_manager
        
    def handle_download_error(self, error: Exception, url: str = "", show_user: bool = True):
        """Handle download-related errors"""
        error_msg = str(error)
        
        # Categorize error types
        if "network" in error_msg.lower() or "connection" in error_msg.lower():
            user_msg = "Network connection error. Please check your internet connection."
            title = "Network Error"
        elif "not found" in error_msg.lower() or "404" in error_msg:
            user_msg = "Video not found. The URL may be invalid or the video may have been removed."
            title = "Video Not Found"
        elif "private" in error_msg.lower() or "permission" in error_msg.lower():
            user_msg = "This video is private or requires authentication."
            title = "Access Denied"
        elif "format" in error_msg.lower():
            user_msg = "The requested format is not available for this video."
            title = "Format Error"
        else:
            user_msg = f"Download failed: {error_msg}"
            title = "Download Error"
            
        # Log the full error
        self.logger.error(f"Download error for {url}: {error}", exc_info=True)
        
        # Show user notification
        if show_user:
            self.notification_manager.show_error(title, user_msg, show_toast=True)
            
    def handle_validation_error(self, field: str, message: str):
        """Handle validation errors"""
        title = f"Validation Error - {field}"
        self.notification_manager.show_warning(title, message, show_toast=True)
        
    def handle_file_error(self, error: Exception, operation: str = "file operation"):
        """Handle file-related errors"""
        error_msg = str(error)
        
        if "permission" in error_msg.lower():
            user_msg = f"Permission denied. Please check file/folder permissions."
            title = "Permission Error"
        elif "not found" in error_msg.lower():
            user_msg = f"File or directory not found."
            title = "File Not Found"
        elif "space" in error_msg.lower():
            user_msg = f"Insufficient disk space."
            title = "Disk Space Error"
        else:
            user_msg = f"File operation failed: {error_msg}"
            title = "File Error"
            
        self.logger.error(f"File error during {operation}: {error}", exc_info=True)
        self.notification_manager.show_error(title, user_msg, show_toast=True)
        
    def handle_unexpected_error(self, error: Exception, context: str = ""):
        """Handle unexpected errors"""
        error_msg = str(error)
        title = "Unexpected Error"
        user_msg = f"An unexpected error occurred. Please try again or contact support if the problem persists."
        
        if context:
            log_msg = f"Unexpected error in {context}: {error}"
        else:
            log_msg = f"Unexpected error: {error}"
            
        self.logger.error(log_msg, exc_info=True)
        self.notification_manager.show_error(title, user_msg, show_toast=True, show_dialog=True)

# Global notification manager instance
_notification_manager = None
_error_handler = None

def get_notification_manager() -> NotificationManager:
    """Get the global notification manager"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager

def get_error_handler() -> ErrorHandler:
    """Get the global error handler"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler(get_notification_manager())
    return _error_handler

def init_notifications(parent_window):
    """Initialize the notification system"""
    notification_manager = get_notification_manager()
    notification_manager.set_parent_window(parent_window)
    return notification_manager

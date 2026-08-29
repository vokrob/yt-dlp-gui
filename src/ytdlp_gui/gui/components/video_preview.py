# -*- coding: utf-8 -*-
"""
Video Preview Component
Author: vokrob
Date: 18.07.2025
"""

import customtkinter as ctk
import threading
import logging
import requests
from PIL import Image
import io
import re
from typing import Dict, Optional, Callable

from ytdlp_gui.core.cookie_manager import CookieManager
from ytdlp_gui.core import ytdlp_wrapper

class VideoPreviewFrame(ctk.CTkFrame):
    """Frame for displaying video preview with title and thumbnail"""
    
    def __init__(self, parent, settings_manager=None,
                 on_info_loaded: Optional[Callable] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager
        self.on_info_loaded = on_info_loaded

        # Initialize cookie manager if settings_manager is available
        self.cookie_manager = None
        if self.settings_manager:
            self.cookie_manager = CookieManager(self.settings_manager)

        # Video info
        self.video_info = None
        self.thumbnail_image = None
        self.loading_complete = False
        self.last_loaded_url = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Loading frame - shown during loading
        self.loading_frame = ctk.CTkFrame(self)
        self.loading_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.loading_frame.grid_columnconfigure(0, weight=1)
        self.loading_frame.grid_rowconfigure(0, weight=1)

        # Loading content
        loading_content = ctk.CTkFrame(self.loading_frame, fg_color="transparent")
        loading_content.grid(row=0, column=0)

        # Loading spinner - clean and modern
        self.loading_label = ctk.CTkLabel(
            loading_content,
            text="|",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=("gray60", "gray40")
        )
        self.loading_label.grid(row=0, column=0, pady=30)

        # Animation state
        self.animation_state = 0

        # Content frame - shown after loading
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)

        # Title section - clean and modern
        self.title_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, sticky="ew", pady=(10, 15))
        self.title_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="",
            font=ctk.CTkFont(size=18, weight="bold"),
            wraplength=800,
            justify="center"
        )
        self.title_label.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        self.channel_label = ctk.CTkLabel(
            self.title_frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray50"),
            justify="center"
        )
        self.channel_label.grid(row=1, column=0, sticky="ew")

        # Thumbnail section - clean and centered
        self.thumbnail_frame = ctk.CTkFrame(self.content_frame, corner_radius=12)
        self.thumbnail_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self.thumbnail_frame.grid_columnconfigure(0, weight=1)
        self.thumbnail_frame.grid_rowconfigure(0, weight=1)

        self.thumbnail_label = ctk.CTkLabel(
            self.thumbnail_frame,
            text="",
            font=ctk.CTkFont(size=14)
        )
        self.thumbnail_label.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        # Start with loading animation
        self.start_loading_animation()

    def start_loading_animation(self):
        """Start loading animation"""
        self.loading_complete = False
        self.animation_state = 0
        self.animation_cycle = 0  # Track animation cycles for subtle effects
        self.loading_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.content_frame.grid_remove()
        self._animate_loading()

    def _animate_loading(self):
        """Animate loading spinner with smooth effects"""
        if not self.loading_complete:
            # Smooth loading animation
            loading_states = [
                "|",
                "/",
                "-",
                "\\",
                "|",
                "/",
                "-",
                "\\"
            ]

            # Subtle color cycling for visual appeal
            colors = [
                ("gray60", "gray40"),
                ("gray65", "gray45"),
                ("gray70", "gray50"),
                ("gray65", "gray45")
            ]

            color_index = (self.animation_cycle // 4) % len(colors)

            self.loading_label.configure(
                text=loading_states[self.animation_state],
                text_color=colors[color_index]
            )

            self.animation_state = (self.animation_state + 1) % len(loading_states)
            self.animation_cycle += 1

            # Continue animation every 120ms for very smooth animation
            self.after(120, self._animate_loading)

    def show_content(self):
        """Show content and hide loading"""
        self.loading_complete = True
        self.loading_frame.grid_remove()
        self.content_frame.grid(row=0, column=0, sticky="nsew")

    def load_video_info(self, url: str):
        """Load video information from URL"""
        if url == self.last_loaded_url and self.video_info:
            self.logger.info(f"Using cached video info for URL: {url}")
            self._update_video_info()
            self._finalize_loading()
            if self.on_info_loaded and self.video_info.get('url'):
                self.on_info_loaded(self.video_info['url'])
            return

        self.logger.info(f"Loading video info for URL: {url}")
        self.last_loaded_url = url

        # Reset state and show loading
        self.start_loading_animation()

        # Load info in separate thread
        threading.Thread(target=self._fetch_video_info, args=(url,), daemon=True).start()
        
    def _fetch_video_info(self, url: str):
        """Fetch video information using yt-dlp (runs in separate thread)"""
        try:
            base_args = [
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]
            # Try once with ONLY cookies.txt if exists (no browser cookie extraction)
            extra = list(base_args)
            if self.cookie_manager:
                self.cookie_manager.add_cookie_file_args(extra)

            info = ytdlp_wrapper.extract_info(url, extra_args=extra)

            if not info:
                real_error = ytdlp_wrapper.get_last_error()
                if real_error and self._is_authentication_error(real_error):
                    self.after(0, lambda: self._show_authentication_error(url))
                elif real_error:
                    user_msg = self._format_user_error(real_error)
                    self.after(0, lambda m=user_msg: self._show_error(m))
                else:
                    self.after(0, lambda: self._show_error("Could not load video information"))
                return

            if info:
                title = info.get('title', 'Unknown Title')
                if 'youtube video #' in title.lower():
                    self.logger.info("Got generic title from yt-dlp, trying HTML extraction...")
                    html_title = ytdlp_wrapper.extract_title_from_html(url)
                    if html_title:
                        title = html_title
                    else:
                        video_id = None
                        if 'youtube.com/watch?v=' in url:
                            video_id = url.split('v=')[1].split('&')[0]
                        elif 'youtu.be/' in url:
                            video_id = url.split('youtu.be/')[1].split('?')[0]
                        if video_id:
                            title = f"YouTube Video ({video_id})"

                self.video_info = {
                    'title': title,
                    'uploader': info.get('uploader', 'Unknown Channel'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', ''),
                    'url': url
                }

                self.after(0, self._update_video_info)

                if self.video_info['thumbnail']:
                    self._load_thumbnail(self.video_info['thumbnail'])
                else:
                    self.after(0, self._finalize_loading)
            else:
                real_error = ytdlp_wrapper.get_last_error()
                if real_error:
                    display_msg = self._format_user_error(real_error)
                else:
                    display_msg = "Could not load video information"
                self.after(0, lambda m=display_msg: self._show_error(m))

        except Exception as e:
            self.logger.error(f"Failed to fetch video info: {e}")
            self.after(0, lambda: self._show_error(f"Error loading video: {str(e)}"))
            
    def _update_video_info(self):
        """Update UI with video information (runs on main thread)"""
        if not self.video_info:
            return

        # Update title
        title = self.video_info['title']
        if len(title) > 100:
            title = title[:97] + "..."
        self.title_label.configure(text=title)

        # Update channel (without duration)
        uploader = self.video_info['uploader']
        self.channel_label.configure(text=uploader)

        # Notify parent that info is loaded so it can load formats
        if self.on_info_loaded and self.video_info.get('url'):
            self.on_info_loaded(self.video_info['url'])
        
    def _load_thumbnail(self, thumbnail_url: str):
        """Load thumbnail image from URL"""
        try:
            response = requests.get(thumbnail_url, timeout=10)
            response.raise_for_status()

            # Load image
            image = Image.open(io.BytesIO(response.content))

            # Get optimal size for preview - balanced and beautiful
            # High quality preview that fits well in the interface
            max_width = 720   # Optimal width for interface
            max_height = 405  # 16:9 aspect ratio, perfect size

            # Calculate scaling to fit the available space while maintaining aspect ratio
            original_width, original_height = image.size
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            scale_ratio = min(width_ratio, height_ratio)

            # Calculate new size
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)

            # Resize image
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to CTkImage with the actual size
            self.thumbnail_image = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=(new_width, new_height)
            )

            # Update UI on main thread
            self.after(0, self._update_thumbnail)

        except Exception as e:
            self.logger.warning(f"Failed to load thumbnail: {e}")
            self.after(0, lambda: self.thumbnail_label.configure(text="Thumbnail not available"))
            self.after(0, self._finalize_loading)
            
    def _update_thumbnail(self):
        """Update thumbnail display (runs on main thread)"""
        if self.thumbnail_image:
            self.thumbnail_label.configure(image=self.thumbnail_image, text="")
        else:
            self.thumbnail_label.configure(text="Thumbnail not available")
        # Finalize loading after thumbnail is set
        self._finalize_loading()

    def _finalize_loading(self):
        """Finalize loading and show content"""
        self.show_content()
            
    @staticmethod
    def _clean_error_message(message: str) -> str:
        """Strip yt-dlp technical prefixes and suffix from error messages."""
        # Remove "ERROR: [extractor] video_id: " prefix
        msg = re.sub(r'^ERROR:\s*\[\w+\].*?: ', '', message, count=1)
        # Remove "; please report this issue..." suffix
        idx = msg.find('; please report this issue')
        if idx > 0:
            msg = msg[:idx]
        # Remove trailing URL if any
        idx = msg.find('https://')
        if idx > 0:
            msg = msg[:idx].rstrip(',; ')
        return msg.strip()

    @staticmethod
    def _format_user_error(ytdlp_error: str) -> str:
        """Convert known yt-dlp errors to user-friendly messages."""
        clean = VideoPreviewFrame._clean_error_message(ytdlp_error)
        lower = clean.lower()

        messages = {
            "no video formats found": (
                "No video formats found.\n\n"
                "Wait for a new yt-dlp release (usually 1-2 days)."
            ),
            "failed to extract any player response": (
                "YouTube changed its API - extraction is unavailable.\n\n"
                "The app already downloaded the latest yt-dlp build, but YouTube\n"
                "requires another update. yt-dlp usually releases a patch in 1-2 days."
            ),
            "video unavailable": (
                "Video unavailable. It may be:\n"
                "- deleted by the author or YouTube\n"
                "- private\n"
                "- blocked in your region"
            ),
            "video is unavailable": (
                "Video unavailable. It may be:\n"
                "- deleted by the author or YouTube\n"
                "- private\n"
                "- blocked in your region"
            ),
            "incomplete youtube id": (
                "Invalid video URL. Please check the link."
            ),
            "sign in to confirm": (
                "This video requires sign-in.\n\n"
                "Log into YouTube in your browser and enable cookies in settings."
            ),
            "this video is only available for registered users": (
                "Video is only available for registered users."
            ),
            "age": (
                "Age-restricted video.\n\n"
                "Log into YouTube in your browser and enable cookies."
            ),
            "http error 404": (
                "Video not found (404). It may have been deleted."
            ),
            "http error 403": (
                "Access denied (403).\n"
                "Check your VPN or try again later."
            ),
        }

        for keyword, msg in messages.items():
            if keyword in lower:
                return msg

        return clean

    def _show_error(self, message: str):
        """Show error message"""
        self.title_label.configure(text="Error loading video")
        self.channel_label.configure(text="")
        if len(message) > 400:
            message = message[:397] + "..."
        self.thumbnail_label.configure(text=message, wraplength=700)
        self.show_content()

    def _is_authentication_error(self, error_msg: str) -> bool:
        """Check if the error is related to authentication/login requirements"""
        auth_keywords = [
            "only available for registered users",
            "sign in to confirm",
            "authentication required",
            "login required",
            "private video",
            "requires authentication",
            "cookies",
            "username and password"
        ]

        error_lower = error_msg.lower()
        return any(keyword in error_lower for keyword in auth_keywords)

    def _show_authentication_error(self, url: str):
        """Show authentication error with helpful message"""
        site_name = self._get_site_name(url)

        if "vk" in url.lower():
            message = f"VK video requires login.\n\nTo access VK videos:\n1. Log in to VK in your browser\n2. Make sure cookies are enabled in settings\n3. Try again"
        elif "youtube" in url.lower():
            message = f"YouTube requires authentication.\n\nTry:\n1. Log in to YouTube in your browser\n2. Enable cookies in settings\n3. Use VPN if needed"
        else:
            message = f"{site_name} requires authentication.\n\nPlease log in to {site_name} in your browser and ensure cookies are enabled."

        self.title_label.configure(text=f"Authentication Required - {site_name}")
        self.channel_label.configure(text="Login needed")
        self.thumbnail_label.configure(text=message)
        self.show_content()

    def _get_site_name(self, url: str) -> str:
        """Extract site name from URL"""
        if "vk.com" in url or "vkvideo.ru" in url:
            return "VKontakte"
        elif "youtube.com" in url or "youtu.be" in url:
            return "YouTube"
        elif "vimeo.com" in url:
            return "Vimeo"
        elif "facebook.com" in url:
            return "Facebook"
        elif "instagram.com" in url:
            return "Instagram"
        elif "twitter.com" in url:
            return "Twitter"
        elif "tiktok.com" in url:
            return "TikTok"
        else:
            # Extract domain name
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                return domain.replace("www.", "").split(".")[0].title()
            except:
                return "Website"

    def get_video_info(self) -> Optional[Dict]:
        """Get current video information"""
        return self.video_info

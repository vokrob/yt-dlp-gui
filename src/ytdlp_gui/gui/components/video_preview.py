# -*- coding: utf-8 -*-
"""
Video Preview Component
Author: vokrob (Данил Борков)
Date: 18.07.2025
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import logging
from pathlib import Path
import requests
from PIL import Image
import io
import yt_dlp
import re
import json
from typing import Dict, Optional, Callable

from ytdlp_gui.core.cookie_manager import CookieManager

class VideoPreviewFrame(ctk.CTkFrame):
    """Frame for displaying video preview with title and thumbnail"""
    
    def __init__(self, parent, on_download_click: Optional[Callable] = None, settings_manager=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.on_download_click = on_download_click
        self.settings_manager = settings_manager

        # Initialize cookie manager if settings_manager is available
        self.cookie_manager = None
        if self.settings_manager:
            self.cookie_manager = CookieManager(self.settings_manager)

        # Video info
        self.video_info = None
        self.thumbnail_image = None
        self.loading_complete = False

        self.setup_ui()

    def _extract_title_from_html(self, url: str) -> Optional[str]:
        """Extract video title directly from YouTube HTML page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                # Don't specify Accept-Encoding to let requests handle it properly
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            html = response.text

            # Try multiple patterns to extract title with priorities
            patterns = [
                (r'<title>([^<]+)</title>', "HTML title tag", 10),
                (r'<meta name="title" content="([^"]+)"', "meta title", 9),
                (r'<meta property="og:title" content="([^"]+)"', "og:title meta", 9),
                (r'"videoDetails":{"videoId":"[^"]+","title":"([^"]+)"', "videoDetails object", 8),
                (r'<meta name="twitter:title" content="([^"]+)"', "twitter:title", 7),
                (r'"og:title" content="([^"]+)"', "og:title content", 6),
                (r'"title":"([^"]+)"', "JSON title field", 1),
            ]

            found_titles = []

            for pattern, description, priority in patterns:
                try:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        title = match.group(1)
                        # Clean up title
                        title = title.replace('\\u0026', '&').replace('\\', '').replace('\\"', '"')
                        # Remove " - YouTube" suffix if present
                        if title.endswith(' - YouTube'):
                            title = title[:-10]

                        # Skip obviously bad titles
                        if title.lower() in ['download unavailable', 'unavailable', 'error', 'blocked']:
                            continue

                        # Check if it's a valid title (not generic)
                        if title and len(title) > 5 and 'youtube video #' not in title.lower():
                            found_titles.append((priority, description, title))
                            self.logger.info(f"Found title via {description}: {title}")
                except Exception as e:
                    self.logger.warning(f"Error with pattern {description}: {e}")

            # Sort by priority and return the best one
            if found_titles:
                found_titles.sort(key=lambda x: x[0], reverse=True)
                best_priority, best_desc, best_title = found_titles[0]
                self.logger.info(f"Selected best title via {best_desc}: {best_title}")
                return best_title

            return None

        except Exception as e:
            self.logger.warning(f"Failed to extract title from HTML: {e}")
            return None

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
            text="⠋",
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
            # Smooth loading animation with Unicode spinner
            loading_states = [
                "⠋",
                "⠙",
                "⠹",
                "⠸",
                "⠼",
                "⠴",
                "⠦",
                "⠧",
                "⠇",
                "⠏"
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
        self.logger.info(f"Loading video info for URL: {url}")

        # Reset state and show loading
        self.start_loading_animation()

        # Load info in separate thread
        threading.Thread(target=self._fetch_video_info, args=(url,), daemon=True).start()
        
    def _fetch_video_info(self, url: str):
        """Fetch video information using yt-dlp (runs in separate thread)"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                # SETTINGS FOR GETTING ORIGINAL VIDEO VERSION
                'geo_bypass': False,  # Disable geo-bypass to preserve original audio track
                'prefer_original_language': True,  # Prefer original language
                # Force specific extractors
                'force_generic_extractor': False,
                # YouTube specific options
                'youtube_include_dash_manifest': True,
                'youtube_skip_dash_manifest': False,
                # Network options
                'socket_timeout': 30,
                'retries': 3,
                'fragment_retries': 3,
                # User agent and headers WITHOUT language preferences
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'referer': 'https://www.youtube.com/',
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                },
                # Additional bypass options
                'no_check_certificate': True,
                'prefer_insecure': False,
                'call_home': False,
            }

            # Add cookie options if available
            if self.cookie_manager:
                cookie_opts = self.cookie_manager.get_cookie_options(url)
                ydl_opts.update(cookie_opts)

            # Try multiple approaches to get video info
            info = None

            # First attempt: Standard extraction
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            except Exception as e:
                error_msg = str(e)
                self.logger.warning(f"Standard extraction failed: {error_msg}")

                # Check if this is an authentication error
                if self._is_authentication_error(error_msg, url):
                    self.after(0, lambda msg=error_msg: self._show_authentication_error(msg, url))
                    return

            # Second attempt: If title is generic, try with different options
            if info and (not info.get('title') or 'youtube video #' in info.get('title', '').lower()):
                self.logger.info("Got generic title, trying alternative extraction...")
                try:
                    # Try with different options
                    alt_opts = ydl_opts.copy()
                    alt_opts.update({
                        'youtube_include_dash_manifest': False,
                        'youtube_skip_dash_manifest': True,
                        'extract_flat': True,
                    })

                    with yt_dlp.YoutubeDL(alt_opts) as ydl:
                        alt_info = ydl.extract_info(url, download=False)
                        if alt_info and alt_info.get('title') and 'youtube video #' not in alt_info.get('title', '').lower():
                            info = alt_info
                except Exception as e:
                    self.logger.warning(f"Alternative extraction failed: {e}")

            # Third attempt: Try with minimal options if still no good title
            if info and (not info.get('title') or 'youtube video #' in info.get('title', '').lower()):
                self.logger.info("Still generic title, trying minimal extraction...")
                try:
                    minimal_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': False,
                        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    }

                    with yt_dlp.YoutubeDL(minimal_opts) as ydl:
                        min_info = ydl.extract_info(url, download=False)
                        if min_info and min_info.get('title') and 'youtube video #' not in min_info.get('title', '').lower():
                            info = min_info
                except Exception as e:
                    self.logger.warning(f"Minimal extraction failed: {e}")

            if info:
                # Check if we got a proper title
                title = info.get('title', 'Unknown Title')
                if 'youtube video #' in title.lower():
                    self.logger.info("Got generic title from yt-dlp, trying HTML extraction...")
                    # Try to extract title from HTML page
                    html_title = self._extract_title_from_html(url)
                    if html_title:
                        title = html_title
                    else:
                        # Fallback: extract video ID and create a better title
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

                # Update UI on main thread
                self.after(0, self._update_video_info)

                # Load thumbnail
                if self.video_info['thumbnail']:
                    self._load_thumbnail(self.video_info['thumbnail'])
                else:
                    # No thumbnail, show content anyway
                    self.after(0, self._finalize_loading)
            else:
                self.after(0, lambda: self._show_error("Could not load video information"))

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
            
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to readable string"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}:{secs:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}:{minutes:02d}:{secs:02d}"
            
    def _show_error(self, message: str):
        """Show error message"""
        self.title_label.configure(text="Error loading video")
        self.channel_label.configure(text="")
        self.thumbnail_label.configure(text=message)
        self.show_content()

    def _is_authentication_error(self, error_msg: str, url: str) -> bool:
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

    def _show_authentication_error(self, error_msg: str, url: str):
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

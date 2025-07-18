"""
URL Input Component - Handles URL input and validation
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import re
import threading
from typing import Callable, Optional

class URLInputFrame(ctk.CTkFrame):
    """Frame for URL input and validation"""
    
    def __init__(self, parent, on_url_change: Callable = None, on_add_to_queue: Callable = None):
        super().__init__(parent)
        
        self.on_url_change = on_url_change
        self.on_add_to_queue = on_add_to_queue
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        
        # URL Label
        url_label = ctk.CTkLabel(self, text="Video URL:", font=ctk.CTkFont(size=14, weight="bold"))
        url_label.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="w")
        
        # URL Entry
        self.url_entry = ctk.CTkEntry(
            self,
            placeholder_text="Paste URL...",
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.url_entry.grid(row=0, column=1, padx=(0, 10), pady=20, sticky="ew")
        self.url_entry.bind("<KeyRelease>", self.on_url_entry_change)
        self.url_entry.bind("<Return>", self.on_enter_pressed)

        # Add comprehensive paste support for different keyboard layouts
        # Standard Ctrl+V combinations
        self.url_entry.bind("<Control-v>", self.on_paste)
        self.url_entry.bind("<Control-V>", self.on_paste)

        # Alternative key combinations (without Russian symbols to avoid tkinter errors)
        self.url_entry.bind("<Control-Key-v>", self.on_paste)
        self.url_entry.bind("<Control-Key-V>", self.on_paste)

        # Middle mouse button for Linux
        self.url_entry.bind("<Button-2>", self.on_paste)

        # Right-click context menu with paste option
        self.url_entry.bind("<Button-3>", self.show_context_menu)

        # Universal key press handler for any Ctrl+V combination (handles Russian layout)
        self.url_entry.bind("<KeyPress>", self.on_key_press)
        
        # Download Button
        self.download_btn = ctk.CTkButton(
            self,
            text="Download",
            width=120,
            height=40,
            command=self.start_download,
            state="disabled"
        )
        self.download_btn.grid(row=0, column=2, padx=(0, 20), pady=20)
        
        # URL Status Label
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_label.grid(row=1, column=1, columnspan=4, padx=(0, 20), pady=(0, 15), sticky="w")
        
    def on_url_entry_change(self, event=None):
        """Handle URL entry changes"""
        url = self.url_entry.get().strip()
        
        if url:
            # Validate URL in a separate thread to avoid blocking UI
            threading.Thread(target=self.validate_url, args=(url,), daemon=True).start()
        else:
            self.update_status("", is_valid=False)
            
        # Notify parent of URL change
        if self.on_url_change:
            self.on_url_change(url)
            
    def validate_url(self, url: str):
        """Validate the URL (runs in separate thread)"""
        try:
            # Basic URL pattern validation
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)

            if url_pattern.match(url):
                # Check if it's a supported site (basic check)
                supported_domains = [
                    'youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com',
                    'twitch.tv', 'facebook.com', 'instagram.com', 'twitter.com',
                    'tiktok.com', 'soundcloud.com', 'bandcamp.com', 'vk.com', 'vkvideo.ru'
                ]

                domain_found = any(domain in url.lower() for domain in supported_domains)

                if domain_found or url_pattern.match(url):
                    self.update_status("", is_valid=True, color="gray")
                else:
                    self.update_status("", is_valid=False, color="gray")
            else:
                self.update_status("", is_valid=False, color="gray")

        except Exception as e:
            self.update_status("", is_valid=False, color="gray")
            
    def update_status(self, message: str, is_valid: bool, color: str = "gray"):
        """Update the status label (thread-safe)"""
        def update():
            self.status_label.configure(text=message, text_color=color)
            self.download_btn.configure(state="normal" if is_valid else "disabled")

        # Schedule update on main thread
        self.after(0, update)
        
    def start_download(self):
        """Start download immediately"""
        url = self.url_entry.get().strip()
        if url and self.on_add_to_queue:
            self.on_add_to_queue(url)

    def on_paste(self, event=None):
        """Handle paste operation"""
        try:
            # Get clipboard content using multiple methods
            clipboard_content = None

            # Method 1: Direct clipboard access
            try:
                clipboard_content = self.url_entry.clipboard_get()
            except:
                pass

            # Method 2: Try through root widget
            if not clipboard_content:
                try:
                    clipboard_content = self.winfo_toplevel().clipboard_get()
                except:
                    pass

            # Method 3: Try through tkinter
            if not clipboard_content:
                try:
                    import tkinter as tk
                    root = tk._default_root
                    if root:
                        clipboard_content = root.clipboard_get()
                except:
                    pass

            if clipboard_content and clipboard_content.strip():
                # Clear current content and insert clipboard content
                self.url_entry.delete(0, 'end')
                self.url_entry.insert(0, clipboard_content.strip())
                # Trigger validation
                self.on_url_entry_change()
                print(f"URL pasted from clipboard: {clipboard_content.strip()[:50]}...")
                return "break"  # Prevent default paste behavior
            else:
                print("Clipboard is empty or unavailable")

        except Exception as e:
            print(f"Paste error: {e}")
            # If clipboard access fails, allow default behavior
            pass
        return None

    def show_context_menu(self, event):
        """Show context menu with paste option"""
        try:
            import tkinter as tk

            # Create context menu
            context_menu = tk.Menu(self, tearoff=0)
            context_menu.add_command(label="Paste URL", command=self.on_paste)
            context_menu.add_separator()
            context_menu.add_command(label="Clear", command=lambda: self.url_entry.delete(0, 'end'))

            # Show menu at cursor position
            context_menu.tk_popup(event.x_root, event.y_root)

        except Exception as e:
            print(f"Context menu error: {e}")
        finally:
            # Clean up
            try:
                context_menu.grab_release()
            except:
                pass

    def on_enter_pressed(self, event=None):
        """Handle Enter key press"""
        if self.download_btn.cget("state") == "normal":
            self.start_download()
            
    def get_url(self) -> str:
        """Get the current URL"""
        return self.url_entry.get().strip()
        
    def set_url(self, url: str):
        """Set the URL"""
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
        self.on_url_entry_change()
        
    def focus_url_entry(self):
        """Focus the URL entry field"""
        self.url_entry.focus_set()

    def on_key_press(self, event):
        """Universal key press handler to catch Ctrl+V in any layout"""
        try:
            # Check if Ctrl is pressed
            if event.state & 0x4:  # Ctrl modifier
                # Check for V key (regardless of layout)
                # In Russian layout, 'v' becomes 'м', but we can catch both
                key_char = event.char.lower()
                key_keysym = event.keysym.lower()

                # Debug info
                print(f"Key pressed: char='{key_char}', keysym='{key_keysym}', state={event.state}")

                # Check for paste combinations
                if (key_char in ['v', 'м'] or
                    key_keysym in ['v', 'м', 'cyrillic_em'] or
                    event.keycode == 86):  # V key code

                    print("Paste combination detected!")
                    self.on_paste()
                    return "break"

        except Exception as e:
            print(f"Error in on_key_press: {e}")

        return None

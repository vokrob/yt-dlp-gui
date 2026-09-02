# -*- coding: utf-8 -*-
"""
Settings Manager
Author: vokrob
Date: 18.07.2025
"""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any
import os


def _write_json_with_timeout(path: Path, data: Dict[str, Any], timeout: float = 3.0) -> bool:
    """Write JSON to disk in a worker thread with a hard timeout.

    Same reasoning as DownloadManager.save_queue: a stuck/redirected filesystem
    must never block the app (e.g. when saving settings on exit).
    """
    result = [False]

    def _do_write():
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            result[0] = True
        except Exception:
            pass

    thread = threading.Thread(target=_do_write, daemon=True)
    thread.start()
    thread.join(timeout)
    return result[0]

class SettingsManager:
    """Settings manager"""
    
    DEFAULT_SETTINGS = {
        'output_directory': str(Path.home() / 'Desktop'),
        'max_concurrent_downloads': 3,
        'proxy_enabled': False,
        'proxy_url': '',
        'cookies_enabled': True,
        'cookies_browser': 'chrome',  # Default browser for cookie extraction
        'cookies_fallback_browsers': ['chrome', 'firefox', 'edge', 'safari'],
        'notification_enabled': True,
        'last_update_check_time': 0.0,  # Timestamp of last update check
        'latest_update_info': '',  # Cached update info JSON string
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings_dir = self._get_settings_directory()
        self.settings_file = self.settings_dir / 'settings.json'
        self.settings = self.DEFAULT_SETTINGS.copy()
        
        # Ensure settings directory exists
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing settings
        self.load_settings()
        
    def _get_settings_directory(self) -> Path:
        """Get the appropriate settings directory for the current OS"""
        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get('APPDATA', Path.home()))
        elif os.name == 'posix':
            if 'darwin' in os.uname().sysname.lower():  # macOS
                base_dir = Path.home() / 'Library' / 'Application Support'
            else:  # Linux and other Unix-like
                base_dir = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
        else:
            base_dir = Path.home()
            
        return base_dir / 'yt-dlp-gui'
        
    def load_settings(self):
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    
                # Merge with defaults (in case new settings were added)
                self.settings.update(saved_settings)
                
                self.logger.info("Settings loaded successfully")
            else:
                self.logger.info("No settings file found, using defaults")
                
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            self.logger.info("Using default settings")
            
    def save_settings(self):
        """Save current settings to file"""
        try:
            if not _write_json_with_timeout(self.settings_file, self.settings):
                self.logger.warning("Settings save skipped (filesystem did not respond in time)")
                return

            self.logger.info("Settings saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set a setting value"""
        self.settings[key] = value
        
    def get_output_directory(self) -> str:
        """Get the current output directory"""
        output_dir = self.get('output_directory')
        
        # Ensure the directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        return output_dir

    def get_network_settings(self) -> Dict[str, Any]:
        """Get network-related settings"""
        return {
            'proxy_enabled': self.get('proxy_enabled'),
            'proxy_url': self.get('proxy_url'),
            'cookies_enabled': self.get('cookies_enabled'),
            'cookies_browser': self.get('cookies_browser'),
            'cookies_fallback_browsers': self.get('cookies_fallback_browsers'),
        }


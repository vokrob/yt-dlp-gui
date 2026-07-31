# -*- coding: utf-8 -*-
"""
Settings Manager
Author: vokrob
Date: 18.07.2025
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
import os

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
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
                
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


# -*- coding: utf-8 -*-
"""
Settings Manager
Author: vokrob (Данил Борков)
Date: 18.07.2025
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import os

class SettingsManager:
    """Settings manager"""
    
    DEFAULT_SETTINGS = {
        'output_directory': str(Path.home() / 'Desktop'),
        'default_format': 'best',
        'audio_format': 'mp3',
        'audio_quality': '192',
        'video_quality': 'best',
        'max_concurrent_downloads': 3,
        'write_thumbnail': False,
        'write_subtitles': False,
        'write_info_json': False,
        'theme': 'dark',
        'window_geometry': '1000x700',
        'auto_start_downloads': True,
        'notification_enabled': True,
        'keep_video_after_audio_extraction': False,
        'custom_filename_template': '%(title)s.%(ext)s',
        'proxy_enabled': False,
        'proxy_url': '',
        'rate_limit': '',
        'retries': 3,
        'fragment_retries': 3,
        'skip_unavailable_fragments': True,
        'cookies_enabled': True,
        'cookies_browser': 'chrome',  # Default browser for cookie extraction
        'cookies_fallback_browsers': ['chrome', 'firefox', 'edge', 'safari'],
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
        
    def set_output_directory(self, path: str):
        """Set the output directory"""
        self.set('output_directory', path)
        
    def get_format_settings(self) -> Dict[str, Any]:
        """Get format-related settings"""
        return {
            'default_format': self.get('default_format'),
            'audio_format': self.get('audio_format'),
            'audio_quality': self.get('audio_quality'),
            'video_quality': self.get('video_quality'),
        }
        
    def get_download_settings(self) -> Dict[str, Any]:
        """Get download-related settings"""
        return {
            'max_concurrent_downloads': self.get('max_concurrent_downloads'),
            'auto_start_downloads': self.get('auto_start_downloads'),
            'retries': self.get('retries'),
            'fragment_retries': self.get('fragment_retries'),
            'skip_unavailable_fragments': self.get('skip_unavailable_fragments'),
            'rate_limit': self.get('rate_limit'),
        }
        
    def get_output_settings(self) -> Dict[str, Any]:
        """Get output-related settings"""
        return {
            'write_thumbnail': self.get('write_thumbnail'),
            'write_subtitles': self.get('write_subtitles'),
            'write_info_json': self.get('write_info_json'),
            'keep_video_after_audio_extraction': self.get('keep_video_after_audio_extraction'),
            'custom_filename_template': self.get('custom_filename_template'),
        }
        
    def get_network_settings(self) -> Dict[str, Any]:
        """Get network-related settings"""
        return {
            'proxy_enabled': self.get('proxy_enabled'),
            'proxy_url': self.get('proxy_url'),
            'cookies_enabled': self.get('cookies_enabled'),
            'cookies_browser': self.get('cookies_browser'),
            'cookies_fallback_browsers': self.get('cookies_fallback_browsers'),
        }
        
    def get_ui_settings(self) -> Dict[str, Any]:
        """Get UI-related settings"""
        return {
            'theme': self.get('theme'),
            'window_geometry': self.get('window_geometry'),
            'notification_enabled': self.get('notification_enabled'),
        }
        
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.save_settings()
        self.logger.info("Settings reset to defaults")
        
    def export_settings(self, file_path: str) -> bool:
        """Export settings to a file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            return False
            
    def import_settings(self, file_path: str) -> bool:
        """Import settings from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
                
            # Validate imported settings
            if isinstance(imported_settings, dict):
                # Only update valid settings
                for key, value in imported_settings.items():
                    if key in self.DEFAULT_SETTINGS:
                        self.settings[key] = value
                        
                self.save_settings()
                return True
            else:
                self.logger.error("Invalid settings file format")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            return False
            
    def validate_settings(self) -> Dict[str, str]:
        """Validate current settings and return any errors"""
        errors = {}
        
        # Validate output directory
        output_dir = self.get('output_directory')
        if not output_dir:
            errors['output_directory'] = "Output directory cannot be empty"
        else:
            try:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            except Exception:
                errors['output_directory'] = "Invalid output directory path"
                
        # Validate concurrent downloads
        max_downloads = self.get('max_concurrent_downloads')
        if not isinstance(max_downloads, int) or max_downloads < 1 or max_downloads > 10:
            errors['max_concurrent_downloads'] = "Must be between 1 and 10"
            
        # Validate audio quality
        audio_quality = self.get('audio_quality')
        if audio_quality not in ['64', '128', '192', '256', '320']:
            errors['audio_quality'] = "Invalid audio quality"
            
        # Validate proxy URL if enabled
        if self.get('proxy_enabled'):
            proxy_url = self.get('proxy_url')
            if not proxy_url:
                errors['proxy_url'] = "Proxy URL required when proxy is enabled"
                
        return errors

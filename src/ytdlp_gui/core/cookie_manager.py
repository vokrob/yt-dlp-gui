# -*- coding: utf-8 -*-
"""
Cookie Manager
Author: vokrob (Данил Борков)
Date: 18.07.2025
"""

import logging
import platform
from typing import Dict, List, Optional, Any
from pathlib import Path


class CookieManager:
    """Cookie manager"""

    def __init__(self, settings_manager):
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager

        self.browser_priority = [
            'chrome',
            'firefox',
            'edge',
            'safari',
            'chromium',
            'opera',
        ]

        self.site_browser_preferences = {
            'vk.com': ['edge', 'chrome', 'firefox'],
            'vkvideo.ru': ['edge', 'chrome', 'firefox'],
        }
        
    def get_cookie_options(self, url: str = None) -> Dict[str, Any]:
        """
        Get yt-dlp cookie options based on current settings
        Returns dictionary with cookie-related yt-dlp options
        """
        network_settings = self.settings_manager.get_network_settings()

        if not network_settings.get('cookies_enabled', True):
            return {}

        # Try to get cookies from preferred browser
        preferred_browser = network_settings.get('cookies_browser', 'chrome')
        fallback_browsers = network_settings.get('cookies_fallback_browsers', [])

        # Check if we have site-specific browser preferences
        site_browsers = None
        if url:
            for site, browsers in self.site_browser_preferences.items():
                if site in url.lower():
                    site_browsers = browsers
                    self.logger.info(f"Using site-specific browser preferences for {site}: {browsers}")
                    break

        # Create list of browsers to try
        if site_browsers:
            # Use site-specific preferences first
            browsers_to_try = site_browsers.copy()
            # Add user preferences if not already included
            if preferred_browser not in browsers_to_try:
                browsers_to_try.append(preferred_browser)
            for browser in fallback_browsers:
                if browser not in browsers_to_try:
                    browsers_to_try.append(browser)
        else:
            # Use normal preferences
            browsers_to_try = [preferred_browser]
            for browser in fallback_browsers:
                if browser not in browsers_to_try:
                    browsers_to_try.append(browser)

        # Add remaining browsers from priority list
        for browser in self.browser_priority:
            if browser not in browsers_to_try:
                browsers_to_try.append(browser)

        # Try each browser until one works
        for browser in browsers_to_try:
            if self._is_browser_available(browser):
                self.logger.info(f"Using cookies from {browser}")
                cookie_options = {
                    'cookiesfrombrowser': (browser, None, None, None)
                }

                # Add site-specific options
                if url:
                    cookie_options.update(self._get_site_specific_options(url))

                return cookie_options

        # If no browser cookies available, log warning but don't fail
        self.logger.warning("No browser cookies available, proceeding without cookies")
        return {}
    
    def _is_browser_available(self, browser: str) -> bool:
        """Check if a browser is available on the current system"""
        try:
            system = platform.system().lower()
            
            if browser == 'chrome':
                return self._check_chrome_available(system)
            elif browser == 'firefox':
                return self._check_firefox_available(system)
            elif browser == 'edge':
                return self._check_edge_available(system)
            elif browser == 'safari':
                return system == 'darwin' and self._check_safari_available()
            elif browser == 'chromium':
                return self._check_chromium_available(system)
            elif browser == 'opera':
                return self._check_opera_available(system)
                
        except Exception as e:
            self.logger.debug(f"Error checking {browser} availability: {e}")
            
        return False
    
    def _check_chrome_available(self, system: str) -> bool:
        """Check if Chrome is available"""
        if system == 'windows':
            paths = [
                Path.home() / 'AppData/Local/Google/Chrome/User Data',
                Path('C:/Program Files/Google/Chrome/Application/chrome.exe'),
                Path('C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'),
            ]
        elif system == 'darwin':  # macOS
            paths = [
                Path.home() / 'Library/Application Support/Google/Chrome',
                Path('/Applications/Google Chrome.app'),
            ]
        else:  # Linux
            paths = [
                Path.home() / '.config/google-chrome',
                Path('/usr/bin/google-chrome'),
                Path('/usr/bin/chrome'),
            ]
            
        return any(path.exists() for path in paths)
    
    def _check_firefox_available(self, system: str) -> bool:
        """Check if Firefox is available"""
        if system == 'windows':
            paths = [
                Path.home() / 'AppData/Roaming/Mozilla/Firefox',
                Path('C:/Program Files/Mozilla Firefox/firefox.exe'),
                Path('C:/Program Files (x86)/Mozilla Firefox/firefox.exe'),
            ]
        elif system == 'darwin':  # macOS
            paths = [
                Path.home() / 'Library/Application Support/Firefox',
                Path('/Applications/Firefox.app'),
            ]
        else:  # Linux
            paths = [
                Path.home() / '.mozilla/firefox',
                Path('/usr/bin/firefox'),
            ]
            
        return any(path.exists() for path in paths)
    
    def _check_edge_available(self, system: str) -> bool:
        """Check if Edge is available"""
        if system == 'windows':
            paths = [
                Path.home() / 'AppData/Local/Microsoft/Edge/User Data',
                Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'),
            ]
        elif system == 'darwin':  # macOS
            paths = [
                Path.home() / 'Library/Application Support/Microsoft Edge',
                Path('/Applications/Microsoft Edge.app'),
            ]
        else:  # Linux
            paths = [
                Path.home() / '.config/microsoft-edge',
                Path('/usr/bin/microsoft-edge'),
            ]
            
        return any(path.exists() for path in paths)
    
    def _check_safari_available(self) -> bool:
        """Check if Safari is available (macOS only)"""
        paths = [
            Path.home() / 'Library/Safari',
            Path('/Applications/Safari.app'),
        ]
        return any(path.exists() for path in paths)
    
    def _check_chromium_available(self, system: str) -> bool:
        """Check if Chromium is available"""
        if system == 'windows':
            paths = [
                Path.home() / 'AppData/Local/Chromium/User Data',
            ]
        elif system == 'darwin':  # macOS
            paths = [
                Path.home() / 'Library/Application Support/Chromium',
                Path('/Applications/Chromium.app'),
            ]
        else:  # Linux
            paths = [
                Path.home() / '.config/chromium',
                Path('/usr/bin/chromium'),
                Path('/usr/bin/chromium-browser'),
            ]
            
        return any(path.exists() for path in paths)
    
    def _check_opera_available(self, system: str) -> bool:
        """Check if Opera is available"""
        if system == 'windows':
            paths = [
                Path.home() / 'AppData/Roaming/Opera Software/Opera Stable',
            ]
        elif system == 'darwin':  # macOS
            paths = [
                Path.home() / 'Library/Application Support/com.operasoftware.Opera',
                Path('/Applications/Opera.app'),
            ]
        else:  # Linux
            paths = [
                Path.home() / '.config/opera',
                Path('/usr/bin/opera'),
            ]
            
        return any(path.exists() for path in paths)

    def _get_site_specific_options(self, url: str) -> Dict[str, Any]:
        """Get site-specific options for better compatibility"""
        options = {}

        if "vk.com" in url or "vkvideo.ru" in url:
            # VK-specific options
            options.update({
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'referer': 'https://vk.com/',
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                }
            })
        elif "youtube.com" in url or "youtu.be" in url:
            # YouTube-specific options
            options.update({
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'referer': 'https://www.youtube.com/',
            })

        return options

    def get_available_browsers(self) -> List[str]:
        """Get list of available browsers on the current system"""
        available = []
        for browser in self.browser_priority:
            if self._is_browser_available(browser):
                available.append(browser)
        return available
    
    def test_cookie_extraction(self, browser: str) -> bool:
        """Test if cookie extraction works for a specific browser"""
        try:
            # This is a simple test - in practice, yt-dlp will handle the actual extraction
            return self._is_browser_available(browser)
        except Exception as e:
            self.logger.error(f"Cookie extraction test failed for {browser}: {e}")
            return False

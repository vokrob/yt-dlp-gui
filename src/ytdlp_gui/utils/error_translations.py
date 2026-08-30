# -*- coding: utf-8 -*-
"""
Human-readable translations of common yt-dlp errors.
Author: vokrob
"""

import re

ERROR_TRANSLATIONS = [
    (r'failed to decrypt with DPAPI', 'Browser cookies are encrypted (Chrome/Edge App Bound Encryption) and cannot be read. Public videos download fine without cookies; for login-only videos export cookies via the "Get cookies.txt" extension and place cookies.txt next to the app'),
    (r'unable to download video data.*HTTP Error 403', 'YouTube blocked the download. Browser cookies are outdated - export new ones via Get cookies.txt extension and place cookies.txt next to the program'),
    (r'Unable to download M3U8|Failed to download M3U8|m3u8.*(?:error|failed)', 'Could not download the stream (HLS). The video may be region-locked or need cookies - try adding cookies.txt next to the program'),
    (r'Unable to download (?:fragment|segment).*HTTP Error 40[13]', 'Stream fragment blocked (HTTP 40x). Try adding cookies.txt next to the program'),
    (r'Server returned 40[13]|403 Forbidden', 'Access denied (HTTP 403). Try adding cookies.txt next to the program'),
    (r'HTTP Error 40[13]', 'Access denied (HTTP 40x). Try adding cookies.txt next to the program'),
    (r'HTTP Error 404', 'Video not found (HTTP 404). It may have been deleted or the link is wrong'),
    (r'HTTP Error 429', 'Too many requests. Wait a few minutes and try again'),
    (r'HTTP Error 5\d{2}', 'Server error (HTTP 5xx). Try again later'),
    (r'Sign in to confirm', 'YouTube requires confirmation. Export browser cookies to cookies.txt and place next to the program'),
    (r'confirm your age', 'Age restriction. Add cookies.txt from an account with confirmed age'),
    (r'video\s+(?:is\s+)?unavailable', 'Video unavailable. It may have been deleted or is accessible by link only'),
    (r'This video is private', 'This is a private video. Add cookies.txt from an account that has access'),
    (r'ffprobe.*not found', 'FFmpeg not found - check your internet connection and restart the program'),
    (r'ffmpeg.*not found', 'FFmpeg not found - check your internet connection and restart the program'),
    (r'No video formats found', 'Could not get video formats. The video may be unavailable in your region'),
    (r'Unable to extract', 'Could not process the page. The site may have changed or cookies are needed'),
    (r'requested format not available', 'Requested quality is not available. Try another one'),
    (r'ConnectionError.*reset', 'Connection reset. Check your internet and VPN'),
    (r'Timeout', 'Connection timeout. Check your internet or try again later'),
    (r'Certificate verify failed', 'SSL certificate error. Check the date and time on your computer'),
    (r'Cloudflare', 'Blocked by Cloudflare protection. Try a VPN or add cookies.txt'),
    (r'\[Errno \d+\]|Name or service not known|Temporary failure in name resolution|Network is unreachable|No route to host|getaddrinfo failed', 'Network error - check your internet connection and VPN'),
]


def translate_error(error: Exception) -> str:
    """Convert common yt-dlp errors to human-readable messages"""
    error_str = str(error)
    for pattern, message in ERROR_TRANSLATIONS:
        if re.search(pattern, error_str, re.IGNORECASE):
            return message
    # Fallback: truncate raw error
    if len(error_str) > 200:
        return error_str[:200] + '...'
    return error_str
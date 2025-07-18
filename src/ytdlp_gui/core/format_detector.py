# -*- coding: utf-8 -*-
"""
Format Detector
Author: vokrob (Данил Борков)
Date: 18.07.2025
"""

import yt_dlp
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .cookie_manager import CookieManager

@dataclass
class FormatInfo:
    """Information about a video format"""
    format_id: str
    ext: str
    resolution: str
    fps: Optional[int]
    vcodec: str
    acodec: str
    filesize: Optional[int]
    tbr: Optional[float]  # Total bitrate
    vbr: Optional[float]  # Video bitrate
    abr: Optional[float]  # Audio bitrate
    format_note: str
    quality: int  # Quality ranking (higher is better)
    
    def __str__(self):
        size_str = f" ({self._format_filesize()})" if self.filesize else ""
        return f"{self.resolution} {self.ext} - {self.format_note}{size_str}"
        
    def _format_filesize(self) -> str:
        """Format filesize to human readable string"""
        if not self.filesize:
            return ""
            
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.filesize < 1024.0:
                return f"{self.filesize:.1f} {unit}"
            self.filesize /= 1024.0
        return f"{self.filesize:.1f} TB"

class FormatDetector:
    """Detects and analyzes available formats for videos"""

    def __init__(self, settings_manager=None):
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager

        # Initialize cookie manager if settings_manager is available
        self.cookie_manager = None
        if self.settings_manager:
            self.cookie_manager = CookieManager(self.settings_manager)
        
    def get_available_formats(self, url: str) -> Tuple[List[FormatInfo], List[FormatInfo], Dict]:
        """
        Get available formats for a URL
        Returns: (video_formats, audio_formats, video_info)
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'listformats': False,
                'extract_flat': False,
                # SETTINGS FOR GETTING ORIGINAL VIDEO VERSION
                'geo_bypass': False,  # Disable geo-bypass to preserve original audio track
                'prefer_original_language': True,  # Prefer original language
                'ignoreerrors': False,
                'no_check_certificate': True,
                # User agent WITHOUT language preferences
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                # Headers WITHOUT language preferences
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            }

            # Add cookie options if available
            if self.cookie_manager:
                cookie_opts = self.cookie_manager.get_cookie_options(url)
                ydl_opts.update(cookie_opts)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return [], [], {}
                    
                formats = info.get('formats', [])
                
                # Separate video and audio formats
                video_formats = []
                audio_formats = []
                
                for fmt in formats:
                    format_info = self._parse_format(fmt)
                    
                    if format_info.vcodec != 'none' and format_info.acodec != 'none':
                        # Combined video+audio format
                        video_formats.append(format_info)
                    elif format_info.vcodec != 'none':
                        # Video-only format
                        video_formats.append(format_info)
                    elif format_info.acodec != 'none':
                        # Audio-only format
                        audio_formats.append(format_info)
                        
                # Sort formats by quality
                video_formats.sort(key=lambda x: x.quality, reverse=True)
                audio_formats.sort(key=lambda x: x.quality, reverse=True)
                
                # Extract basic video info
                video_info = {
                    'title': info.get('title', 'Unknown'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', ''),
                    'description': info.get('description', ''),
                    'thumbnail': info.get('thumbnail', ''),
                }
                
                return video_formats, audio_formats, video_info
                
        except Exception as e:
            self.logger.error(f"Failed to get formats for {url}: {e}")
            return [], [], {}
            
    def _parse_format(self, fmt: Dict) -> FormatInfo:
        """Parse a format dictionary into FormatInfo"""
        # Extract basic information
        format_id = fmt.get('format_id', '')
        ext = fmt.get('ext', 'unknown')
        vcodec = fmt.get('vcodec', 'none')
        acodec = fmt.get('acodec', 'none')
        
        # Resolution
        width = fmt.get('width')
        height = fmt.get('height')
        if width and height:
            resolution = f"{width}x{height}"
        elif height:
            resolution = f"{height}p"
        else:
            resolution = "unknown"
            
        # Bitrates
        tbr = fmt.get('tbr')  # Total bitrate
        vbr = fmt.get('vbr')  # Video bitrate
        abr = fmt.get('abr')  # Audio bitrate
        
        # File size
        filesize = fmt.get('filesize') or fmt.get('filesize_approx')
        
        # FPS
        fps = fmt.get('fps')
        
        # Format note
        format_note = fmt.get('format_note', '') or fmt.get('format', '')
        
        # Calculate quality ranking
        quality = self._calculate_quality_score(fmt)
        
        return FormatInfo(
            format_id=format_id,
            ext=ext,
            resolution=resolution,
            fps=fps,
            vcodec=vcodec,
            acodec=acodec,
            filesize=filesize,
            tbr=tbr,
            vbr=vbr,
            abr=abr,
            format_note=format_note,
            quality=quality
        )
        
    def _calculate_quality_score(self, fmt: Dict) -> int:
        """Calculate a quality score for ranking formats"""
        score = 0
        
        # Resolution score
        height = fmt.get('height', 0) or 0
        if height >= 2160:  # 4K
            score += 1000
        elif height >= 1440:  # 1440p
            score += 800
        elif height >= 1080:  # 1080p
            score += 600
        elif height >= 720:  # 720p
            score += 400
        elif height >= 480:  # 480p
            score += 200
        elif height >= 360:  # 360p
            score += 100
            
        # Bitrate score
        tbr = fmt.get('tbr', 0) or 0
        score += min(tbr, 500)  # Cap at 500 to prevent extreme values
        
        # Codec preference
        vcodec = fmt.get('vcodec', '')
        if 'av01' in vcodec:  # AV1
            score += 50
        elif 'vp9' in vcodec:  # VP9
            score += 30
        elif 'h264' in vcodec or 'avc' in vcodec:  # H.264
            score += 20
            
        acodec = fmt.get('acodec', '')
        if 'opus' in acodec:
            score += 15
        elif 'aac' in acodec:
            score += 10
        elif 'mp3' in acodec:
            score += 5
            
        # Prefer combined formats over separate video/audio
        if fmt.get('vcodec', 'none') != 'none' and fmt.get('acodec', 'none') != 'none':
            score += 100
            
        return score
        
    def get_best_format(self, url: str, prefer_audio_only: bool = False) -> Optional[FormatInfo]:
        """Get the best available format for a URL"""
        try:
            video_formats, audio_formats, _ = self.get_available_formats(url)
            
            if prefer_audio_only and audio_formats:
                return audio_formats[0]  # Already sorted by quality
            elif video_formats:
                return video_formats[0]  # Already sorted by quality
            elif audio_formats:
                return audio_formats[0]  # Fallback to audio
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get best format: {e}")
            return None
            
    def get_format_by_quality(self, url: str, quality: str) -> Optional[FormatInfo]:
        """Get format by quality preference (e.g., '720p', '1080p', 'best', 'worst')"""
        try:
            video_formats, audio_formats, _ = self.get_available_formats(url)
            
            if quality == 'best':
                return video_formats[0] if video_formats else None
            elif quality == 'worst':
                return video_formats[-1] if video_formats else None
            else:
                # Look for specific quality
                for fmt in video_formats:
                    if quality in fmt.resolution:
                        return fmt
                        
                # If not found, return best
                return video_formats[0] if video_formats else None
                
        except Exception as e:
            self.logger.error(f"Failed to get format by quality: {e}")
            return None
            
    def is_playlist(self, url: str) -> bool:
        """Check if URL is a playlist"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info and info.get('_type') == 'playlist'
                
        except Exception:
            return False
            
    def get_playlist_info(self, url: str) -> Dict:
        """Get playlist information"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info and info.get('_type') == 'playlist':
                    return {
                        'title': info.get('title', 'Unknown Playlist'),
                        'uploader': info.get('uploader', 'Unknown'),
                        'entry_count': len(info.get('entries', [])),
                        'entries': info.get('entries', []),
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to get playlist info: {e}")
            
        return {}

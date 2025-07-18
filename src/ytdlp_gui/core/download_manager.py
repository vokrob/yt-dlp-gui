# -*- coding: utf-8 -*-
"""
Download Manager
Author: vokrob (Данил Борков)
Date: 18.07.2025
"""

import yt_dlp
import threading
import queue
import logging
import time
import json
import requests
import re
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid

from .cookie_manager import CookieManager

class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

@dataclass
class DownloadItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    url: str = ""
    title: str = ""
    format_info: Dict = field(default_factory=dict)
    output_path: str = ""
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    file_size: str = ""
    downloaded_bytes: int = 0
    total_bytes: int = 0
    error_message: str = ""
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

class DownloadManager:
    """Download manager"""

    def __init__(self, settings_manager):
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager
        self.cookie_manager = CookieManager(settings_manager)
        self.download_queue: List[DownloadItem] = []
        self.active_downloads: Dict[str, threading.Thread] = {}
        self.download_callbacks: List[Callable] = []
        self.queue_lock = threading.Lock()
        self.max_concurrent_downloads = settings_manager.get('max_concurrent_downloads', 3)
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        self.queue_file = self._get_queue_file_path()

        from ytdlp_gui.core.history_manager import HistoryManager
        self.history_manager = HistoryManager(settings_manager)

        # Notification system
        try:
            from ytdlp_gui.utils.notifications import get_notification_manager, get_error_handler
            from ytdlp_gui.utils.logger import log_download_event
            self.notification_manager = get_notification_manager()
            self.error_handler = get_error_handler()
            self.log_download_event = log_download_event
        except ImportError:
            # Fallback if notification system not available
            self.notification_manager = None
            self.error_handler = None
            self.log_download_event = lambda *args: None

        # Load saved queue
        self.load_queue()
        
    def add_download(self, url: str, format_info: Dict, output_path: str, video_title: str = None) -> str:
        """Add a new download to the queue"""
        try:
            # Create download item
            download_item = DownloadItem(
                url=url,
                format_info=format_info,
                output_path=output_path
            )

            # Use provided title if available, otherwise get video info
            if video_title:
                download_item.title = video_title
                self.logger.info(f"Using provided title: '{video_title}'")
            else:
                # Get video info to populate title
                self._get_video_info(download_item)
            
            with self.queue_lock:
                self.download_queue.append(download_item)

            self.logger.info(f"Added download: {download_item.title} ({download_item.id})")
            self.log_download_event("ADDED", url, download_item.title)

            # Save queue and notify changes
            self.save_queue()
            self._notify_queue_change()

            # Start download if possible
            self._process_queue()

            return download_item.id
            
        except Exception as e:
            self.logger.error(f"Failed to add download: {e}")
            raise
            
    def remove_download(self, download_id: str) -> bool:
        """Remove a download from the queue"""
        try:
            with self.queue_lock:
                # Find and remove the download
                for i, item in enumerate(self.download_queue):
                    if item.id == download_id:
                        # Cancel if currently downloading
                        if download_id in self.active_downloads:
                            self._cancel_download(download_id)
                        
                        del self.download_queue[i]
                        self.logger.info(f"Removed download: {download_id}")

                        # Save queue and notify changes
                        self.save_queue()
                        self._notify_queue_change()
                        return True
                        
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to remove download: {e}")
            return False
            
    def pause_download(self, download_id: str) -> bool:
        """Pause a download"""
        # Note: yt-dlp doesn't support pausing, so we'll cancel and mark as paused
        try:
            item = self.get_download_item(download_id)
            if item and item.status == DownloadStatus.DOWNLOADING:
                self._cancel_download(download_id)
                item.status = DownloadStatus.PAUSED
                self._notify_progress_change(download_id)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to pause download: {e}")
            return False
            
    def resume_download(self, download_id: str) -> bool:
        """Resume a paused download"""
        try:
            item = self.get_download_item(download_id)
            if item and item.status == DownloadStatus.PAUSED:
                item.status = DownloadStatus.PENDING
                self._process_queue()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to resume download: {e}")
            return False
            
    def get_queue(self) -> List[DownloadItem]:
        """Get the current download queue"""
        with self.queue_lock:
            return self.download_queue.copy()
            
    def get_download_item(self, download_id: str) -> Optional[DownloadItem]:
        """Get a specific download item"""
        with self.queue_lock:
            for item in self.download_queue:
                if item.id == download_id:
                    return item
            return None
            
    def add_progress_callback(self, download_id: str, callback: Callable):
        """Add a progress callback for a specific download"""
        if download_id not in self.progress_callbacks:
            self.progress_callbacks[download_id] = []
        self.progress_callbacks[download_id].append(callback)
        
    def add_queue_callback(self, callback: Callable):
        """Add a callback for queue changes"""
        self.download_callbacks.append(callback)
        
    def stop_all_downloads(self):
        """Stop all active downloads"""
        with self.queue_lock:
            for download_id in list(self.active_downloads.keys()):
                self._cancel_download(download_id)

        # Save queue state
        self.save_queue()

    def _extract_title_from_html(self, url: str) -> Optional[str]:
        """Extract video title directly from YouTube HTML page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                # Omit Accept-Language to get original video version
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

    def _get_video_info(self, download_item: DownloadItem):
        """Get video information without downloading"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                # Video extraction settings for original content
                'geo_bypass': False,  # Preserve regional settings
                'prefer_original_language': True,  # Prefer original language
                # HTTP headers for content localization
                'http_headers': {
                    'Accept-Language': 'ru-RU,ru;q=0.9',  # Russian language preference
                },
                'writeautomaticsub': False,  # Skip automatic subtitles
                'writesubtitles': False,  # Skip subtitles
                # YouTube specific options
                'youtube_include_dash_manifest': True,
                'youtube_skip_dash_manifest': False,
                # Network options
                'socket_timeout': 30,
                'retries': 3,
                'fragment_retries': 3,
                # Stability settings
                # Additional bypass options
                'no_check_certificate': True,
                'prefer_insecure': False,
                'call_home': False,
            }

            # Add cookies for original content access
            cookie_opts = self.cookie_manager.get_cookie_options(download_item.url)
            if cookie_opts:
                ydl_opts.update(cookie_opts)
                self.logger.info("Using cookies for video info extraction to get original language")

            # Try to get video info with fallback for generic titles
            info = None
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(download_item.url, download=False)

            if info:
                # Use HTML extraction for titles
                self.logger.info("Using HTML extraction for title (bypasses time/region issues)")
                html_title = self._extract_title_from_html(download_item.url)

                if html_title:
                    title = html_title
                    self.logger.info(f"HTML title extracted: '{title}'")
                else:
                    # Fallback на yt-dlp только если HTML не сработал
                    title = info.get('title', 'Unknown Title')
                    self.logger.warning(f"HTML extraction failed, using yt-dlp title: '{title}'")

                download_item.title = title
                download_item.file_size = self._format_bytes(info.get('filesize') or 0)
                    
        except Exception as e:
            self.logger.warning(f"Failed to get video info: {e}")
            # Try HTML extraction as last resort before fallback
            html_title = self._extract_title_from_html(download_item.url)
            if html_title:
                download_item.title = html_title
                self.logger.info(f"Fallback HTML title extracted: '{html_title}'")
            else:
                download_item.title = f"Video from {download_item.url}"
            
    def _process_queue(self):
        """Process the download queue"""
        with self.queue_lock:
            # Count active downloads
            active_count = len(self.active_downloads)
            
            if active_count >= self.max_concurrent_downloads:
                return
                
            # Find next pending download
            for item in self.download_queue:
                if item.status == DownloadStatus.PENDING:
                    self._start_download(item)
                    break
                    
    def _start_download(self, download_item: DownloadItem):
        """Start downloading a specific item"""
        try:
            download_item.status = DownloadStatus.DOWNLOADING
            
            # Create download thread
            thread = threading.Thread(
                target=self._download_worker,
                args=(download_item,),
                daemon=True
            )
            
            self.active_downloads[download_item.id] = thread
            thread.start()
            
            self.logger.info(f"Started download: {download_item.title}")
            self._notify_progress_change(download_item.id)
            
        except Exception as e:
            self.logger.error(f"Failed to start download: {e}")
            download_item.status = DownloadStatus.FAILED
            download_item.error_message = str(e)
            self._notify_progress_change(download_item.id)
            
    def _download_worker(self, download_item: DownloadItem):
        """Worker thread for downloading"""
        try:
            # Prepare yt-dlp options
            ydl_opts = self._prepare_ydl_options(download_item)
            
            # Add progress hook
            ydl_opts['progress_hooks'] = [
                lambda d: self._progress_hook(d, download_item.id)
            ]

            # Add postprocessor hook for merger progress
            ydl_opts['postprocessor_hooks'] = [
                lambda d: self._postprocessor_hook(d, download_item.id)
            ]
            
            # Start download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Сохраняем селектор формата для проверки слияния
                format_selector = ydl_opts.get('format', '')
                self._current_format_selector = format_selector

                if '+' in format_selector or 'bestvideo' in format_selector:
                    self.logger.info(f"Format selector '{format_selector}' may require merging")

                ydl.download([download_item.url])

                # После завершения загрузки, показываем индикатор слияния если нужно
                if '+' in format_selector or 'bestvideo' in format_selector:
                    # Показываем индикатор слияния
                    download_item.speed = 'Merging formats...'
                    download_item.eta = 'Processing'
                    download_item.progress = 100
                    self.logger.info(f"Post-download merger indicator for {download_item.title}")
                    print(f"   🔄 Post-download merging for: {download_item.title}")
                    self._notify_progress_change(download_item.id)

                    # Небольшая задержка для показа индикатора
                    import threading
                    def clear_merger_indicator():
                        time.sleep(3)
                        if download_item.status.value != 'completed':
                            download_item.speed = ''
                            download_item.eta = ''
                            self._notify_progress_change(download_item.id)

                    threading.Thread(target=clear_merger_indicator, daemon=True).start()

            # Mark as completed
            download_item.status = DownloadStatus.COMPLETED
            download_item.completed_at = time.time()
            download_item.progress = 100.0
            download_item.speed = ''
            download_item.eta = ''

            self.logger.info(f"Download completed: {download_item.title}")
            self.log_download_event("COMPLETED", download_item.url, download_item.title)

            # Show completion notification
            if self.notification_manager:
                self.notification_manager.show_success(
                    "Download Complete",
                    f"'{download_item.title}' has been downloaded successfully"
                )

        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            download_item.status = DownloadStatus.FAILED
            download_item.error_message = str(e)

            self.log_download_event("FAILED", download_item.url, str(e))

            # Handle error with notification system
            if self.error_handler:
                self.error_handler.handle_download_error(e, download_item.url, show_user=True)

        finally:
            # Save to history
            try:
                self.history_manager.add_download(download_item)
            except Exception as e:
                self.logger.error(f"Failed to save to history: {e}")

            # Clean up
            if download_item.id in self.active_downloads:
                del self.active_downloads[download_item.id]

            self._notify_progress_change(download_item.id)
            self._process_queue()  # Start next download
            
    def _prepare_ydl_options(self, download_item: DownloadItem) -> Dict:
        """Prepare yt-dlp options for download"""
        output_path = Path(download_item.output_path)

        # Get format with high-quality fallback
        format_id = download_item.format_info.get('format_id', 'bestvideo+bestaudio/best')

        self.logger.info(f"Preparing download for: {download_item.url}")
        self.logger.info(f"Format info: {download_item.format_info}")
        self.logger.info(f"Using format_id: {format_id}")

        # ИСПРАВЛЕНИЕ ПРОБЛЕМЫ С СЕРЫМ ВИДЕО И МЕРЦАНИЕМ ДЛЯ НИЗКИХ КАЧЕСТВ
        # Для качеств 480p и ниже: используем простые селекторы без слияния потоков
        # Для высоких качеств: применяем сложную логику с кодеками
        if not download_item.format_info.get('audio_only'):
            import re

            # Ищем ограничения по высоте в format_id
            height_match = re.search(r'height<=(\d+)', format_id)

            # Проверяем, содержит ли селектор ограничения для низких качеств
            is_low_quality_selector = (height_match and
                                     int(height_match.group(1)) <= 480)

            if is_low_quality_selector:
                # Для качеств 480p и ниже - применяем специальную логику H.264
                height = int(height_match.group(1))

                # Если это уже правильный селектор с приоритетом H.264, оставляем как есть
                if 'vcodec^=avc1' in format_id:
                    self.logger.info(f"Quality {height}p: Using H.264 priority selector to avoid gray filter")
                    print(f"   📱 {height}p → Селектор с приоритетом H.264 (избегаем серый фильтр)")
                else:
                    # Если это старый селектор, заменяем на правильный
                    format_id = f'best[height<={height}][ext=mp4][vcodec!=none][acodec!=none]/bestvideo[height<={height}][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}]'
                    self.logger.info(f"Quality {height}p: Replaced with H.264 priority selector")
                    print(f"   📱 {height}p → Заменен на селектор с приоритетом H.264")
            elif 'bestvideo' in format_id:
                if height_match:
                    height = int(height_match.group(1))

                    if height <= 1080:
                        # Medium qualities: strict H.264 + FORCED RUSSIAN AUDIO
                        # CRITICALLY IMPORTANT: Force Russian language in selector
                        format_id = f'bestvideo[height<={height}][vcodec^=avc1]+bestaudio[language=ru]/bestvideo[height<={height}]+bestaudio[language=orig]/bestvideo[height<={height}]+bestaudio/best'
                        self.logger.info(f"Quality {height}p: H.264 codec + forced Russian audio")
                        print(f"   {height}p -> H.264 codec + FORCED RUSSIAN AUDIO")
                    else:
                        # High qualities: any codec + FORCED RUSSIAN AUDIO
                        format_id = f'bestvideo[height<={height}]+bestaudio[language=ru]/bestvideo[height<={height}]+bestaudio[language=orig]/bestvideo[height<={height}]+bestaudio/best'
                        self.logger.info(f"Quality {height}p: Any codec + forced Russian audio")
                        print(f"   🖥️ {height}p → Любой кодек + ПРИНУДИТЕЛЬНО РУССКОЕ АУДИО")
                else:
                    # Нет ограничения по качеству - простой селектор
                    format_id = 'bestvideo+bestaudio/best'
                    self.logger.info("Best quality: simple selector, FFmpeg will handle compatibility")
            elif format_id == 'best':
                format_id = 'bestvideo+bestaudio/best'
                self.logger.info("Best quality (replacing 'best'): simple selector")

        ydl_opts = {
            'outtmpl': str(output_path / '%(title)s.%(ext)s'),
            'format': format_id,
            # Disable additional files - MP4 only!
            'writeinfojson': False,
            'writethumbnail': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            # CRITICALLY IMPORTANT SETTINGS FOR GETTING ORIGINAL AUDIO TRACK
            'geo_bypass': False,  # Disable geo-bypass to preserve regional settings
            'prefer_original_language': True,  # Prefer original language
            # FORCED HTTP HEADERS FOR RUSSIAN CONTENT
            'http_headers': {
                'Accept-Language': 'ru-RU,ru;q=0.9',  # FORCED Russian language
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            },
            # Настройки для обхода ограничений YouTube
            'ignoreerrors': False,
            'extractor_retries': 3,
            'fragment_retries': 3,
            # МИНИМАЛЬНЫЕ НАСТРОЙКИ ДЛЯ СТАБИЛЬНОСТИ
            'merge_output_format': 'mp4',  # Принудительно MP4
            # Дополнительные настройки для оригинального контента
            'no_check_certificate': True,
            'prefer_insecure': False,
            'call_home': False,
            # МИНИМАЛЬНЫЕ настройки для стабильности - не переопределяем заголовки
            # Пусть yt-dlp сам управляет HTTP заголовками для лучшей совместимости
        }

        # Add format-specific options ONLY for audio
        if download_item.format_info.get('audio_only'):
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': download_item.format_info.get('audio_format', 'mp3'),
                'preferredquality': download_item.format_info.get('audio_quality', '192'),
            }]
            self.logger.info("Audio-only download configured")
        else:
            # ВИДЕО ЗАГРУЗКА - все видео в MP4 формате для совместимости
            # Избегаем WebM из-за проблем с зависаниями при воспроизведении

            quality = download_item.format_info.get('quality', '')

            # Все видео принудительно в MP4 формате
            ydl_opts['merge_output_format'] = 'mp4'

            # Определяем качество для настройки сортировки и постпроцессинга
            import re
            height_match = re.search(r'(\d+)p', quality) if quality else None
            height = int(height_match.group(1)) if height_match else 1080

            # Дополнительные настройки для обеспечения совместимости
            # Для низких качеств (480p и ниже) - строгий приоритет H.264
            if height <= 480:
                ydl_opts['format_sort'] = ['res', 'fps', 'vcodec:h264', 'acodec:m4a', 'ext:mp4', 'size']
                print(f"   📱 {height}p → Строгий приоритет H.264 кодека для избежания серого фильтра")
            else:
                ydl_opts['format_sort'] = ['res', 'fps', 'vcodec:h264', 'acodec:m4a', 'size']
            ydl_opts['prefer_free_formats'] = False  # Не предпочитаем WebM/VP9

            # Определяем, нужен ли постпроцессинг для высоких качеств

            if height > 1080:
                # Для высоких качеств (2K/4K) добавляем FFmpeg постпроцессинг
                # чтобы исправить проблему с серым фильтром при использовании VP9
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }]

                # Минимальные аргументы для исправления цветов
                ydl_opts['postprocessor_args'] = {
                    'ffmpeg': [
                        '-c:v', 'libx264',      # H.264 кодек
                        '-c:a', 'copy',         # Копируем аудио без перекодирования
                        '-preset', 'ultrafast', # Максимально быстрое кодирование
                        '-pix_fmt', 'yuv420p',  # Правильный формат пикселей
                    ]
                }

                self.logger.info(f"High quality {height}p: Adding minimal FFmpeg processing to fix gray filter")
                print(f"   🔄 {height}p → Минимальный FFmpeg для исправления серого фильтра")

            # Логирование настроек качества
            self.logger.info(f"Quality {height}p: MP4 format (compatible, no freezing)")
            print(f"   📱 {height}p → MP4 (совместимо, без зависаний)")

            self.logger.info(f"Video download configured with format: {format_id}")

        # КРИТИЧЕСКИ ВАЖНО: Добавляем cookies для обхода региональных ограничений
        # Это помогает получить оригинальную аудиодорожку вместо дублированной
        cookie_opts = self.cookie_manager.get_cookie_options(download_item.url)
        if cookie_opts:
            ydl_opts.update(cookie_opts)
            self.logger.info(f"Using cookies from browser: {cookie_opts.get('cookiesfrombrowser', ['unknown'])[0]}")
            print(f"   🍪 Используем cookies из браузера для получения оригинальной озвучки")
        else:
            self.logger.warning("No cookies available - may get dubbed audio instead of original")
            print(f"   ⚠️  Cookies недоступны - возможна дублированная озвучка вместо оригинальной")

        # Финальная диагностика настроек
        self.logger.info(f"Final yt-dlp options: format='{ydl_opts['format']}', cookies={'yes' if cookie_opts else 'no'}")
        print(f"   🔧 Финальные настройки: формат='{ydl_opts['format']}', cookies={'да' if cookie_opts else 'нет'}")

        return ydl_opts
        
    def _progress_hook(self, d: Dict, download_id: str):
        """Handle download progress updates"""
        try:
            download_item = self.get_download_item(download_id)
            if not download_item:
                return

            # Логируем все статусы для отладки
            self.logger.debug(f"Progress hook: status={d.get('status')}, data={d}")

            if d['status'] == 'downloading':
                # Update progress information
                if 'total_bytes' in d:
                    download_item.total_bytes = d['total_bytes']
                    download_item.downloaded_bytes = d.get('downloaded_bytes', 0)
                    download_item.progress = (download_item.downloaded_bytes / download_item.total_bytes) * 100

                # Clean up speed and ETA strings from yt-dlp formatting
                raw_speed = d.get('_speed_str', '')
                raw_eta = d.get('_eta_str', '')

                # Remove brackets and other formatting characters
                download_item.speed = self._clean_display_string(raw_speed)
                download_item.eta = self._clean_display_string(raw_eta)

                self._notify_progress_change(download_id)

            elif d['status'] == 'finished':
                # Download finished, check if merging is needed
                download_item.progress = 100

                # Проверяем, требуется ли слияние форматов
                format_info = getattr(download_item, 'format_info', {})
                needs_merging = False

                # Проверяем по селектору формата
                if hasattr(self, '_current_format_selector'):
                    needs_merging = '+' in self._current_format_selector

                # Проверяем по качеству (высокие качества обычно требуют слияния)
                quality = format_info.get('quality', '')
                if quality in ['720p', '1080p', '1440p', '2160p', '4K']:
                    needs_merging = True

                # Проверяем по имени файла
                filename = d.get('filename', '')
                if filename and any(ext in filename for ext in ['.f', '.temp', '.part']):
                    needs_merging = True

                if needs_merging:
                    download_item.speed = 'Merging formats...'
                    download_item.eta = 'Processing'
                    self.logger.info(f"Format merging detected for {download_item.title}")
                    print(f"   🔄 Merging formats for: {download_item.title}")
                else:
                    download_item.speed = 'Finishing...'
                    download_item.eta = 'Almost done'

                self._notify_progress_change(download_id)

            elif d['status'] == 'processing':
                # Postprocessing (merging formats)
                download_item.speed = '🔄 Merging formats...'
                download_item.eta = 'Processing'
                download_item.progress = 100
                self.logger.info(f"Postprocessing started for {download_item.title}")
                self._notify_progress_change(download_id)

        except Exception as e:
            self.logger.error(f"Progress hook error: {e}")

    def _clean_display_string(self, text: str) -> str:
        """Clean display strings from yt-dlp formatting"""
        if not text:
            return ""

        import re

        # Remove ANSI escape sequences
        text = re.sub(r'\x1b\[[0-9;]*m', '', text)

        # Remove color codes in brackets like [32m, [31;1m, [0m
        text = re.sub(r'\[\d+(?:;\d+)*m', '', text)

        # Remove percentage indicators in brackets like [90%]
        text = re.sub(r'\[\d+%\]', '', text)

        # Remove [download] prefix
        text = re.sub(r'\[download\]\s*', '', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text.strip()

    def _postprocessor_hook(self, d: Dict, download_id: str):
        """Handle postprocessor progress updates"""
        try:
            download_item = self.get_download_item(download_id)
            if not download_item:
                return

            # Логируем все события постобработки
            self.logger.info(f"Postprocessor hook: status={d.get('status')}, postprocessor={d.get('postprocessor')}, data={d}")
            print(f"🔄 Postprocessor: {d.get('status')} - {d.get('postprocessor', 'Unknown')}")

            if d['status'] == 'started':
                # Postprocessing started
                download_item.speed = '🔄 Merging formats...'
                download_item.eta = 'Processing'
                self.logger.info(f"Postprocessing started for {download_item.title}")
                print(f"   🔄 Started merging for: {download_item.title}")
                self._notify_progress_change(download_id)

            elif d['status'] == 'processing':
                # Postprocessing in progress
                download_item.speed = 'Merging formats...'
                download_item.eta = 'Processing'
                self._notify_progress_change(download_id)

            elif d['status'] == 'finished':
                # Postprocessing finished
                download_item.speed = ''
                download_item.eta = ''
                self.logger.info(f"Postprocessing finished for {download_item.title}")
                print(f"   Finished merging for: {download_item.title}")
                self._notify_progress_change(download_id)

        except Exception as e:
            self.logger.error(f"Postprocessor hook error: {e}")
            print(f"Postprocessor hook error: {e}")

    def _cancel_download(self, download_id: str):
        """Cancel an active download"""
        if download_id in self.active_downloads:
            # Note: yt-dlp doesn't support graceful cancellation
            # The thread will continue but we mark it as cancelled
            item = self.get_download_item(download_id)
            if item:
                item.status = DownloadStatus.CANCELLED
                self._notify_progress_change(download_id)
                
    def _notify_progress_change(self, download_id: str):
        """Notify progress callbacks"""
        if download_id in self.progress_callbacks:
            for callback in self.progress_callbacks[download_id]:
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"Progress callback error: {e}")
                    
    def _notify_queue_change(self):
        """Notify queue change callbacks"""
        for callback in self.download_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Queue callback error: {e}")
                
    def _get_queue_file_path(self) -> Path:
        """Get the path for the queue persistence file"""
        if hasattr(self.settings_manager, 'settings_dir'):
            return self.settings_manager.settings_dir / 'download_queue.json'
        else:
            # Fallback to home directory
            return Path.home() / '.yt-dlp-gui' / 'download_queue.json'

    def save_queue(self):
        """Save the current queue to file"""
        try:
            # Ensure directory exists
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert queue to serializable format
            queue_data = []
            with self.queue_lock:
                for item in self.download_queue:
                    # Convert dataclass to dict
                    item_dict = asdict(item)
                    # Convert enum to string
                    item_dict['status'] = item.status.value
                    queue_data.append(item_dict)

            # Save to file
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Queue saved with {len(queue_data)} items")

        except Exception as e:
            self.logger.error(f"Failed to save queue: {e}")

    def load_queue(self):
        """Load the queue from file"""
        try:
            if not self.queue_file.exists():
                self.logger.info("No saved queue found")
                return

            with open(self.queue_file, 'r', encoding='utf-8') as f:
                queue_data = json.load(f)

            # Convert back to DownloadItem objects
            loaded_items = []
            for item_dict in queue_data:
                # Convert status string back to enum
                status_str = item_dict.get('status', 'pending')
                try:
                    status = DownloadStatus(status_str)
                except ValueError:
                    status = DownloadStatus.PENDING

                item_dict['status'] = status

                # Create DownloadItem
                download_item = DownloadItem(**item_dict)

                # Skip cancelled downloads - they should not be restored
                if download_item.status == DownloadStatus.CANCELLED:
                    self.logger.info(f"Skipping cancelled download: {download_item.title}")
                    continue

                # Reset active downloads to pending
                if download_item.status == DownloadStatus.DOWNLOADING:
                    download_item.status = DownloadStatus.PENDING
                    download_item.progress = 0.0
                    download_item.speed = ""
                    download_item.eta = ""

                loaded_items.append(download_item)

            with self.queue_lock:
                self.download_queue = loaded_items

            self.logger.info(f"Loaded queue with {len(loaded_items)} items")

            # Clean up old failed downloads (older than 24 hours)
            self._cleanup_old_failed_downloads()

            # Start processing queue
            self._process_queue()

        except Exception as e:
            self.logger.error(f"Failed to load queue: {e}")

    def clear_queue_file(self):
        """Clear the saved queue file"""
        try:
            if self.queue_file.exists():
                self.queue_file.unlink()
                self.logger.info("Queue file cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear queue file: {e}")

    def _cleanup_old_failed_downloads(self):
        """Remove old failed downloads from the queue"""
        try:
            import time
            current_time = time.time()
            cleanup_threshold = 24 * 60 * 60  # 24 hours in seconds

            with self.queue_lock:
                original_count = len(self.download_queue)

                # Keep only downloads that are not old failed ones
                self.download_queue = [
                    item for item in self.download_queue
                    if not (
                        item.status == DownloadStatus.FAILED and
                        current_time - item.created_at > cleanup_threshold
                    )
                ]

                cleaned_count = original_count - len(self.download_queue)

                if cleaned_count > 0:
                    self.logger.info(f"Cleaned up {cleaned_count} old failed downloads")
                    # Save the cleaned queue
                    self.save_queue()

        except Exception as e:
            self.logger.error(f"Failed to cleanup old failed downloads: {e}")

    def reorder_queue(self, item_id: str, new_position: int) -> bool:
        """Reorder an item in the queue"""
        try:
            with self.queue_lock:
                # Find the item
                item_index = None
                for i, item in enumerate(self.download_queue):
                    if item.id == item_id:
                        item_index = i
                        break

                if item_index is None:
                    return False

                # Remove item from current position
                item = self.download_queue.pop(item_index)

                # Insert at new position
                new_position = max(0, min(new_position, len(self.download_queue)))
                self.download_queue.insert(new_position, item)

                # Save queue
                self.save_queue()
                self._notify_queue_change()

                return True

        except Exception as e:
            self.logger.error(f"Failed to reorder queue: {e}")
            return False

    def get_queue_statistics(self) -> Dict:
        """Get statistics about the current queue"""
        with self.queue_lock:
            stats = {
                'total': len(self.download_queue),
                'pending': 0,
                'downloading': 0,
                'completed': 0,
                'failed': 0,
                'paused': 0,
                'cancelled': 0,
            }

            for item in self.download_queue:
                stats[item.status.value] += 1

            return stats

    def get_download_history(self, status_filter: Optional[str] = None, limit: Optional[int] = None):
        """Get download history from history manager"""
        try:
            return self.history_manager.get_download_history(status_filter, limit)
        except Exception as e:
            self.logger.error(f"Failed to get download history: {e}")
            return []

    def clear_failed_downloads(self):
        """Remove all failed downloads from the queue"""
        try:
            with self.queue_lock:
                original_count = len(self.download_queue)

                # Keep only downloads that are not failed
                self.download_queue = [
                    item for item in self.download_queue
                    if item.status != DownloadStatus.FAILED
                ]

                cleared_count = original_count - len(self.download_queue)

                if cleared_count > 0:
                    self.logger.info(f"Cleared {cleared_count} failed downloads")
                    # Save the cleaned queue
                    self.save_queue()
                    # Notify queue change
                    self._notify_queue_change()

                return cleared_count

        except Exception as e:
            self.logger.error(f"Failed to clear failed downloads: {e}")
            return 0

    def clear_completed_downloads(self):
        """Remove all completed and failed downloads from the queue"""
        try:
            with self.queue_lock:
                original_count = len(self.download_queue)

                # Keep only downloads that are not completed or failed
                self.download_queue = [
                    item for item in self.download_queue
                    if item.status not in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]
                ]

                cleared_count = original_count - len(self.download_queue)

                if cleared_count > 0:
                    self.logger.info(f"Cleared {cleared_count} completed/failed downloads")
                    # Save the cleaned queue
                    self.save_queue()
                    # Notify queue change
                    self._notify_queue_change()

                return cleared_count

        except Exception as e:
            self.logger.error(f"Failed to clear completed downloads: {e}")
            return 0

    def clear_completed_downloads_simple(self):
        """Remove all completed and failed downloads from the queue (simple version without callbacks)"""
        try:
            with self.queue_lock:
                original_count = len(self.download_queue)

                # Keep only downloads that are not completed or failed
                self.download_queue = [
                    item for item in self.download_queue
                    if item.status not in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]
                ]

                cleared_count = original_count - len(self.download_queue)

                if cleared_count > 0:
                    self.logger.info(f"Cleared {cleared_count} completed/failed downloads (simple)")

                return cleared_count

        except Exception as e:
            self.logger.error(f"Failed to clear completed downloads (simple): {e}")
            return 0

    def search_history(self, query: str, limit: Optional[int] = None):
        """Search download history"""
        try:
            return self.history_manager.search_downloads(query, limit)
        except Exception as e:
            self.logger.error(f"Failed to search history: {e}")
            return []

    def clear_history(self, status_filter: Optional[str] = None) -> bool:
        """Clear download history"""
        try:
            return self.history_manager.clear_history(status_filter)
        except Exception as e:
            self.logger.error(f"Failed to clear history: {e}")
            return False

    def get_history_statistics(self) -> Dict:
        """Get download history statistics"""
        try:
            return self.history_manager.get_statistics()
        except Exception as e:
            self.logger.error(f"Failed to get history statistics: {e}")
            return {}

    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """Format bytes to human readable string"""
        if bytes_value == 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0

        return f"{bytes_value:.1f} PB"

    def cancel_all_downloads(self):
        """Cancel all active downloads and clear the queue permanently"""
        self.logger.info("Cancelling all downloads permanently...")

        try:
            # Stop the download thread
            self.stop_downloads()

            # Cancel any active yt-dlp processes and clear queue
            with self.queue_lock:
                for item in self.download_queue:
                    if item.status == DownloadStatus.DOWNLOADING:
                        self.logger.info(f"Cancelled download: {item.url}")

                # Clear the entire queue permanently
                self.download_queue.clear()
                self.logger.info("Download queue cleared permanently")

            # Delete queue file to prevent restoration
            try:
                if self.queue_file.exists():
                    self.queue_file.unlink()
                    self.logger.info("Queue file deleted - downloads will not resume")
            except Exception as e:
                self.logger.error(f"Failed to delete queue file: {e}")
                # Fallback: save empty queue
                self.save_queue()
                self.logger.info("Fallback: Empty queue saved")

            # Notify callbacks about queue changes
            self._notify_queue_change()

        except Exception as e:
            self.logger.error(f"Error cancelling downloads: {e}")

    def stop_downloads(self):
        """Stop the download thread"""
        try:
            self.running = False
            if hasattr(self, 'download_thread') and self.download_thread and self.download_thread.is_alive():
                self.download_thread.join(timeout=2.0)  # Wait up to 2 seconds
                if self.download_thread.is_alive():
                    self.logger.warning("Download thread did not stop gracefully")
                else:
                    self.logger.info("Download thread stopped")
        except Exception as e:
            self.logger.error(f"Error stopping download thread: {e}")

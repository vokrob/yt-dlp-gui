# -*- coding: utf-8 -*-
"""
Download Manager
Author: vokrob (Данил Борков)
Date: 18.07.2025
"""

import threading
import queue
import logging
import time
import json
import requests
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid

from .cookie_manager import CookieManager, cookie_opts_to_cli
from . import ytdlp_wrapper

ERROR_TRANSLATIONS = [
    (r'unable to download video data.*HTTP Error 403', 'YouTube заблокировал скачивание. Куки в браузере устарели — экспортируйте новые через расширение Get cookies.txt в файл cookies.txt и положите рядом с программой'),
    (r'HTTP Error 40[13]', 'Доступ запрещён (HTTP 40x). Попробуйте добавить cookies.txt рядом с программой'),
    (r'HTTP Error 404', 'Видео не найдено (HTTP 404). Возможно, оно удалено или ссылка неверна'),
    (r'HTTP Error 429', 'Слишком много запросов. Подождите несколько минут и повторите'),
    (r'HTTP Error 5\d{2}', 'Ошибка сервера (HTTP 5xx). Повторите попытку позже'),
    (r'Sign in to confirm', 'YouTube запросил подтверждение. Экспортируйте cookies браузера в cookies.txt и положите рядом с программой'),
    (r'confirm your age', 'Возрастное ограничение. Добавьте cookies.txt из аккаунта с подтверждённым возрастом'),
    (r'Video unavailable', 'Видео недоступно. Возможно, оно удалено или доступно только по ссылке'),
    (r'This video is private', 'Это приватное видео. Добавьте cookies.txt из аккаунта, у которого есть доступ'),
    (r'ffprobe.*not found', 'FFmpeg не найден — проверьте подключение к интернету и перезапустите программу'),
    (r'ffmpeg.*not found', 'FFmpeg не найден — проверьте подключение к интернету и перезапустите программу'),
    (r'No video formats found', 'Не удалось получить форматы видео. Возможно, видео недоступно в вашем регионе'),
    (r'Unable to extract', 'Не удалось обработать страницу. Возможно, сайт изменился или нужны куки'),
    (r'requested format not available', 'Запрошенное качество недоступно. Попробуйте другое'),
    (r'ConnectionError.*reset', 'Соединение разорвано. Проверьте интернет и VPN'),
    (r'Timeout', 'Таймаут соединения. Проверьте интернет или попробуйте позже'),
    (r'Certificate verify failed', 'Ошибка SSL-сертификата. Проверьте дату и время на компьютере'),
]

def translate_error(error: Exception) -> str:
    """Convert common yt-dlp errors to human-readable Russian messages"""
    error_str = str(error)
    for pattern, message in ERROR_TRANSLATIONS:
        import re
        if re.search(pattern, error_str, re.IGNORECASE):
            return message
    # Fallback: truncate raw error
    if len(error_str) > 200:
        return error_str[:200] + '...'
    return error_str

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
            base_args = [
                '--add-header', 'Accept-Language: ru-RU,ru;q=0.9',
            ]

            info = None
            for browser in ['chrome', 'firefox', 'edge', None]:
                extra = list(base_args)
                cookie_opts = self.cookie_manager.get_cookie_options(download_item.url, browser=browser)
                if cookie_opts:
                    extra.extend(cookie_opts_to_cli(cookie_opts))
                try:
                    info = ytdlp_wrapper.extract_info(download_item.url, extra_args=extra)
                    if info:
                        break
                except Exception:
                    continue

            if info:
                html_title = self._extract_title_from_html(download_item.url)
                if html_title:
                    title = html_title
                    self.logger.info(f"HTML title extracted: '{title}'")
                else:
                    title = info.get('title', 'Unknown Title')
                    self.logger.warning(f"HTML extraction failed, using yt-dlp title: '{title}'")

                download_item.title = title
                download_item.file_size = self._format_bytes(info.get('filesize') or 0)
                    
        except Exception as e:
            self.logger.warning(f"Failed to get video info: {e}")
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
            download_item.error_message = translate_error(e)
            self._notify_progress_change(download_item.id)
            
    def _download_worker(self, download_item: DownloadItem):
        """Worker thread for downloading"""
        cookie_browsers = ['chrome', 'firefox', 'edge', None]
        last_error = None
        success = False

        for browser in cookie_browsers:
            try:
                extra_args, format_spec, output_path = self._prepare_ydl_options(download_item, browser=browser)

                def progress_callback(p):
                    self._on_subprocess_progress(p, download_item.id)

                exit_code = ytdlp_wrapper.download(
                    download_item.url, output_path, format_spec,
                    extra_args=extra_args,
                    progress_callback=progress_callback
                )

                if exit_code == 0:
                    download_item.status = DownloadStatus.COMPLETED
                    download_item.completed_at = time.time()
                    download_item.progress = 100.0
                    download_item.speed = ''
                    download_item.eta = ''

                    self.logger.info(f"Download completed: {download_item.title}")
                    self.log_download_event("COMPLETED", download_item.url, download_item.title)

                    if self.notification_manager:
                        self.notification_manager.show_success(
                            "Download Complete",
                            f"'{download_item.title}' has been downloaded successfully"
                        )

                    success = True
                    break
                else:
                    raise Exception(f"yt-dlp exited with code {exit_code}")

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                self.logger.warning(f"Download attempt with {browser or 'no cookies'} failed: {e}")

                if any(kw in error_msg for kw in ['sign in', 'confirm you', 'bot', 'cookie', '403', 'forbidden']):
                    if browser is not None:
                        self.logger.info(f"Auth/access issue with {browser}, trying next browser...")
                        continue

                break

        if not success:
            self.logger.error(f"Download failed: {last_error}")
            download_item.status = DownloadStatus.FAILED
            download_item.error_message = translate_error(last_error)

            self.log_download_event("FAILED", download_item.url, str(last_error))

            if self.error_handler:
                self.error_handler.handle_download_error(last_error, download_item.url, show_user=True)

        try:
            self.history_manager.add_download(download_item)
        except Exception as e:
            self.logger.error(f"Failed to save to history: {e}")

        if download_item.id in self.active_downloads:
            del self.active_downloads[download_item.id]

        self._notify_progress_change(download_item.id)
        self._process_queue()

    def _on_subprocess_progress(self, progress: dict, download_id: str):
        """Handle progress callback from subprocess download."""
        try:
            download_item = self.get_download_item(download_id)
            if not download_item:
                return

            percent = progress.get('percent', 0)
            download_item.progress = percent
            download_item.speed = progress.get('speed', '')
            download_item.eta = progress.get('eta', '')

            if 'error' in progress:
                download_item.status = DownloadStatus.FAILED
                download_item.error_message = progress['error']

            self._notify_progress_change(download_id)
        except Exception as e:
            self.logger.error(f"Subprocess progress error: {e}")

    def _prepare_ydl_options(self, download_item: DownloadItem, browser: str = None):
        """Prepare yt-dlp CLI arguments. Returns (extra_args, format_spec, output_template)."""
        output_path = Path(download_item.output_path)
        output_template = str(output_path / '%(title)s.%(ext)s')
        format_id = download_item.format_info.get('format_id', 'bestvideo+bestaudio/best')

        self.logger.info(f"Preparing download: url={download_item.url}, format={format_id}")

        extra_args = [
            '--no-playlist',
            '--merge-output-format', 'mp4',
            '--no-check-certificate',
            '--add-header', 'Accept-Language: ru-RU,ru;q=0.9',
            '--add-header', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '--retries', '3',
            '--fragment-retries', '3',
            '--extractor-retries', '3',
        ]

        if not download_item.format_info.get('audio_only'):
            height_match = re.search(r'height<=(\d+)', format_id)
            quality = download_item.format_info.get('quality', '')

            sort_args = ['res', 'fps', 'vcodec:h264', 'acodec:m4a', 'ext:mp4', 'size']
            extra_args.append('--format-sort')
            extra_args.append(','.join(sort_args))

            if height_match:
                height = int(height_match.group(1))
                if height > 1080:
                    extra_args.append('--remux-video')
                    extra_args.append('mp4')
                    extra_args.append('--postprocessor-args')
                    extra_args.append('ffmpeg:-c:v libx264 -c:a copy -preset ultrafast -pix_fmt yuv420p')
            else:
                extra_args.append('--remux-video')
                extra_args.append('mp4')
        else:
            audio_fmt = download_item.format_info.get('audio_format', 'mp3')
            audio_quality = download_item.format_info.get('audio_quality', '192')
            extra_args.extend(['--extract-audio', '--audio-format', audio_fmt, '--audio-quality', audio_quality])
            format_id = 'bestaudio/best'

        cookie_opts = self.cookie_manager.get_cookie_options(download_item.url, browser=browser)
        if cookie_opts:
            extra_args.extend(cookie_opts_to_cli(cookie_opts))

        return extra_args, format_id, output_template
        
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

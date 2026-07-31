# -*- coding: utf-8 -*-
"""
Logger
Author: vokrob
Date: 18.07.2025
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

class LogManager:
    """Manages application logging"""
    
    def __init__(self, app_name: str = "yt-dlp-gui", log_dir: Optional[Path] = None):
        # Determine log directory
        if log_dir:
            self.log_dir = log_dir
        else:
            if os.name == 'nt':  # Windows
                base_dir = Path(os.environ.get('APPDATA', Path.home()))
            elif os.name == 'posix':
                if 'darwin' in os.uname().sysname.lower():  # macOS
                    base_dir = Path.home() / 'Library' / 'Application Support'
                else:  # Linux
                    base_dir = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
            else:
                base_dir = Path.home()
                
            self.log_dir = base_dir / app_name / 'logs'
            
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log files
        self.app_log_file = self.log_dir / 'app.log'
        self.error_log_file = self.log_dir / 'error.log'
        self.download_log_file = self.log_dir / 'downloads.log'
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Set up the logging configuration"""
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Main application log file (rotating)
        app_handler = logging.handlers.RotatingFileHandler(
            self.app_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.DEBUG)
        app_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        app_handler.setFormatter(app_formatter)
        root_logger.addHandler(app_handler)
        
        # Error log file (errors and critical only)
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n'
            'Exception: %(exc_info)s\n' + '-'*80,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)
        
        # Download-specific logger
        download_logger = logging.getLogger('downloads')
        download_handler = logging.handlers.RotatingFileHandler(
            self.download_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        download_handler.setLevel(logging.INFO)
        download_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        download_handler.setFormatter(download_formatter)
        download_logger.addHandler(download_handler)
        download_logger.propagate = False  # Don't propagate to root logger
        
        # Suppress noisy third-party loggers
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('yt_dlp').setLevel(logging.WARNING)
        
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name"""
        return logging.getLogger(name)
        
    def get_download_logger(self) -> logging.Logger:
        """Get the download-specific logger"""
        return logging.getLogger('downloads')

# Global log manager instance
_log_manager = None

def get_log_manager() -> LogManager:
    """Get the global log manager"""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager()
    return _log_manager

def init_logging(app_name: str = "yt-dlp-gui", log_dir: Optional[Path] = None) -> LogManager:
    """Initialize the logging system"""
    global _log_manager
    _log_manager = LogManager(app_name, log_dir)
    return _log_manager

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return get_log_manager().get_logger(name)

def log_download_event(event_type: str, url: str, details: str = ""):
    """Log a download-specific event"""
    download_logger = get_log_manager().get_download_logger()
    message = f"[{event_type}] {url}"
    if details:
        message += f" - {details}"
    download_logger.info(message)

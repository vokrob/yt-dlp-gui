# -*- coding: utf-8 -*-
"""
History Manager
Author: vokrob
Date: 18.07.2025
"""

import sqlite3
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from ytdlp_gui.core.download_manager import DownloadItem

class HistoryManager:
    """Manages download history using SQLite database"""
    
    def __init__(self, settings_manager):
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager
        
        # Database file path
        self.db_path = self._get_db_path()
        
        # Initialize database
        self.init_database()
        
    def _get_db_path(self) -> Path:
        """Get the database file path"""
        if hasattr(self.settings_manager, 'settings_dir'):
            return self.settings_manager.settings_dir / 'download_history.db'
        else:
            # Fallback to home directory
            return Path.home() / '.yt-dlp-gui' / 'download_history.db'
            
    def init_database(self):
        """Initialize the database and create tables"""
        try:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create downloads table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS downloads (
                        id TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        title TEXT,
                        status TEXT NOT NULL,
                        format_info TEXT,
                        output_path TEXT,
                        file_size INTEGER,
                        downloaded_bytes INTEGER,
                        progress REAL,
                        error_message TEXT,
                        created_at REAL NOT NULL,
                        completed_at REAL,
                        updated_at REAL NOT NULL
                    )
                ''')
                
                # Create index for faster queries
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_downloads_status 
                    ON downloads(status)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_downloads_created_at 
                    ON downloads(created_at)
                ''')
                
                conn.commit()
                
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            
    def add_download(self, download_item: DownloadItem):
        """Add a download to history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Serialize format_info to JSON
                format_info_json = json.dumps(download_item.format_info) if download_item.format_info else None
                
                cursor.execute('''
                    INSERT OR REPLACE INTO downloads (
                        id, url, title, status, format_info, output_path,
                        file_size, downloaded_bytes, progress, error_message,
                        created_at, completed_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    download_item.id,
                    download_item.url,
                    download_item.title,
                    download_item.status.value,
                    format_info_json,
                    download_item.output_path,
                    download_item.total_bytes,
                    download_item.downloaded_bytes,
                    download_item.progress,
                    download_item.error_message,
                    download_item.created_at,
                    download_item.completed_at,
                    datetime.now().timestamp()
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to add download to history: {e}")
            
    def get_download_history(self, status_filter: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Get download history with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query
                query = "SELECT * FROM downloads"
                params = []
                
                if status_filter:
                    query += " WHERE status = ?"
                    params.append(status_filter)
                    
                query += " ORDER BY created_at DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                    
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                columns = [description[0] for description in cursor.description]
                history = []
                
                for row in rows:
                    item_dict = dict(zip(columns, row))
                    
                    # Parse format_info JSON
                    if item_dict['format_info']:
                        try:
                            item_dict['format_info'] = json.loads(item_dict['format_info'])
                        except json.JSONDecodeError:
                            item_dict['format_info'] = {}
                    else:
                        item_dict['format_info'] = {}
                        
                    history.append(item_dict)
                    
                return history
                
        except Exception as e:
            self.logger.error(f"Failed to get download history: {e}")
            return []

    def clear_history(self, status_filter: Optional[str] = None) -> bool:
        """Clear download history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if status_filter:
                    cursor.execute("DELETE FROM downloads WHERE status = ?", (status_filter,))
                else:
                    cursor.execute("DELETE FROM downloads")
                    
                conn.commit()
                
                self.logger.info(f"Cleared {cursor.rowcount} items from history")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to clear history: {e}")
            return False


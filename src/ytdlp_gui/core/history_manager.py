# -*- coding: utf-8 -*-
"""
History Manager
Author: vokrob (Данил Борков)
Date: 18.07.2025
"""

import sqlite3
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from ytdlp_gui.core.download_manager import DownloadItem, DownloadStatus

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
            
    def update_download(self, download_item: DownloadItem):
        """Update an existing download in history"""
        self.add_download(download_item)  # INSERT OR REPLACE handles updates
        
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
            
    def get_download_by_id(self, download_id: str) -> Optional[Dict]:
        """Get a specific download by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM downloads WHERE id = ?", (download_id,))
                row = cursor.fetchone()
                
                if row:
                    columns = [description[0] for description in cursor.description]
                    item_dict = dict(zip(columns, row))
                    
                    # Parse format_info JSON
                    if item_dict['format_info']:
                        try:
                            item_dict['format_info'] = json.loads(item_dict['format_info'])
                        except json.JSONDecodeError:
                            item_dict['format_info'] = {}
                    else:
                        item_dict['format_info'] = {}
                        
                    return item_dict
                    
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get download by ID: {e}")
            return None
            
    def remove_download(self, download_id: str) -> bool:
        """Remove a download from history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM downloads WHERE id = ?", (download_id,))
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Failed to remove download from history: {e}")
            return False
            
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
            
    def get_statistics(self) -> Dict:
        """Get download statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get counts by status
                cursor.execute('''
                    SELECT status, COUNT(*) as count 
                    FROM downloads 
                    GROUP BY status
                ''')
                status_counts = dict(cursor.fetchall())
                
                # Get total downloads
                cursor.execute("SELECT COUNT(*) FROM downloads")
                total_downloads = cursor.fetchone()[0]
                
                # Get total size
                cursor.execute("SELECT SUM(file_size) FROM downloads WHERE file_size > 0")
                total_size = cursor.fetchone()[0] or 0
                
                # Get recent downloads (last 7 days)
                week_ago = datetime.now().timestamp() - (7 * 24 * 60 * 60)
                cursor.execute("SELECT COUNT(*) FROM downloads WHERE created_at > ?", (week_ago,))
                recent_downloads = cursor.fetchone()[0]
                
                return {
                    'total_downloads': total_downloads,
                    'status_counts': status_counts,
                    'total_size': total_size,
                    'recent_downloads': recent_downloads,
                    'completed': status_counts.get('completed', 0),
                    'failed': status_counts.get('failed', 0),
                    'cancelled': status_counts.get('cancelled', 0),
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {
                'total_downloads': 0,
                'status_counts': {},
                'total_size': 0,
                'recent_downloads': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0,
            }
            
    def search_downloads(self, query: str, limit: Optional[int] = None) -> List[Dict]:
        """Search downloads by title or URL"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                search_query = f"%{query}%"
                sql = '''
                    SELECT * FROM downloads 
                    WHERE title LIKE ? OR url LIKE ?
                    ORDER BY created_at DESC
                '''
                
                params = [search_query, search_query]
                
                if limit:
                    sql += " LIMIT ?"
                    params.append(limit)
                    
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                columns = [description[0] for description in cursor.description]
                results = []
                
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
                        
                    results.append(item_dict)
                    
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to search downloads: {e}")
            return []
            
    def export_history(self, file_path: str, format: str = 'json') -> bool:
        """Export download history to file"""
        try:
            history = self.get_download_history()
            
            if format.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=2, ensure_ascii=False)
            elif format.lower() == 'csv':
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    if history:
                        writer = csv.DictWriter(f, fieldnames=history[0].keys())
                        writer.writeheader()
                        writer.writerows(history)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
            self.logger.info(f"Exported {len(history)} items to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export history: {e}")
            return False
            
    def cleanup_old_entries(self, days: int = 30) -> int:
        """Clean up old history entries"""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "DELETE FROM downloads WHERE created_at < ? AND status IN ('completed', 'failed', 'cancelled')",
                    (cutoff_time,)
                )
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old history entries")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old entries: {e}")
            return 0

"""
Cache Management Module
Handles SQLite-based caching with TTL support for web search operations.
"""

import hashlib
import logging
import sqlite3
# WARNING: Pickle security - Only use with trusted data sources
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """Advanced caching system with SQLite backend and TTL support."""
    
    def __init__(self, cache_file: str = "data/legal_search_cache.db", ttl_hours: int = 24):
        self.cache_file = cache_file
        self.ttl = timedelta(hours=ttl_hours)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for caching."""
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                timestamp DATETIME,
                ttl_hours INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS url_status (
                url TEXT PRIMARY KEY,
                status TEXT,
                status_code INTEGER,
                last_checked DATETIME,
                content_hash TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _generate_key(self, *args) -> str:
        """Generate cache key from arguments."""
        key_string = "|".join(str(arg) for arg in args)
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()
    
    def get(self, *args) -> Optional[Any]:
        """Get cached value."""
        key = self._generate_key(*args)
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT value, timestamp, ttl_hours FROM search_cache WHERE key = ?',
            (key,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            value_str, timestamp_str, ttl_hours = result
            timestamp = datetime.fromisoformat(timestamp_str)
            ttl = timedelta(hours=ttl_hours)
            
            if datetime.now() - timestamp < ttl:
                try:
                    return pickle.loads(value_str.encode('latin1'))
                except Exception:
                    return None
            else:
                # Expired, remove it
                self.delete(*args)
        
        return None
    
    def set(self, *args, value: Any, ttl_hours: Optional[int] = None):
        """Set cached value."""
        key = self._generate_key(*args[:-1])  # Exclude value from key
        ttl_hours = ttl_hours or int(self.ttl.total_seconds() / 3600)
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        try:
            value_str = pickle.dumps(value).decode('latin1')
            cursor.execute(
                'INSERT OR REPLACE INTO search_cache (key, value, timestamp, ttl_hours) VALUES (?, ?, ?, ?)',
                (key, value_str, datetime.now().isoformat(), ttl_hours)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to cache value: {e}")
        finally:
            conn.close()
    
    def delete(self, *args):
        """Delete cached value."""
        key = self._generate_key(*args)
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM search_cache WHERE key = ?', (key,))
        conn.commit()
        conn.close()
    
    def cleanup_expired(self):
        """Remove expired cache entries."""
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM search_cache 
            WHERE datetime(timestamp, '+' || ttl_hours || ' hours') < datetime('now')
        ''')
        
        conn.commit()
        conn.close()
    
    def get_url_status(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached URL accessibility status."""
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT status, status_code, last_checked, content_hash FROM url_status WHERE url = ?',
            (url,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            status, status_code, last_checked_str, content_hash = result
            last_checked = datetime.fromisoformat(last_checked_str)
            
            # Return cached status if checked within last hour
            if datetime.now() - last_checked < timedelta(hours=1):
                return {
                    'status': status,
                    'status_code': status_code,
                    'last_checked': last_checked,
                    'content_hash': content_hash
                }
        
        return None
    
    def set_url_status(self, url: str, status: str, status_code: Optional[int] = None, 
                      content_hash: Optional[str] = None):
        """Cache URL accessibility status."""
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT OR REPLACE INTO url_status (url, status, status_code, last_checked, content_hash) VALUES (?, ?, ?, ?, ?)',
            (url, status, status_code, datetime.now().isoformat(), content_hash)
        )
        
        conn.commit()
        conn.close() 
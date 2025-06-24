import json
import redis
import sqlite3
import gzip
import pickle
import time
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedCacheManager:
    """
    Unified cache manager using Redis as primary cache with SQLite persistence.
    
    Features:
    - Redis for fast in-memory caching
    - SQLite for persistent storage
    - Automatic compression for large data
    - TTL management
    - Cache warming from SQLite
    - Memory usage monitoring
    """
    
    def __init__(self, config_file: str = "cache_config.json"):
        self.config = self._load_config(config_file)
        self.redis_client = None
        self.db_path = self.config['database_cache']['file']
        self._init_redis()
        self._init_database()
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load cache configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return {
                "redis": {
                    "host": "localhost",
                    "port": 6379,
                    "databases": {
                        "rq_queue": 0,
                        "citation_cache": 1,
                        "url_cache": 2,
                        "session_data": 3
                    }
                },
                "citation_cache": {
                    "ttl": 2592000,
                    "max_size": "100MB",
                    "compression": True
                },
                "url_cache": {
                    "ttl": 604800,
                    "max_size": "500MB",
                    "compression": True
                },
                "database_cache": {
                    "file": "data/citations.db",
                    "indexes": True,
                    "vacuum_interval": 86400
                }
            }
    
    def _init_redis(self):
        """Initialize Redis connection."""
        try:
            redis_config = self.config['redis']
            self.redis_client = redis.Redis(
                host=redis_config['host'],
                port=redis_config['port'],
                decode_responses=False,  # Keep as bytes for compression
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def _init_database(self):
        """Initialize SQLite database with proper schema."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if citations table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='citations'")
                table_exists = cursor.fetchone() is not None
                
                if not table_exists:
                    # Create citations table with the existing schema
                    cursor.execute('''
                        CREATE TABLE citations (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            citation_text TEXT UNIQUE NOT NULL,
                            case_name TEXT,
                            year INTEGER,
                            parallel_citations TEXT,
                            verification_result TEXT,
                            found BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                else:
                    # Table exists, check if we need to add new columns
                    cursor.execute("PRAGMA table_info(citations)")
                    existing_columns = [col[1] for col in cursor.fetchall()]
                    
                    # Add missing columns if they don't exist
                    try:
                        if 'parallel_citations' not in existing_columns:
                            cursor.execute('ALTER TABLE citations ADD COLUMN parallel_citations TEXT')
                    except:
                        pass  # Column might already exist
                        
                    try:
                        if 'verification_result' not in existing_columns:
                            cursor.execute('ALTER TABLE citations ADD COLUMN verification_result TEXT')
                    except:
                        pass  # Column might already exist
                        
                    try:
                        if 'found' not in existing_columns:
                            cursor.execute('ALTER TABLE citations ADD COLUMN found BOOLEAN DEFAULT FALSE')
                    except:
                        pass  # Column might already exist
                        
                    try:
                        if 'updated_at' not in existing_columns:
                            cursor.execute('ALTER TABLE citations ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                    except:
                        pass  # Column might already exist
                
                # Create cache_stats table if it doesn't exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cache_stats'")
                stats_table_exists = cursor.fetchone() is not None
                
                if not stats_table_exists:
                    cursor.execute('''
                        CREATE TABLE cache_stats (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            cache_type TEXT NOT NULL,
                            hits INTEGER DEFAULT 0,
                            misses INTEGER DEFAULT 0,
                            size_bytes INTEGER DEFAULT 0,
                            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                
                # Create indexes if enabled
                if self.config['database_cache']['indexes']:
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_citation_text ON citations(citation_text)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_case_name ON citations(case_name)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON citations(year)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_updated_at ON citations(updated_at)')
                
                conn.commit()
                logger.info("SQLite database initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def _compress_data(self, data: Any) -> bytes:
        """Compress data using gzip."""
        try:
            serialized = pickle.dumps(data)
            return gzip.compress(serialized)
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return pickle.dumps(data)
    
    def _decompress_data(self, data: bytes) -> Any:
        """Decompress data using gzip."""
        try:
            decompressed = gzip.decompress(data)
            return pickle.loads(decompressed)
        except Exception:
            # Fallback to direct pickle if not compressed
            return pickle.loads(data)
    
    def _get_redis_key(self, cache_type: str, key: str) -> str:
        """Generate Redis key with namespace."""
        return f"casestrainer:{cache_type}:{key}"
    
    def get_citation(self, citation: str) -> Optional[Dict[str, Any]]:
        """Get citation from cache (Redis first, then SQLite)."""
        if not self.redis_client:
            return self._get_from_sqlite('citations', citation)
        
        redis_key = self._get_redis_key('citation', citation)
        try:
            # Try Redis first
            cached_data = self.redis_client.get(redis_key)
            if cached_data:
                self._update_stats('citation', 'hit')
                return self._decompress_data(cached_data)
            
            # Fallback to SQLite
            result = self._get_from_sqlite('citations', citation)
            if result:
                # Cache in Redis for next time
                self._set_in_redis('citation', citation, result, 
                                 self.config['citation_cache']['ttl'])
            else:
                self._update_stats('citation', 'miss')
            
            return result
        except Exception as e:
            logger.error(f"Error getting citation {citation}: {e}")
            return self._get_from_sqlite('citations', citation)
    
    def set_citation(self, citation: str, data: Dict[str, Any]) -> bool:
        """Set citation in both Redis and SQLite."""
        success = True
        
        # Set in Redis
        if self.redis_client:
            try:
                redis_key = self._get_redis_key('citation', citation)
                compressed_data = self._compress_data(data)
                self.redis_client.setex(
                    redis_key,
                    self.config['citation_cache']['ttl'],
                    compressed_data
                )
            except Exception as e:
                logger.error(f"Redis set failed for {citation}: {e}")
                success = False
        
        # Set in SQLite
        try:
            self._set_in_sqlite('citations', citation, data)
        except Exception as e:
            logger.error(f"SQLite set failed for {citation}: {e}")
            success = False
        
        return success
    
    def get_url_content(self, url: str) -> Optional[str]:
        """Get URL content from cache."""
        if not self.redis_client:
            return None
        
        redis_key = self._get_redis_key('url', url)
        try:
            cached_data = self.redis_client.get(redis_key)
            if cached_data:
                self._update_stats('url', 'hit')
                return self._decompress_data(cached_data)
            else:
                self._update_stats('url', 'miss')
                return None
        except Exception as e:
            logger.error(f"Error getting URL content {url}: {e}")
            return None
    
    def set_url_content(self, url: str, content: str) -> bool:
        """Set URL content in Redis."""
        if not self.redis_client:
            return False
        
        try:
            redis_key = self._get_redis_key('url', url)
            compressed_data = self._compress_data(content)
            self.redis_client.setex(
                redis_key,
                self.config['url_cache']['ttl'],
                compressed_data
            )
            return True
        except Exception as e:
            logger.error(f"Error setting URL content {url}: {e}")
            return False
    
    def _get_from_sqlite(self, table: str, key: str) -> Optional[Dict[str, Any]]:
        """Get data from SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Handle the existing schema which uses citation_text
                if table == 'citations':
                    cursor.execute('SELECT * FROM citations WHERE citation_text = ?', (key,))
                else:
                    cursor.execute(f'SELECT * FROM {table} WHERE citation = ?', (key,))
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            logger.error(f"SQLite get failed: {e}")
            return None
    
    def _set_in_sqlite(self, table: str, key: str, data: Dict[str, Any]) -> bool:
        """Set data in SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Handle citations table specifically with existing schema
                if table == 'citations':
                    # Check if record exists
                    cursor.execute('SELECT id FROM citations WHERE citation_text = ?', (key,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing record
                        cursor.execute('''
                            UPDATE citations 
                            SET case_name = ?, year = ?, parallel_citations = ?, verification_result = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE citation_text = ?
                        ''', (
                            data.get('case_name'),
                            data.get('year'),
                            json.dumps(data.get('parallel_citations', [])),
                            json.dumps(data.get('verification_result', {})),
                            key
                        ))
                    else:
                        # Insert new record
                        cursor.execute('''
                            INSERT INTO citations 
                            (citation_text, case_name, year, parallel_citations, verification_result, found, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ''', (
                            key,
                            data.get('case_name'),
                            data.get('year'),
                            json.dumps(data.get('parallel_citations', [])),
                            json.dumps(data.get('verification_result', {})),
                            data.get('verification_result', {}).get('valid', False)
                        ))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"SQLite set failed: {e}")
            return False
    
    def _set_in_redis(self, cache_type: str, key: str, data: Any, ttl: int) -> bool:
        """Set data in Redis with TTL."""
        try:
            redis_key = self._get_redis_key(cache_type, key)
            compressed_data = self._compress_data(data)
            self.redis_client.setex(redis_key, ttl, compressed_data)
            return True
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
            return False
    
    def _update_stats(self, cache_type: str, stat_type: str):
        """Update cache statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO cache_stats (cache_type, hits, misses, last_updated)
                    VALUES (
                        ?,
                        CASE WHEN ? = 'hit' THEN 1 ELSE 0 END,
                        CASE WHEN ? = 'miss' THEN 1 ELSE 0 END,
                        CURRENT_TIMESTAMP
                    )
                ''', (cache_type, stat_type, stat_type))
                conn.commit()
        except Exception as e:
            logger.error(f"Stats update failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'redis_connected': self.redis_client is not None,
            'cache_stats': {},
            'memory_usage': {}
        }
        
        # Get SQLite stats
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT cache_type, hits, misses FROM cache_stats')
                for row in cursor.fetchall():
                    cache_type, hits, misses = row
                    total = hits + misses
                    hit_rate = (hits / total * 100) if total > 0 else 0
                    stats['cache_stats'][cache_type] = {
                        'hits': hits,
                        'misses': misses,
                        'hit_rate': f"{hit_rate:.1f}%"
                    }
        except Exception as e:
            logger.error(f"Stats retrieval failed: {e}")
        
        # Get Redis memory usage
        if self.redis_client:
            try:
                info = self.redis_client.info('memory')
                stats['memory_usage']['redis'] = {
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'used_memory_peak': info.get('used_memory_peak_human', 'N/A')
                }
            except Exception as e:
                logger.error(f"Redis memory info failed: {e}")
        
        return stats
    
    def warm_cache(self, limit: int = 1000) -> int:
        """Warm Redis cache from SQLite database."""
        if not self.redis_client:
            return 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Use the existing schema with citation_text column
                cursor.execute('''
                    SELECT citation_text, case_name, year, parallel_citations, verification_result
                    FROM citations 
                    ORDER BY updated_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                warmed = 0
                for row in cursor.fetchall():
                    citation, case_name, year, parallel_citations, verification_result = row
                    
                    # Convert existing data to new format
                    if verification_result:
                        try:
                            verification_data = json.loads(verification_result)
                        except:
                            verification_data = {
                                'valid': True,
                                'found': True,
                                'confidence': 0.8,
                                'source': 'database'
                            }
                    else:
                        verification_data = {
                            'valid': True,
                            'found': True,
                            'confidence': 0.8,
                            'source': 'database'
                        }
                    
                    data = {
                        'case_name': case_name or '',
                        'year': year,
                        'parallel_citations': json.loads(parallel_citations) if parallel_citations else [],
                        'verification_result': json.dumps(verification_data)
                    }
                    
                    if self._set_in_redis('citation', citation, data, 
                                        self.config['citation_cache']['ttl']):
                        warmed += 1
                
                logger.info(f"Warmed {warmed} citations in Redis cache")
                return warmed
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            return 0
    
    def clear_cache(self, cache_type: str = None):
        """Clear cache (Redis only, SQLite is persistent)."""
        if not self.redis_client:
            return
        
        try:
            if cache_type:
                pattern = f"casestrainer:{cache_type}:*"
            else:
                pattern = "casestrainer:*"
            
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} keys from Redis cache")
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")

# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> UnifiedCacheManager:
    """Get or create the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = UnifiedCacheManager()
    return _cache_manager 
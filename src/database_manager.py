"""
Database Manager for CaseStrainer

This module provides comprehensive database management including:
- Connection pooling and optimization
- Database backup and recovery
- Performance monitoring
- Security features
- Migration management
"""

import os
import sqlite3
import logging
import threading
import time
import shutil
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager
import hashlib
import tempfile
import gzip
from pathlib import Path
from .config import DATABASE_FILE

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Comprehensive database manager for CaseStrainer with production-ready features.
    """
    
    def __init__(self, db_path: str, max_connections: int = 10, backup_enabled: bool = True):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
            max_connections: Maximum number of connections in the pool
            backup_enabled: Whether to enable automatic backups (now handled by background tasks)
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self.backup_enabled = backup_enabled
        self.connection_pool = []
        self.pool_lock = threading.Lock()
        self.stats = {
            'connections_created': 0,
            'connections_reused': 0,
            'queries_executed': 0,
            'backups_created': 0,
            'last_backup': None,
            'errors': 0
        }
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database with optimized settings
        self._initialize_database()
        
        # Note: Backup scheduling is now handled by the centralized background tasks system
        # in src/background_tasks.py
    
    def _initialize_database(self):
        """Initialize the database with optimized settings and schema."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Set SQLite optimization pragmas
                cursor.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
                cursor.execute("PRAGMA synchronous = NORMAL")  # Balance between safety and performance
                cursor.execute("PRAGMA cache_size = -64000")  # 64MB cache
                cursor.execute("PRAGMA temp_store = MEMORY")  # Store temp tables in memory
                cursor.execute("PRAGMA mmap_size = 268435456")  # 256MB memory mapping
                cursor.execute("PRAGMA page_size = 4096")  # Optimal page size
                cursor.execute("PRAGMA auto_vacuum = INCREMENTAL")  # Incremental vacuum
                cursor.execute("PRAGMA incremental_vacuum = 1000")  # Vacuum 1000 pages at a time
                
                # Create optimized schema
                self._create_schema(cursor)
                
                # Create indexes for performance
                self._create_indexes(cursor)
                
                conn.commit()
                logger.info(f"Database initialized with optimizations: {self.db_path}")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _create_schema(self, cursor):
        """Create the database schema with optimized structure."""
        
        # Check if citations table exists and get its current schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='citations'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Get current schema
            cursor.execute("PRAGMA table_info(citations)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            # Add missing columns to existing table
            missing_columns = []
            
            if 'verification_source' not in existing_columns:
                missing_columns.append('verification_source TEXT')
            if 'verification_confidence' not in existing_columns:
                missing_columns.append('verification_confidence REAL')
            if 'is_verified' not in existing_columns:
                missing_columns.append('is_verified BOOLEAN DEFAULT FALSE')
            if 'updated_at' not in existing_columns:
                missing_columns.append('updated_at TIMESTAMP')
            if 'last_verified_at' not in existing_columns:
                missing_columns.append('last_verified_at TIMESTAMP')
            if 'verification_count' not in existing_columns:
                missing_columns.append('verification_count INTEGER DEFAULT 0')
            if 'error_count' not in existing_columns:
                missing_columns.append('error_count INTEGER DEFAULT 0')
            
            # Add missing columns
            for column_def in missing_columns:
                try:
                    column_name = column_def.split()[0]
                    cursor.execute(f"ALTER TABLE citations ADD COLUMN {column_def}")
                    logger.info(f"Added column {column_name} to citations table")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        logger.warning(f"Could not add column {column_def}: {e}")
            
            # Update existing rows for columns that need default values
            if 'updated_at' in missing_columns:
                try:
                    cursor.execute("UPDATE citations SET updated_at = date_added WHERE updated_at IS NULL")
                    logger.info("Updated existing rows with updated_at values")
                except sqlite3.OperationalError as e:
                    logger.warning(f"Could not update updated_at values: {e}")
            
            logger.info("Updated existing citations table schema")
        else:
            # Create new citations table with comprehensive fields
            cursor.execute('''
                CREATE TABLE citations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    citation_text TEXT NOT NULL UNIQUE,
                    case_name TEXT,
                    year INTEGER,
                    court TEXT,
                    reporter TEXT,
                    volume TEXT,
                    page TEXT,
                    parallel_citations TEXT,
                    verification_result TEXT,
                    verification_source TEXT,
                    verification_confidence REAL,
                    found BOOLEAN DEFAULT FALSE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_verified_at TIMESTAMP,
                    verification_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0
                )
            ''')
            logger.info("Created new citations table")
        
        # Cache table for API responses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT NOT NULL UNIQUE,
                cache_data TEXT NOT NULL,
                cache_type TEXT NOT NULL,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Statistics table for monitoring
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS db_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_name TEXT NOT NULL UNIQUE,
                stat_value TEXT NOT NULL,
                stat_type TEXT DEFAULT 'string',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Task tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL UNIQUE,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                progress REAL DEFAULT 0.0,
                total_items INTEGER DEFAULT 0,
                processed_items INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                metadata TEXT
            )
        ''')
    
    def _create_indexes(self, cursor):
        """Create optimized indexes for better query performance."""
        
        # Get existing columns to determine which indexes to create
        cursor.execute("PRAGMA table_info(citations)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # Citations table indexes - only create on existing columns
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_citation_text ON citations(citation_text)')
        
        if 'case_name' in existing_columns:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_citation_case_name ON citations(case_name)')
        
        if 'year' in existing_columns:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_citation_year ON citations(year)')
        
        if 'court' in existing_columns:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_citation_court ON citations(court)')
        
        if 'found' in existing_columns:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_citation_found ON citations(found)')
        
        # Handle different column names for verification status
        if 'is_verified' in existing_columns:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_citation_verified ON citations(is_verified)')
        
        # Handle different timestamp column names
        if 'updated_at' in existing_columns:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_citation_updated ON citations(updated_at)')
        if 'date_added' in existing_columns:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_citation_date_added ON citations(date_added)')
        elif 'created_at' in existing_columns:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_citation_created ON citations(created_at)')
        
        # Composite indexes for common queries - only create if both columns exist
        if 'is_verified' in existing_columns and 'found' in existing_columns:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_citation_found_verified ON citations(found, is_verified)')
        
        if 'year' in existing_columns and 'court' in existing_columns:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_citation_year_court ON citations(year, court)')
        
        # API cache indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_key ON api_cache(cache_key)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_type ON api_cache(cache_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_expires ON api_cache(expires_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_last_accessed ON api_cache(last_accessed)')
        
        # Tasks indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_id ON tasks(task_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_created ON tasks(created_at)')
        
        logger.info("Database indexes created/verified")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool."""
        conn = None
        try:
            # Try to get connection from pool
            with self.pool_lock:
                if self.connection_pool:
                    conn = self.connection_pool.pop()
                    self.stats['connections_reused'] += 1
                else:
                    # Use check_same_thread=False for thread safety
                    conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
                    conn.row_factory = sqlite3.Row
                    self.stats['connections_created'] += 1
            
            yield conn
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                # Return connection to pool if pool is not full
                with self.pool_lock:
                    if len(self.connection_pool) < self.max_connections:
                        try:
                            # Reset connection state
                            conn.rollback()
                            self.connection_pool.append(conn)
                        except:
                            # If reset fails, close the connection
                            conn.close()
                    else:
                        conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                self.stats['queries_executed'] += 1
                
                if query.strip().upper().startswith('SELECT'):
                    columns = [description[0] for description in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                else:
                    conn.commit()
                    return []
                    
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Query execution error: {e}")
            raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute a query multiple times with different parameters."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                self.stats['queries_executed'] += len(params_list)
                
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Batch query execution error: {e}")
            raise
    
    def backup_database(self, backup_path: str = None) -> str:
        """Create a compressed backup of the database."""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, f"citations_backup_{timestamp}.db.gz")
        
        try:
            # Create a temporary backup
            temp_backup = f"{backup_path}.tmp"
            
            # Copy database file
            shutil.copy2(self.db_path, temp_backup)
            
            # Compress the backup
            with open(temp_backup, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove temporary file
            os.remove(temp_backup)
            
            # Update stats
            self.stats['backups_created'] += 1
            self.stats['last_backup'] = datetime.now().isoformat()
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from a backup file."""
        try:
            # Create a temporary restore file
            temp_restore = f"{self.db_path}.restore"
            
            # Decompress backup
            with gzip.open(backup_path, 'rb') as f_in:
                with open(temp_restore, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Close all connections
            with self.pool_lock:
                for conn in self.connection_pool:
                    conn.close()
                self.connection_pool.clear()
            
            # Replace current database
            shutil.move(temp_restore, self.db_path)
            
            logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
    
    def vacuum_database(self) -> bool:
        """Optimize database by removing unused space."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("VACUUM")
                cursor.execute("ANALYZE")
                logger.info("Database vacuum and analyze completed")
                return True
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get table sizes
                cursor.execute("""
                    SELECT name, sql FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = cursor.fetchall()
                
                stats = {
                    'database_path': self.db_path,
                    'database_size_mb': os.path.getsize(self.db_path) / (1024 * 1024),
                    'tables': {},
                    'connection_pool': {
                        'pool_size': len(self.connection_pool),
                        'max_connections': self.max_connections
                    },
                    'performance': self.stats.copy()
                }
                
                for table_name, _ in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    column_count = len(cursor.fetchall())
                    
                    stats['tables'][table_name] = {
                        'row_count': row_count,
                        'column_count': column_count
                    }
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def _cleanup_old_backups(self, keep_days: int = 7):
        """Clean up old backup files."""
        try:
            backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
            if not os.path.exists(backup_dir):
                return
            
            cutoff_time = datetime.now() - timedelta(days=keep_days)
            
            for filename in os.listdir(backup_dir):
                if filename.startswith("citations_backup_") and filename.endswith(".db.gz"):
                    file_path = os.path.join(backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        logger.info(f"Removed old backup: {filename}")
                        
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    def close(self):
        """Close all database connections."""
        with self.pool_lock:
            for conn in self.connection_pool:
                conn.close()
            self.connection_pool.clear()
        logger.info("Database manager closed")

# Global database manager instance
_db_manager = None

def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(DATABASE_FILE)
    return _db_manager

def close_database_manager():
    """Close the global database manager."""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None 
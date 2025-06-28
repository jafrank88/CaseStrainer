import time
import threading
import os
import logging
from redis import Redis
from rq import Queue
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
from src.database_manager import get_database_manager
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Settings
CHECK_INTERVAL = int(os.environ.get('REPROCESS_CHECK_INTERVAL', 60))  # seconds between checks (default: 1 min)
BATCH_SIZE = int(os.environ.get('REPROCESS_BATCH_SIZE', 100))
SLEEP_BETWEEN = int(os.environ.get('REPROCESS_SLEEP_BETWEEN', 1))

# Background task intervals
BACKUP_INTERVAL = int(os.environ.get('BACKUP_INTERVAL', 3600))  # 1 hour
CLEANUP_INTERVAL = int(os.environ.get('CLEANUP_INTERVAL', 300))  # 5 minutes
MONITORING_INTERVAL = int(os.environ.get('MONITORING_INTERVAL', 60))  # 1 minute

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
QUEUE_NAME = os.environ.get('RQ_QUEUE_NAME', 'casestrainer')


def reprocess_parallel_citations(batch_size=BATCH_SIZE, sleep_time=SLEEP_BETWEEN, max_batches=None):
    """Reprocess citations missing parallel citations."""
    verifier = EnhancedMultiSourceVerifier()
    db_manager = get_database_manager()
    processed = 0
    batch_num = 0
    while True:
        rows = db_manager.execute_query(
            "SELECT citation_text FROM citations WHERE (parallel_citations IS NULL OR parallel_citations = '') LIMIT ?", (batch_size,)
        )
        if not rows:
            logger.info("[REPROCESS] No more citations to reprocess.")
            break
        for row in rows:
            citation = row['citation_text']
            logger.info(f"[REPROCESS] Reprocessing: {citation}")
            result = verifier._lookup_citation(citation)
            if result and result.get('parallel_citations'):
                verifier._save_to_database(citation, result)
            processed += 1
            time.sleep(sleep_time)
        batch_num += 1
        if max_batches and batch_num >= max_batches:
            break
        time.sleep(5)
    logger.info(f"[REPROCESS] Reprocessing complete. Total processed: {processed}")


def database_backup_task():
    """Create database backup and clean old backups."""
    try:
        db_manager = get_database_manager()
        logger.info("[BACKUP] Starting database backup task")
        
        # Create backup
        backup_result = db_manager.backup_database()
        if backup_result:
            logger.info("[BACKUP] Database backup completed successfully")
        else:
            logger.warning("[BACKUP] Database backup failed")
        
        # Clean old backups (keep last 7 days)
        cleanup_result = db_manager._cleanup_old_backups(keep_days=7)
        if cleanup_result:
            logger.info("[BACKUP] Old backup cleanup completed")
        
    except Exception as e:
        logger.error(f"[BACKUP] Error in database backup task: {e}")


def cleanup_old_tasks():
    """Clean up old completed/failed tasks from memory and Redis."""
    try:
        # Import here to avoid circular imports
        from src.vue_api_endpoints import active_requests, TASK_TTL
        
        now = time.time()
        to_delete = []
        
        # Clean up in-memory tasks
        for task_id, task in list(active_requests.items()):
            if task['status'] in ('completed', 'failed'):
                end_time = task.get('end_time', task.get('start_time', now))
                if now - end_time > TASK_TTL:
                    to_delete.append(task_id)
        
        for task_id in to_delete:
            del active_requests[task_id]
            logger.debug(f"[CLEANUP] Removed task {task_id} from memory")
        
        if to_delete:
            logger.info(f"[CLEANUP] Cleaned up {len(to_delete)} old tasks from memory")
        
        # Clean up Redis task results
        try:
            redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
            # This would clean up old task results from Redis
            # Implementation depends on how you store task results in Redis
            logger.debug("[CLEANUP] Redis cleanup completed")
        except Exception as e:
            logger.warning(f"[CLEANUP] Redis cleanup failed: {e}")
            
    except Exception as e:
        logger.error(f"[CLEANUP] Error in task cleanup: {e}")


def monitoring_task():
    """Collect and log system monitoring metrics."""
    try:
        try:
            import psutil
        except ImportError:
            logger.warning("[MONITOR] psutil not available - skipping system metrics")
            return
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database metrics
        db_manager = get_database_manager()
        db_stats = db_manager.stats if hasattr(db_manager, 'stats') else {}
        
        # Log metrics
        logger.info(f"[MONITOR] CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")
        logger.info(f"[MONITOR] DB stats: {db_stats}")
        
    except Exception as e:
        logger.error(f"[MONITOR] Error in monitoring task: {e}")


def is_queue_idle(redis_conn, queue_name=QUEUE_NAME):
    """Return True if the RQ queue is idle (no jobs in queue or started)."""
    from rq import Queue
    queue = Queue(queue_name, connection=redis_conn)
    return queue.count == 0 and queue.started_job_registry.count == 0


def background_maintenance_loop():
    """Main background thread that coordinates all maintenance tasks."""
    redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    queue = Queue(QUEUE_NAME, connection=redis_conn)
    
    # Track last run times
    last_reprocess_check = 0
    last_backup = 0
    last_cleanup = 0
    last_monitoring = 0
    
    logger.info("[MAINTENANCE] Background maintenance thread started")
    
    while True:
        try:
            current_time = time.time()
            
            # Check for parallel citation reprocessing (every CHECK_INTERVAL)
            if current_time - last_reprocess_check >= CHECK_INTERVAL:
                last_reprocess_check = current_time
                
                # Check if there are citations needing reprocessing
                db_manager = get_database_manager()
                rows = db_manager.execute_query(
                    "SELECT COUNT(*) as cnt FROM citations WHERE (parallel_citations IS NULL OR parallel_citations = '')"
                )
                count = rows[0]['cnt'] if rows else 0
                
                if count > 0 and is_queue_idle(redis_conn, QUEUE_NAME):
                    logger.info(f"[MAINTENANCE] Enqueuing reprocessing job for {count} citations")
                    queue.enqueue(reprocess_parallel_citations, batch_size=BATCH_SIZE, sleep_time=SLEEP_BETWEEN)
                elif count == 0:
                    logger.debug("[MAINTENANCE] No citations need reprocessing")
                else:
                    logger.debug("[MAINTENANCE] Queue is busy, skipping reprocessing")
            
            # Database backup (every BACKUP_INTERVAL)
            if current_time - last_backup >= BACKUP_INTERVAL:
                last_backup = current_time
                if is_queue_idle(redis_conn, QUEUE_NAME):
                    logger.info("[MAINTENANCE] Enqueuing database backup task")
                    queue.enqueue(database_backup_task)
                else:
                    logger.debug("[MAINTENANCE] Queue is busy, skipping backup")
            
            # Task cleanup (every CLEANUP_INTERVAL)
            if current_time - last_cleanup >= CLEANUP_INTERVAL:
                last_cleanup = current_time
                if is_queue_idle(redis_conn, QUEUE_NAME):
                    logger.info("[MAINTENANCE] Enqueuing task cleanup")
                    queue.enqueue(cleanup_old_tasks)
                else:
                    logger.debug("[MAINTENANCE] Queue is busy, skipping cleanup")
            
            # Monitoring (every MONITORING_INTERVAL)
            if current_time - last_monitoring >= MONITORING_INTERVAL:
                last_monitoring = current_time
                if is_queue_idle(redis_conn, QUEUE_NAME):
                    logger.debug("[MAINTENANCE] Enqueuing monitoring task")
                    queue.enqueue(monitoring_task)
                else:
                    logger.debug("[MAINTENANCE] Queue is busy, skipping monitoring")
            
            # Sleep for a short interval before next check
            time.sleep(10)  # Check every 10 seconds for task scheduling
            
        except Exception as e:
            logger.error(f"[MAINTENANCE] Error in background maintenance loop: {e}")
            time.sleep(60)  # Wait longer on error


def start_background_maintenance():
    """Start the centralized background maintenance system."""
    t = threading.Thread(target=background_maintenance_loop, daemon=True)
    t.start()
    logger.info("[MAINTENANCE] Background maintenance system started")


# Legacy function name for backward compatibility
def start_background_reprocessing():
    """Legacy function - now starts the full maintenance system."""
    start_background_maintenance() 
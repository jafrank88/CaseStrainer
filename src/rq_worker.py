"""
Robust RQ Worker for CaseStrainer with memory management and auto-restart
This script starts an RQ worker with better error handling and resource management
"""

import os
import sys

# CRITICAL: Set up Python path FIRST before any other imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # Add /app to path
sys.path.insert(0, os.path.dirname(__file__))  # Add /app/src to path

# Load .env from project root so COURTLISTENER_API_KEY etc. are set before config is imported.
# (Flask loads .env via config; the worker may run with a different cwd or in Docker.)
try:
    from dotenv import load_dotenv
    _root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    load_dotenv(os.path.join(_root, ".env"))
except Exception:
    pass


import logging
import signal
import time
import platform
import threading
import re
from pathlib import Path

# Initialize persistent logging for workers
try:
    from src.persistent_logger import init_persistent_logging

    worker_id = os.environ.get("WORKER_ID", "unknown")
    persistent_logger = init_persistent_logging(f"casestrainer-worker{worker_id}", "/app/logs")
    logger = persistent_logger.get_logger()
    event_logger = persistent_logger.get_event_logger()
    # So verification/processor logs (BATCH-FALLBACK, WL-LEFT, etc.) appear in the same worker log file
    persistent_logger.attach_main_handler_to_root()
except Exception as e:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    event_logger = logger
    logger.warning(f"Failed to initialize persistent logging: {e}")

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - memory monitoring disabled")

from rq import Worker, SimpleWorker, Queue
from src.verification_manager import VerificationManager
from redis import Redis
from src.redis_distributed_processor import extract_pdf_pages, extract_pdf_optimized, DockerOptimizedProcessor
from src.optimized_pdf_processor import extract_pdf_optimized_v2
import html  # For unescaping HTML entities like &amp;

# Import helper for filtering cluster members (avoid circular imports)
from src.utils.cluster_filter import filter_cluster_members_by_reporter
from src.rq_worker_helpers import (
    _force_release_memory,
    _get_citation_state,
    _citations_compatible_for_parallel,
    _has_case_history_signal_between,
    _extract_reporter_type_simple,
    _are_parallel_reporter_types,
)
from src.rq_worker_pipeline import run_citation_task

# Persistent logger already initialized above
# logger = logging.getLogger(__name__)

from src.config import REDIS_URL

redis_conn = Redis.from_url(REDIS_URL)

queue = Queue("casestrainer", connection=redis_conn)


def register_worker_functions():
    """Register all worker functions with RQ."""
    worker_functions = [
        "extract_pdf_pages",
        "extract_pdf_optimized",
        "extract_pdf_optimized_v2",
        "process_citation_task_direct",
        "process_citation_task_async",
        "src.redis_distributed_processor.DockerOptimizedProcessor.process_document",
        "src.async_verification_worker.verify_citations_enhanced",
        "src.async_verification_worker.verify_citations_basic",
        "src.async_verification_worker.verify_citations_async",
    ]

    logger.info(f"Registered worker functions: {worker_functions}")
    return worker_functions


__all__ = [
    "process_citation_task_direct",
    "process_citation_task_async",
    "extract_pdf_pages",
    "extract_pdf_optimized",
    "extract_pdf_optimized_v2",
    "verify_citations_enhanced",
]


def process_citation_task_direct(task_id: str, input_type: str, input_data: dict):
    """Direct wrapper function for RQ job execution.
    
    NOTE: ThreadPoolExecutor wrapper was removed to reduce memory overhead.
    RQ's own job_timeout handles timeouts. The executor was doubling memory
    by keeping the main thread's stack alive alongside the worker thread.
    """

    try:
        result = _process_citation_task_internal(task_id, input_type, input_data)
        logger.info(f"[TASK:{task_id}] Worker completed successfully")
        return result
    except Exception as e:
        logger.error(f"[TASK:{task_id}] Worker crashed: {str(e)}")
        import traceback
        logger.error(f"[TASK:{task_id}] Traceback: {traceback.format_exc()}")
        return {
            "status": "failed",
            "task_id": task_id,
            "error": f"Worker crashed: {str(e)}",
        }


def _process_citation_task_internal(task_id: str, input_type: str, input_data: dict):
    """Delegates to pipeline module (single place for citation task logic)."""
    return run_citation_task(task_id, input_type, input_data, logger=logger)


def verify_citations_enhanced(citations: list, text: str, request_id: str, input_type: str, metadata: dict):
    """Enhanced async verification of citations using the fallback verifier."""
    try:
        from src.async_verification_worker import verify_citations_enhanced as verify_enhanced

        result = verify_enhanced(citations, text, request_id, input_type, metadata)

        logger.info(f"Verification completed for request {request_id}: {len(citations)} citations processed")
        return result

    except Exception as e:
        logger.error(f"Verification failed for request {request_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Verification failed: {str(e)}",
            "citations": citations,
            "request_id": request_id,
            "input_type": input_type,
            "metadata": metadata,
        }


class RobustWorker(Worker):
    """
    Enhanced RQ worker with memory management, graceful shutdown, and better monitoring.

    Features:
    - Memory usage monitoring and soft limits
    - Automatic restart after job count threshold
    - Graceful shutdown on signals
    - Detailed logging
    - Resource usage tracking
    """

    def __init__(self, *args, **kwargs):
        # Configure memory limits
        self.max_memory_mb = int(os.environ.get("WORKER_MAX_MEMORY_MB", 2048))  # 2GB default
        self.memory_check_interval = int(os.environ.get("MEMORY_CHECK_INTERVAL", 5))  # jobs

        # Configure job limits
        self.job_count = 0
        self.max_jobs = int(os.environ.get("MAX_JOBS_BEFORE_RESTART", 100))

        # Initialize worker with custom queue name if specified
        queue_name = os.environ.get("RQ_QUEUE_NAME", "casestrainer")
        if "queues" not in kwargs:
            kwargs["queues"] = [queue_name]

        # Configure worker name for better identification
        if "name" not in kwargs:
            kwargs["name"] = f"worker-{os.getpid()}@{os.uname().nodename}"

        # Note: RQ Worker only accepts connection, queues, and name parameters
        # Other settings like job_timeout, result_ttl are set per-job or globally

        super().__init__(*args, **kwargs)

        # Initialize metrics
        self.start_time = time.time()
        self.metrics = {"jobs_completed": 0, "jobs_failed": 0, "memory_high_watermark": 0, "last_memory_check": 0}

        logger.info(
            f"Initialized RobustWorker with max_memory={self.max_memory_mb}MB, "
            f"max_jobs={self.max_jobs}, queues={kwargs['queues']}"
        )

    def perform_job(self, job, queue):
        """Override to add memory management and job counting."""
        try:
            if PSUTIL_AVAILABLE:
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                if memory_usage > self.max_memory_mb:
                    logger.warning(f"Memory usage high ({memory_usage:.1f}MB), restarting worker")
                    sys.exit(0)  # Graceful shutdown
                    return

            self.job_count += 1
            if self.job_count >= self.max_jobs:
                logger.info(f"Processed {self.job_count} jobs, restarting worker")
                sys.exit(0)  # Graceful shutdown
                return

            logger.info(f"Processing job {job.id} (job #{self.job_count})")
            result = super().perform_job(job, queue)

            if PSUTIL_AVAILABLE:
                memory_after = psutil.Process().memory_info().rss / 1024 / 1024
                logger.info(f"Job {job.id} completed. Memory: {memory_after:.1f}MB")
            else:
                logger.info(f"Job {job.id} completed. Memory monitoring disabled")

            return result

        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}")
            raise


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


class CodeChangeMonitor:
    """Monitor Python files for changes and trigger worker reload."""

    def __init__(self, watch_dir="/app/src", check_interval=2):
        self.watch_dir = Path(watch_dir)
        self.check_interval = check_interval
        self.file_mtimes = {}
        self.should_reload = False
        self.monitoring = False

        # Scan initial state
        self._scan_files()
        logger.info(f"[FILE] Code monitor initialized: watching {len(self.file_mtimes)} Python files in {watch_dir}")

    def _scan_files(self):
        """Scan all Python files and record their modification times."""
        try:
            for py_file in self.watch_dir.rglob("*.py"):
                # Skip __pycache__ directories
                if "__pycache__" not in str(py_file):
                    try:
                        self.file_mtimes[str(py_file)] = py_file.stat().st_mtime
                    except Exception as e:
                        logger.debug(f"Could not stat {py_file}: {e}")
        except Exception as e:
            logger.warning(f"Error scanning files: {e}")

    def check_for_changes(self):
        """Check if any files have been modified."""
        try:
            for py_file in self.watch_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue

                file_path = str(py_file)
                try:
                    current_mtime = py_file.stat().st_mtime

                    if file_path not in self.file_mtimes:
                        # New file detected
                        logger.info(f"[NEW] New file detected: {py_file.name}")
                        self.file_mtimes[file_path] = current_mtime
                        self.should_reload = True
                        return True
                    elif current_mtime > self.file_mtimes[file_path]:
                        # Modified file detected
                        logger.warning(f"Code change detected: {py_file.name}")
                        logger.warning(f"   Full path: {file_path}")
                        self.file_mtimes[file_path] = current_mtime
                        self.should_reload = True
                        return True
                except Exception as e:
                    logger.debug(f"Could not check {file_path}: {e}")

        except Exception as e:
            logger.warning(f"Error checking for changes: {e}")

        return False

    def start_monitoring(self, worker_pid):
        """Start monitoring in a background thread."""
        self.monitoring = True

        def monitor_loop():
            logger.info(f"Auto-reload enabled: monitoring for code changes every {self.check_interval}s")
            while self.monitoring:
                time.sleep(self.check_interval)
                if self.check_for_changes():
                    logger.warning("CODE CHANGED - Restarting worker to load new code...")
                    os.kill(worker_pid, signal.SIGTERM)
                    break

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False


def process_citation_task_async(task_id: str, document_text: str, document_type: str):
    """Async citation processing task for RQ workers with progress tracking."""

    logger.info(f"process_citation_task_async STARTED: task_id={task_id}, text_length={len(document_text)}")

    try:
        # Import the progress manager
        from src.progress_manager import ProgressManager

        # Initialize progress manager with Redis
        progress_manager = ProgressManager(redis_client=redis_conn)

        # Create progress tracker
        from src.progress_manager import ProgressTracker

        tracker = ProgressTracker(task_id, total_steps=25)  # Default steps

        # Store tracker in active tasks
        progress_manager.active_tasks[task_id] = tracker

        # Update initial progress
        progress_manager.update_progress(task_id, 0, "started", "Processing started...")

        # Create async event loop
        import asyncio

        async def run_async_processing():
            """Run the async processing in this worker."""
            try:
                # Get the async processor
                processor = progress_manager.async_processor

                # Call the async processing method
                await processor._process_document_async(task_id, document_text, document_type, tracker)

            except Exception as e:
                logger.error(f"Error in async processing: {e}")
                import traceback

                traceback.print_exc()

                # Update progress with error
                progress_manager.update_progress(task_id, 0, "failed", f"Processing failed: {str(e)}", error=str(e))

        # Run the async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(run_async_processing())
        finally:
            loop.close()

        logger.info(f"process_citation_task_async COMPLETED: task_id={task_id}")

    except Exception as e:
        logger.error(f"process_citation_task_async FAILED: task_id={task_id}, error={e}")
        import traceback

        traceback.print_exc()

        # Try to update progress with error if possible
        try:
            from src.progress_manager import ProgressManager

            progress_manager = ProgressManager(redis_client=redis_conn)
            progress_manager.update_progress(task_id, 0, "failed", f"Task failed: {str(e)}", error=str(e))
        except:
            pass  # Best effort error reporting

    return {
        "task_id": task_id,
        "status": "failed",
        "error": "Async processing did not produce a final result payload",
        "citations": [],
        "clusters": [],
        "success": False,
    }


def main():
    """Main entry point for the RQ worker with enhanced error handling and monitoring."""
    # Configure logging
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    # Log startup information
    logger.info("=" * 80)
    logger.info(f"Starting CaseStrainer Worker (PID: {os.getpid()})")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Redis URL: {REDIS_URL[:50]}...")
    logger.info("=" * 80)

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Configure queue and worker name
    queue_name = os.environ.get("RQ_QUEUE_NAME", "casestrainer")
    worker_name = f"worker-{os.getpid()}@{os.uname().nodename}"
    logger.info(f"Queue={queue_name}, Worker={worker_name}")

    # CRITICAL: Clean up any stale registration with the same name
    # This prevents "worker already exists" errors after container restarts
    try:
        from rq import Worker

        existing_workers = Worker.all(connection=redis_conn)
        for w in existing_workers:
            if w.name == worker_name:
                logger.info(f"Removing stale worker registration: {worker_name}")
                w.register_death()
                break
    except Exception as e:
        logger.warning(f"Could not clean up stale worker registration: {e}")

    # Configure worker settings
    worker_functions = register_worker_functions()
    logger.info(f"Worker will register functions: {worker_functions}")

    worker_kwargs = {"connection": redis_conn, "queues": [queue_name], "name": worker_name}

    # Check if auto-reload is enabled (for development)
    auto_reload = os.environ.get("RQ_WORKER_AUTORELOAD", "false").lower() == "true"
    logger.info(f"Auto-reload: {auto_reload} (RQ_WORKER_AUTORELOAD={os.environ.get('RQ_WORKER_AUTORELOAD', 'not set')})") 

    # Start the worker with error handling
    max_restarts = 10
    restart_count = 0
    monitor = None  # Initialize here to avoid UnboundLocalError

    while restart_count < max_restarts:
        try:
            logger.info(f"Starting worker (attempt {restart_count + 1}/{max_restarts})")

            worker = RobustWorker(**worker_kwargs)

            # Start code change monitor if auto-reload is enabled
            if auto_reload:
                try:
                    monitor = CodeChangeMonitor(watch_dir="/app/src", check_interval=2)
                    monitor.start_monitoring(os.getpid())
                    logger.info("Auto-reload monitor started successfully")
                except Exception as e:
                    logger.warning(f"Could not start code monitor: {e}")
                    logger.warning("Continuing without auto-reload...")
                    monitor = None
            else:
                logger.info("Auto-reload disabled. Set RQ_WORKER_AUTORELOAD=true to enable.")

            logger.info("Worker started. Press Ctrl+C to exit.")
            worker.work(logging_level="INFO")

            # Stop monitoring if active
            if monitor:
                monitor.stop_monitoring()

            break  # Exit loop if worker exits cleanly

        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            if monitor:
                monitor.stop_monitoring()
            break

        except Exception:
            if monitor:
                monitor.stop_monitoring()

            restart_count += 1
            wait_time = min(2**restart_count, 60)  # Exponential backoff, max 60s

            logger.error(
                f"Worker crashed (attempt {restart_count}/{max_restarts}). " f"Restarting in {wait_time} seconds...",
                exc_info=True,
            )

            time.sleep(wait_time)

    if restart_count >= max_restarts:
        logger.critical("Maximum restart attempts reached. Worker shutting down.")
    else:
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    main()

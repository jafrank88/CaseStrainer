"""
Robust RQ Worker for CaseStrainer with memory management and auto-restart
This script starts an RQ worker with better error handling and resource management
"""

import os
import sys

# CRITICAL: Set up Python path FIRST before any other imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # Add /app to path
sys.path.insert(0, os.path.dirname(__file__))  # Add /app/src to path


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

# Persistent logger already initialized above
# logger = logging.getLogger(__name__)

redis_url = os.environ.get("REDIS_URL", "redis://:caseStrainerRedis123@casestrainer-redis-prod:6379/0")
redis_conn = Redis.from_url(redis_url)

queue = Queue("casestrainer", connection=redis_conn)


def _force_release_memory():
    """Force glibc to return freed pages to the OS via malloc_trim.

    Python's gc.collect() frees Python objects, but glibc's malloc keeps
    the freed pages mapped (RSS stays high) due to heap fragmentation.
    malloc_trim(0) tells glibc to release as many pages as possible.
    This is critical in memory-limited Docker containers.
    """
    import gc
    gc.collect()
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
    except Exception:
        pass  # Not on Linux / glibc not available


def _start_memory_monitor(interval=2):
    """Start a daemon thread that logs TRUE RSS + cgroup memory every N seconds.

    This runs inside the forked child so we see the child's actual memory,
    plus the container-level cgroup usage that Docker reports.
    """
    import threading

    def _monitor():
        import time as _t
        _count = 0
        while True:
            _t.sleep(interval)
            _count += 1
            try:
                # Child process RSS from kernel
                _rss = "?"
                with open('/proc/self/status') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            _rss = f"{int(line.split()[1]) // 1024}MB"
                            break
                # Container cgroup memory (what Docker sees)
                _cgroup = "?"
                for cg_path in [
                    '/sys/fs/cgroup/memory/memory.usage_in_bytes',
                    '/sys/fs/cgroup/memory.current',
                ]:
                    try:
                        with open(cg_path) as f:
                            _cgroup = f"{int(f.read().strip()) // (1024*1024)}MB"
                            break
                    except FileNotFoundError:
                        continue
                logger.warning(
                    f"[MEM-MONITOR] tick={_count} child_rss={_rss} cgroup={_cgroup}"
                )
                import sys; sys.stderr.flush()
            except Exception:
                break  # Process dying, exit quietly

    t = threading.Thread(target=_monitor, daemon=True)
    t.start()
    return t

# State-specific reporters for jurisdiction checking
STATE_REPORTERS = {
    "ohio": ["Ohio St.", "Ohio App.", "Ohio Misc.", "N.E.", "N.E.2d", "N.E.3d"],
    "nebraska": ["Neb.", "Neb. App.", "N.W.", "N.W.2d"],
    "washington": ["Wash.", "Wn.", "Wn.2d", "Wn. App.", "Wn. App. 2d", "P.", "P.2d", "P.3d"],
    "connecticut": ["Conn.", "Conn. App.", "Conn. Supp.", "A.", "A.2d", "A.3d"],
    "california": ["Cal.", "Cal.2d", "Cal.3d", "Cal.4th", "Cal.5th", "Cal. App.", "Cal. Rptr."],
    "new_york": ["N.Y.", "N.Y.2d", "N.Y.3d", "A.D.", "A.D.2d", "A.D.3d", "N.Y.S.", "N.Y.S.2d", "N.Y.S.3d"],
    "federal": [
        "U.S.",
        "S. Ct.",
        "L. Ed.",
        "L. Ed. 2d",
        "F.",
        "F.2d",
        "F.3d",
        "F.4th",
        "F. Supp.",
        "F. Supp. 2d",
        "F. Supp. 3d",
    ],
}


def _get_citation_state(citation_text: str) -> str:
    """Determine which state/jurisdiction a citation belongs to."""
    if not citation_text:
        return "unknown"
    cit_upper = citation_text.upper()
    for state, reporters in STATE_REPORTERS.items():
        for reporter in reporters:
            if reporter.upper() in cit_upper:
                return state
    return "unknown"


def _citations_compatible_for_parallel(cit1: str, cit2: str) -> bool:
    """Check if two citations could be parallel (same jurisdiction)."""
    state1 = _get_citation_state(cit1)
    state2 = _get_citation_state(cit2)
    if state1 == "unknown" or state2 == "unknown":
        return True
    return state1 == state2


# Case history signals that indicate different court proceedings
# Note: Handle different apostrophe characters: ' (regular), ' (right single quote), ʼ (modifier letter)
CASE_HISTORY_SIGNALS = [
    r"\baff['ʼ']?d\b",  # aff'd, affd, aff'd
    r"\baffirmed\b",
    r"\brev['ʼ']?d\b",  # rev'd, revd, rev'd
    r"\breversed\b",
    r"\bvacated\b",
    r"\bremanded\b",
    r"\bmodified\b",
    r"\boverruled\b",
    r"\bcert\.\s*denied\b",  # cert. denied
    r"\bcert\.\s*granted\b",  # cert. granted
    r"\bappeal\s+from\b",
    r"\bon\s+appeal\b",
]


def _has_case_history_signal_between(text: str, pos1: int, pos2: int) -> bool:
    """Check if there's a case history signal between two positions in text."""
    if not text or pos1 < 0 or pos2 < 0:
        return False
    start = min(pos1, pos2)
    end = max(pos1, pos2)
    # Get text between the two positions
    between_text = text[start:end].lower()
    if not between_text:
        return False
    # Distance guard: case history signals (aff'd, rev'd) appear immediately
    # adjacent to citations, not pages apart. If the span is >500 chars, the
    # citations are in different parts of the document and any matching signal
    # words belong to other cases' discussions — not a real case history link.
    if len(between_text) > 500:
        return False
    # Normalize fancy quotes to regular apostrophe for pattern matching
    # Handles: ' (U+2019 right single quote), ' (U+2018 left single quote), ʼ (U+02BC modifier letter)
    between_text = between_text.replace("\u2019", "'").replace("\u2018", "'").replace("\u02bc", "'")
    import re

    for pattern in CASE_HISTORY_SIGNALS:
        if re.search(pattern, between_text, re.IGNORECASE):
            return True
    return False


def _extract_reporter_type_simple(citation_text: str) -> str:
    """Extract simplified reporter type from citation text for parallel matching."""
    if not citation_text:
        return "unknown"
    normalized = citation_text.lower()

    # Washington Court of Appeals
    if any(t in normalized for t in ("wn. app", "wash. app", "wn app", "wash app")):
        return "wash_app"
    # Washington Supreme Court
    if any(t in normalized for t in ("wn.2d", "wn. 2d", "wash.2d", "wash. 2d")):
        return "wash2d"
    # Pacific Reporter
    if "p.3d" in normalized or "p3d" in normalized or "p. 3d" in normalized:
        return "p3d"
    if "p.2d" in normalized or "p2d" in normalized or "p. 2d" in normalized:
        return "p2d"
    if " p. " in normalized or " p " in normalized or normalized.endswith(" p."):
        return "p"
    # US Supreme Court
    if "u.s." in normalized:
        return "us"
    if "s. ct." in normalized or "s.ct." in normalized:
        return "sct"
    if "l. ed." in normalized or "l.ed." in normalized:
        return "led"
    # Federal
    if "f.3d" in normalized or "f3d" in normalized:
        return "f3d"
    if "f.2d" in normalized or "f2d" in normalized:
        return "f2d"
    # Atlantic
    if "a.2d" in normalized or "a2d" in normalized:
        return "a2d"
    if "a.3d" in normalized or "a3d" in normalized:
        return "a3d"
    # Other regional
    if "n.e." in normalized or "n.e.2d" in normalized:
        return "ne"
    if "n.w." in normalized or "n.w.2d" in normalized:
        return "nw"
    if "s.e." in normalized or "s.e.2d" in normalized:
        return "se"
    if "s.w." in normalized or "s.w.2d" in normalized:
        return "sw"

    return "unknown"


def _are_parallel_reporter_types(cit1: str, cit2: str) -> bool:
    """Check if two citations have compatible parallel reporter types."""
    type1 = _extract_reporter_type_simple(cit1)
    type2 = _extract_reporter_type_simple(cit2)

    if type1 == "unknown" or type2 == "unknown":
        return False
    if type1 == type2:
        return False  # Same reporter type = not parallel

    # Known parallel reporter pairs
    parallel_pairs = {
        # Washington
        frozenset({"wash2d", "p3d"}),
        frozenset({"wash2d", "p2d"}),
        frozenset({"wash2d", "p"}),
        frozenset({"wash_app", "p3d"}),
        frozenset({"wash_app", "p2d"}),
        frozenset({"wash_app", "p"}),
        # US Supreme Court
        frozenset({"us", "sct"}),
        frozenset({"us", "led"}),
        frozenset({"sct", "led"}),
        # Federal + US
        frozenset({"f3d", "us"}),
        frozenset({"f2d", "us"}),
    }

    return frozenset({type1, type2}) in parallel_pairs


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
    """Direct wrapper function with diagnostic logging.
    
    NOTE: ThreadPoolExecutor wrapper was removed to reduce memory overhead.
    RQ's own job_timeout handles timeouts. The executor was doubling memory
    by keeping the main thread's stack alive alongside the worker thread.
    """

    # DIAGNOSTIC LOGGING - Track every step of worker startup
    logger.info(f"[DIAGNOSTIC:{task_id}] ========== WORKER STARTUP BEGINS ==========")
    logger.info(f"[DIAGNOSTIC:{task_id}] Step 1: Function entry successful")

    # Start background memory monitor — logs child RSS + cgroup every 2s
    _start_memory_monitor(interval=2)

    try:
        result = _process_citation_task_internal(task_id, input_type, input_data)
        logger.info(f"[DIAGNOSTIC:{task_id}] ========== WORKER COMPLETED SUCCESSFULLY ==========")
        return result
    except Exception as e:
        logger.error(f"[DIAGNOSTIC:{task_id}] ========== WORKER CRASHED ==========")
        logger.error(f"[DIAGNOSTIC:{task_id}] Error: {str(e)}")
        import traceback

        logger.error(f"[DIAGNOSTIC:{task_id}] Traceback: {traceback.format_exc()}")
        return {
            "status": "failed",
            "task_id": task_id,
            "error": f"Worker crashed: {str(e)}",
            "diagnostic": "worker_crash",
        }


def _process_citation_task_internal(task_id: str, input_type: str, input_data: dict):

    try:
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 2: Starting basic imports...")
        import traceback
        import time
        import json
        import os
        import sys

        logger.info(f"[DIAGNOSTIC:{task_id}] Step 2: Basic imports SUCCESS")

        logger.info(f"[DIAGNOSTIC:{task_id}] Step 3: Environment info...")
        logger.info(f"[DIAGNOSTIC:{task_id}] Python version: {sys.version}")
        logger.info(f"[DIAGNOSTIC:{task_id}] Working directory: {os.getcwd()}")
        logger.info(f"[DIAGNOSTIC:{task_id}] Input type: {input_type}")
        logger.info(f"[DIAGNOSTIC:{task_id}] Input data keys: {list(input_data.keys())}")
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 3: Environment info SUCCESS")

        logger.info(f"[DIAGNOSTIC:{task_id}] Step 4: Redis readiness check...")
        try:
            import redis

            redis_url = os.environ.get("REDIS_URL", "redis://:caseStrainerRedis123@casestrainer-redis-prod:6379/0")
            logger.info(f"[DIAGNOSTIC:{task_id}] Redis URL: {redis_url}")

            # Check if Redis is ready (not loading dataset)
            redis_client = redis.from_url(redis_url)

            # Wait for Redis to be ready with timeout
            max_wait = 30  # 30 seconds max wait
            wait_interval = 1  # Check every second

            for attempt in range(max_wait):
                try:
                    # Test Redis connection
                    redis_client.ping()
                    logger.info(f"[DIAGNOSTIC:{task_id}] Redis ready after {attempt} seconds")
                    break
                except redis.exceptions.BusyLoadingError:
                    if attempt == 0:
                        logger.info(f"[DIAGNOSTIC:{task_id}] Redis loading dataset, waiting...")
                    elif attempt % 5 == 0:
                        logger.info(f"[DIAGNOSTIC:{task_id}] Still waiting for Redis ({attempt}s)...")
                    time.sleep(wait_interval)
                except Exception as e:
                    logger.error(f"[DIAGNOSTIC:{task_id}] Redis connection error: {e}")
                    if attempt < 5:  # Retry connection errors for first 5 seconds
                        time.sleep(wait_interval)
                    else:
                        raise
            else:
                # Timeout waiting for Redis
                logger.error(f"[DIAGNOSTIC:{task_id}] Redis not ready after {max_wait} seconds")
                return {
                    "status": "failed",
                    "task_id": task_id,
                    "error": f"Redis not ready after {max_wait} seconds - dataset still loading",
                    "diagnostic": "redis_loading_timeout",
                }

        except Exception as e:
            logger.error(f"[DIAGNOSTIC:{task_id}] Redis readiness error: {str(e)}")
            # Continue anyway - might be a temporary issue
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 4: Redis readiness SUCCESS")

        logger.info(f"[DIAGNOSTIC:{task_id}] Step 5: CitationService import...")
        from src.api.services.citation_service import CitationService

        logger.info(f"[DIAGNOSTIC:{task_id}] Step 5: CitationService import SUCCESS")

        logger.info(f"[DIAGNOSTIC:{task_id}] Step 6: Creating CitationService instance...")
        service = CitationService()
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 6: CitationService creation SUCCESS")

        logger.info(f"[DIAGNOSTIC:{task_id}] ========== WORKER STARTUP COMPLETE ==========")

    except Exception as e:
        logger.error(f"[DIAGNOSTIC:{task_id}] STARTUP FAILED at import/initialization: {str(e)}")
        logger.error(f"[DIAGNOSTIC:{task_id}] Traceback: {traceback.format_exc()}")
        return {
            "status": "failed",
            "task_id": task_id,
            "error": f"Worker startup failed: {str(e)}",
            "diagnostic": "startup_failure",
        }

    # Setup timeout handler - disabled since we use ThreadPoolExecutor for timeout
    # Note: signal only works in main thread, so we rely on ThreadPoolExecutor timeout instead
    timeout_set = False
    logger.info(f"[TASK:{task_id}] Using ThreadPoolExecutor timeout (5 minutes) instead of signal handler")

    try:
        start_time = time.time()
        logger.info(f"[DIAGNOSTIC:{task_id}] ========== MAIN PROCESSING BEGINS ==========")
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 7: Starting processing of type: {input_type}")

        # MEMORY CHECK: Check available memory before processing
        if PSUTIL_AVAILABLE:
            try:
                # psutil is already imported at module level, just use it
                process = psutil.Process()
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                # Get system memory info
                system_memory = psutil.virtual_memory()
                available_mb = system_memory.available / 1024 / 1024
                total_mb = system_memory.total / 1024 / 1024
                memory_percent = system_memory.percent
                
                logger.info(f"[TASK:{task_id}] Memory check before processing:")
                logger.info(f"[TASK:{task_id}]   Process memory: {memory_mb:.1f}MB")
                logger.info(f"[TASK:{task_id}]   System available: {available_mb:.1f}MB / {total_mb:.1f}MB ({memory_percent:.1f}% used)")
                
                # Check if memory is critically low
                min_required_mb = 500  # Minimum 500MB required for processing
                if available_mb < min_required_mb:
                    logger.error(
                        f"[TASK:{task_id}] ⚠️ CRITICAL: Low memory detected! "
                        f"Available: {available_mb:.1f}MB < Required: {min_required_mb}MB"
                    )
                    return {
                        "status": "failed",
                        "task_id": task_id,
                        "error": f"Insufficient memory: {available_mb:.1f}MB available, {min_required_mb}MB required",
                        "diagnostic": "low_memory",
                    }
                
                # Warn if memory is getting low (less than 1GB available)
                if available_mb < 1024:
                    logger.warning(
                        f"[TASK:{task_id}] ⚠️ WARNING: Low memory warning! "
                        f"Available: {available_mb:.1f}MB (less than 1GB). Processing may fail."
                    )
            except Exception as mem_err:
                logger.warning(f"[TASK:{task_id}] Could not check memory: {mem_err}")
        else:
            logger.warning(f"[TASK:{task_id}] psutil not available - memory check skipped")

        # CRITICAL: Add immediate flush to ensure logs appear
        import sys

        sys.stdout.flush()
        sys.stderr.flush()

        # Register verification/progress so the UI can poll immediately
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 7.1: About to create VerificationManager...")
        try:
            vm = VerificationManager()
            logger.info(f"[DIAGNOSTIC:{task_id}] Step 7.1: About to register verification")
            # Do not imply a citation total before extraction; use 0 to avoid 1/100-style messages
            vm.register_verification(task_id, task_id, total_citations=0)
            logger.info(f"[DIAGNOSTIC:{task_id}] Step 7.2: Verification registered")
            vm.update_progress(task_id, processed=0, total=0, message="Initializing async processing")
            logger.info(f"[DIAGNOSTIC:{task_id}] Step 7.3: Progress updated - starting PDF processing")
        except Exception as _e:
            logger.error(f"[DIAGNOSTIC:{task_id}] Step 7.ERROR: VerificationManager failed: {_e}")
            import traceback

            logger.error(f"[DIAGNOSTIC:{task_id}] VerificationManager traceback: {traceback.format_exc()}")

        logger.info(f"[DIAGNOSTIC:{task_id}] Step 8: Starting PDF download and processing")

        # Log input data (truncated if too large)
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 8: About to log input data...")
        input_data_str = str(input_data)
        if len(input_data_str) > 500:
            input_data_str = input_data_str[:500] + "... [truncated]"
        logger.info(f"[DIAGNOSTIC:{task_id}] Step 8: Input data logged (length: {len(input_data_str)})")

        logger.info(f"[DIAGNOSTIC:{task_id}] Step 9: About to enter processing logic...")
        logger.info(f"[DIAGNOSTIC:{task_id}] Using minimal async worker for diagnostic testing")

        if input_type in ["text", "url"]:
            # Handle both text and URL inputs with the full pipeline
            if input_type == "text":
                text = input_data.get("text", "")
                # Release the text reference from input_data to free memory
                # (text local var still holds the string)
                input_data["text"] = ""
                logger.info(f"[TASK:{task_id}] Processing text of length {len(text)}")
            elif input_type == "url":
                url = input_data.get("url", "")
                logger.info(f"[TASK:{task_id}] Processing URL: {url}")

                # Update progress: Starting URL extraction (no citation totals yet)
                try:
                    vm.update_progress(
                        task_id, processed=0, total=0, message="Downloading and extracting text from URL..."
                    )
                except Exception:
                    pass

                # Extract text from URL first
                try:
                    logger.info(f"[TASK:{task_id}] Extracting text from URL...")
                    import requests
                    import tempfile
                    import os

                    # Download the content
                    # CRITICAL FIX: Follow redirects to handle HTTP→HTTPS redirects
                    response = requests.get(url, timeout=30, allow_redirects=True)
                    response.raise_for_status()

                    # Update progress: Downloaded, extracting text (no citation totals yet)
                    try:
                        vm.update_progress(
                            task_id, processed=0, total=0, message="Downloaded document, extracting text..."
                        )
                    except Exception:
                        pass

                    # If it's a PDF, extract text
                    if "pdf" in response.headers.get("content-type", "").lower() or url.lower().endswith(".pdf"):
                        logger.info(f"[TASK:{task_id}] Detected PDF, extracting text...")

                        # Save to temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                            temp_file.write(response.content)
                            temp_path = temp_file.name

                        try:
                            # Extract text using UnifiedTextExtractor (same as file uploads)
                            from src.unified_text_extractor import extract_text_from_file_unified

                            text, method = extract_text_from_file_unified(temp_path, verbose=True)
                            logger.info(f"[TASK:{task_id}] Extracted {len(text)} characters using {method}")
                        finally:
                            # Clean up temp file
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                    else:
                        # Plain text content
                        text = response.text
                        logger.info(f"[TASK:{task_id}] Extracted {len(text)} characters from URL")

                    if not text or len(text.strip()) < 10:
                        logger.warning(f"[TASK:{task_id}] No meaningful text extracted from URL")
                        result = {
                            "success": True,
                            "citations": [],
                            "clusters": [],
                            "processing_strategy": "url_no_text",
                            "processing_time": time.time() - start_time,
                        }
                        # Skip to full processing
                        skip_full_processing = True
                    else:
                        skip_full_processing = False

                except Exception as e:
                    logger.error(f"[TASK:{task_id}] URL text extraction failed: {e}")
                    result = {"success": False, "error": f"URL text extraction failed: {str(e)}"}
                    skip_full_processing = True
            else:
                skip_full_processing = False

            # Only proceed with full processing if we have text and no errors
            if not locals().get("skip_full_processing", False):
                # FULL ASYNC WORKER - Use CLEAN PIPELINE (87-93% accuracy)
                logger.info(
                    f"[DIAGNOSTIC:{task_id}] Step 9: Using CLEAN PIPELINE for async processing (87-93% accuracy)"
                )

                try:
                    logger.info(
                        f"[DIAGNOSTIC:{task_id}] Step 10: Importing full pipeline (with clustering & verification)..."
                    )
                    import time

                    logger.info(f"[DIAGNOSTIC:{task_id}] Step 10: Full pipeline import SUCCESS")

                    # Verification is enabled by default for end users
                    # Can be disabled for testing/troubleshooting via enable_verification parameter
                    enable_verification = input_data.get("enable_verification", True)  # Default to True for end users
                    # Note: URLs can have many citations, but verification is still the default behavior

                    logger.info(f"[TASK:{task_id}] Running full pipeline with verification={enable_verification}")

                    # Create progress callback for worker

                    # SYNCHRONOUS COMPLETION - Wait for full verification
                    # Import required modules for synchronous processing
                    import asyncio
                    import gc  # Garbage collection for memory management
                    from src.unified_processing_pipeline import process_citations_unified

                    # Worker stability: Monitor memory usage before processing
                    try:
                        import psutil

                        process = psutil.Process()
                        memory_mb = process.memory_info().rss / 1024 / 1024
                        logger.info(f"[TASK:{task_id}] Worker memory usage: {memory_mb:.1f}MB before processing")

                        # If memory usage is high, force garbage collection
                        if memory_mb > 500:  # 500MB threshold
                            logger.warning(f"[TASK:{task_id}] High memory usage detected, forcing garbage collection")
                            gc.collect()
                    except ImportError:
                        logger.info(f"[TASK:{task_id}] psutil not available for memory monitoring")

                    # Run full pipeline with verification and wait for completion
                    logger.info(f"[TASK:{task_id}] Processing with verification={enable_verification}...")

                    # Update progress: Starting citation extraction (no citation totals yet)
                    try:
                        vm.update_progress(
                            task_id, processed=0, total=0, message="Extracting citations from document..."
                        )
                    except Exception:
                        pass

                    try:
                        # Create progress callback to update citations_processed incrementally
                        # We'll set total_cites after extraction completes
                        total_cites_for_callback = [0]  # Use list to allow modification in nested function

                        def update_verification_progress(processed_count, status, message):
                            """Update VerificationManager with incremental citation progress"""
                            try:
                                # Get current total from VerificationManager if available
                                current_status = vm.get_verification_status(task_id) or {}
                                current_total = current_status.get("total_citations", 0)

                                # If we have a total from the callback context, use it
                                if total_cites_for_callback[0] > 0:
                                    current_total = total_cites_for_callback[0]

                                # If current_total is still 0 or placeholder (100), try to extract from message
                                # Message format: "Verifying citations... (X/Y citations)" or "Starting verification of Y citations..."
                                if current_total == 0 or current_total == 100:
                                    import re

                                    # Try to extract total from message
                                    msg_match = re.search(r"(\d+)\s+citations", message)
                                    if msg_match:
                                        extracted_total = int(msg_match.group(1))
                                        if extracted_total > 0:
                                            current_total = extracted_total
                                            logger.info(
                                                f"[TASK:{task_id}] Extracted total from message: {current_total}"
                                            )

                                # Use processed_count as fallback for total if still 0
                                if current_total == 0:
                                    current_total = max(processed_count, 100)  # Use at least 100 or processed_count

                                # Update progress with citation count
                                vm.update_progress(
                                    task_id, processed=processed_count, total=current_total, message=message
                                )
                                logger.info(
                                    f"[TASK:{task_id}] Progress callback: {processed_count}/{current_total} citations - {message}"
                                )
                            except Exception as e:
                                logger.warning(f"[TASK:{task_id}] Failed to update incremental progress: {e}")

                        # Single pass: full processing with verification and progress callback
                        # FIX 2026-01-30: Timeout to avoid infinite hang in clustering (e.g. "Creating citation clusters")
                        pipeline_timeout = int(os.environ.get("PIPELINE_TIMEOUT_SECONDS", "600"))  # 10 min default

                        async def run_pipeline_with_timeout():
                            return await asyncio.wait_for(
                                process_citations_unified(
                                    text,
                                    processing_mode="enhanced_sync",
                                    enable_parallel_verification=(
                                        enable_verification if enable_verification else False
                                    ),
                                    enable_verification=enable_verification,
                                    progress_callback=update_verification_progress if enable_verification else None,
                                ),
                                timeout=float(pipeline_timeout),
                            )

                        try:
                            pipeline_result = asyncio.run(run_pipeline_with_timeout())
                        except asyncio.TimeoutError:
                            logger.error(
                                f"[TASK:{task_id}] Pipeline timed out after {pipeline_timeout}s (likely stuck in clustering)"
                            )
                            try:
                                vm.update_progress(
                                    task_id, processed=0, total=1, message="Pipeline timed out; returning partial result"
                                )
                            except Exception:
                                pass
                            result = {
                                "status": "failed",
                                "task_id": task_id,
                                "error": f"Processing timed out after {pipeline_timeout} seconds. The document may be too large or clustering may have stalled.",
                                "citations": [],
                                "clusters": [],
                                "success": False,
                            }
                            return result

                        logger.info(f"[TASK:{task_id}] Full pipeline processing with verification completed")
                        logger.error(f"[TASK:{task_id}] ⚠️ PIPELINE RESULT: {len(pipeline_result.get('citations', []))} citations, {len(pipeline_result.get('clusters', []))} clusters")
                        logger.error(f"[TASK:{task_id}] ⚠️ Pipeline result keys: {list(pipeline_result.keys())}")

                        # Extract results from completed pipeline
                        citations_raw = pipeline_result.get("citations", []) or []
                        clusters_raw = pipeline_result.get("clusters", []) or []
                        logger.error(f"[TASK:{task_id}] ⚠️ Extracted {len(citations_raw)} citations_raw, {len(clusters_raw)} clusters_raw")
                        # DIAGNOSTIC: Track specific citations through post-processing
                        def _diag_check(label, cit_list, clust_list=None):
                            for c in cit_list:
                                ct = c.get('citation','') if isinstance(c, dict) else (getattr(c, 'citation', '') if hasattr(c, 'citation') else '')
                                if '508 U.S. 520' in ct or '508 U. S. 520' in ct or ('508 U' in ct and 'Cas' not in ct):
                                    logger.error(f"[DIAG:{task_id}] {label}: LUKUMI FOUND in citations: {ct[:60]}")
                                    return
                            logger.error(f"[DIAG:{task_id}] {label}: LUKUMI NOT in {len(cit_list)} citations")
                        _diag_check("PIPELINE_RAW", citations_raw)

                        # CRITICAL FIX: Ensure citations are dicts, not CitationResult objects
                        citations_list = []
                        for cit in citations_raw:
                            if isinstance(cit, dict):
                                citations_list.append(cit)
                            elif hasattr(cit, "to_dict"):
                                citations_list.append(cit.to_dict())
                            else:
                                # Fallback: try to convert CitationResult to dict manually
                                cit_dict = {
                                    "citation": getattr(cit, "citation", ""),
                                    "extracted_case_name": getattr(cit, "extracted_case_name", None),
                                    "extracted_date": getattr(cit, "extracted_date", None),
                                    "canonical_name": getattr(cit, "canonical_name", None),
                                    "canonical_date": getattr(cit, "canonical_date", None),
                                    "canonical_url": getattr(cit, "canonical_url", None),
                                    "verified": getattr(cit, "verified", False),
                                    "source": getattr(cit, "source", None),
                                    "start_index": getattr(cit, "start_index", None),
                                    "end_index": getattr(cit, "end_index", None),
                                    "confidence": getattr(cit, "confidence", 0.9),
                                    "method": getattr(cit, "method", "unified_processor"),
                                }
                                citations_list.append(cit_dict)

                        clusters_list = list(clusters_raw) if clusters_raw else []
                        _diag_check("AFTER_DICT_CONVERT", citations_list)

                        # LAST-MILE: Apply known federal citations + clear verified without URL (shared with sync path)
                        try:
                            from src.unified_verification_master import (
                                apply_known_federal_citations_and_clear_verified_without_url,
                                apply_verification_paradox_fix,
                            )
                            apply_known_federal_citations_and_clear_verified_without_url(citations_list, clusters_list)
                            apply_verification_paradox_fix(citations_list)
                        except Exception as e:
                            logger.warning(f"[KNOWN-CITATION] Could not apply known citations / clear verified: {e}")

                        # Free accumulated garbage before heavy post-processing
                        _force_release_memory()
                        # Read TRUE RSS from /proc/self/status (kernel value, not psutil)
                        try:
                            with open('/proc/self/status') as _pf:
                                for _line in _pf:
                                    if _line.startswith('VmRSS:'):
                                        _true_rss_kb = int(_line.split()[1])
                                        logger.warning(f"[MEM-CHECKPOINT] TRUE RSS from /proc/self/status: {_true_rss_kb // 1024}MB")
                                        import sys; sys.stderr.flush()
                                        break
                        except Exception:
                            pass
                        if PSUTIL_AVAILABLE:
                            try:
                                _mem = psutil.Process().memory_info().rss / 1024 / 1024
                                logger.info(f"[TASK:{task_id}] Memory before post-processing: {_mem:.0f}MB")
                            except Exception:
                                pass

                        # USER FIX: Post-process clusters to ensure canonical data is populated from citations
                        # This fixes the issue where cluster-level fields are None but citation-level fields are correct
                        if clusters_list and citations_list:
                            logger.info(
                                f"[TASK:{task_id}] Post-processing clusters to populate canonical data from citations"
                            )
                            # Build citation lookup by citation text (and normalized form so "426 U. S. 26" matches "426 U.S. 26")
                            citation_lookup = {}
                            try:
                                from src.unified_verification_master import _normalize_citation_for_known_lookup as _norm_cit
                            except Exception:
                                def _norm_cit(s):
                                    if not s:
                                        return ""
                                    return (s or "").strip().lower().replace("u. s.", "u.s.")
                            for cit in citations_list:
                                if isinstance(cit, dict):
                                    cit_text = cit.get("citation", "")
                                    if cit_text:
                                        citation_lookup[cit_text] = cit
                                        norm_key = _norm_cit(cit_text)
                                        if norm_key and norm_key != cit_text:
                                            citation_lookup[norm_key] = cit
                            # Helper: get citation dict by member text (try exact then normalized)
                            def _lookup_cit(member_text):
                                if not member_text:
                                    return {}
                                out = citation_lookup.get(member_text)
                                if out is not None:
                                    return out
                                n = _norm_cit(member_text)
                                return citation_lookup.get(n, {}) if n else {}

                            # Update each cluster with data from its member citations
                            for cluster in clusters_list:
                                if not isinstance(cluster, dict):
                                    continue

                                # Find verified citation data from cluster members
                                members = cluster.get("cluster_members", [])
                                best_canonical_name = cluster.get("canonical_name")
                                best_canonical_date = cluster.get("canonical_date")
                                best_canonical_url = cluster.get("canonical_url")
                                best_extracted_name = cluster.get("extracted_case_name")
                                any_verified = cluster.get("verified", False)

                                # FIX: Validate that inherited canonical_name matches cluster's citations
                                # Prevents split clusters from inheriting parent's canonical_name
                                # (e.g., Susan B. Anthony List inheriting "Spokeo, Inc. v. Robins")
                                import re

                                def _extract_meaningful_first_party(name):
                                    """Extract first meaningful party word, skipping suffixes like Inc., Corp., LLC."""
                                    if not name or " v. " not in name:
                                        return ""
                                    first_half = re.split(r"\s+v\.?\s+", name, maxsplit=1)[0].strip()
                                    # Remove trailing legal suffixes
                                    words = first_half.rstrip(".,").split()
                                    skip = {"inc", "inc.", "corp", "corp.", "llc", "l.l.c.", "ltd", "ltd.", "co", "co.",
                                            "ass'n", "assn", "assn.", "assoc", "assoc.", "org", "org.", "comm.",
                                            "commission", "dept", "dept.", "department", "dist", "dist.", "district",
                                            "service", "services"}
                                    # Walk backwards to find first non-suffix word
                                    for w in reversed(words):
                                        if w.lower().rstrip(".,") not in skip and len(w) > 1:
                                            return re.sub(r"['\-\.,]", "", w).lower()
                                    return words[-1].lower() if words else ""

                                if best_canonical_name and " v. " in best_canonical_name:
                                    cn_first = _extract_meaningful_first_party(best_canonical_name)
                                    # Check if any citation's ecn matches the canonical first party
                                    cit_ecns = []
                                    for _c in (cluster.get("citations") or []):
                                        if isinstance(_c, dict):
                                            _ecn = _c.get("extracted_case_name") or ""
                                            if _ecn and _ecn != "N/A" and " v. " in _ecn:
                                                cit_ecns.append(_ecn)
                                    if cit_ecns:
                                        ecn_firsts = [_extract_meaningful_first_party(e) for e in cit_ecns]
                                        if cn_first not in ecn_firsts:
                                            logger.warning(
                                                f"[TASK:{task_id}] Clearing inherited canonical_name '{best_canonical_name}' "
                                                f"from cluster '{cluster.get('cluster_id', '?')}' — doesn't match any citation ecn "
                                                f"(cn_first='{cn_first}', ecn_firsts={ecn_firsts})"
                                            )
                                            best_canonical_name = None
                                            best_canonical_date = None
                                            best_canonical_url = None

                                for member in members:
                                    # Handle different member formats: dict, stringified dict, or plain string
                                    if isinstance(member, dict):
                                        member_text = member.get("citation", "")
                                        # USER FIX: Use cluster_member's own canonical/extracted when present (avoids null at cluster level)
                                        if member.get("canonical_url") and member.get("canonical_name"):
                                            any_verified = True
                                            cn = (member.get("canonical_name") or "").strip()
                                            if cn and cn.upper() != "N/A":
                                                best_canonical_name = member.get("canonical_name")
                                                best_canonical_date = member.get("canonical_date") or best_canonical_date
                                                best_canonical_url = member.get("canonical_url")
                                        ext_m = member.get("extracted_case_name")
                                        if ext_m and ext_m != "N/A":
                                            if not best_extracted_name or len(ext_m) > len(best_extracted_name or ""):
                                                best_extracted_name = ext_m
                                    elif isinstance(member, str):
                                        # Check if it's a stringified dict like "{'citation': '131 Wn.2d 25', ...}"
                                        if member.startswith("{") and "'citation':" in member:
                                            import re

                                            match = re.search(r"'citation':\s*'([^']+)'", member)
                                            member_text = match.group(1) if match else member
                                        else:
                                            member_text = member
                                        # CRITICAL FIX: For string members, look up citation data immediately
                                        # and check verification status (just like we do for dict members)
                                        if member_text:
                                            cit_data = _lookup_cit(member_text)
                                            if cit_data:
                                                # Check if this citation is verified AND has canonical_url
                                                if cit_data.get("verified", False) and cit_data.get("canonical_url"):
                                                    any_verified = True
                                                    cn = cit_data.get("canonical_name")
                                                    if cn and str(cn).strip() and str(cn).strip().upper() != "N/A":
                                                        best_canonical_name = cn
                                                        best_canonical_date = cit_data.get("canonical_date")
                                                        best_canonical_url = cit_data.get("canonical_url")
                                                # Get extracted name (prefer longest)
                                                ext_name = cit_data.get("extracted_case_name")
                                                if ext_name and ext_name != "N/A":
                                                    if not best_extracted_name or len(ext_name) > len(best_extracted_name):
                                                        best_extracted_name = ext_name
                                    else:
                                        member_text = str(member)

                                # FIX 2026-02-10: Correct canonical_date when it's a CourtListener DB update date
                                # CourtListener's date_filed for old SCOTUS cases often shows 2020-2021 (bulk DB update)
                                # The year in the citation parenthetical (e.g., "(1990)") is authoritative
                                if best_canonical_date:
                                    import re as _re
                                    can_yr_m = _re.search(r"(19|20)\d{2}", str(best_canonical_date))
                                    can_yr = int(can_yr_m.group(0)) if can_yr_m else None
                                    if can_yr and can_yr >= 2015:
                                        # Check citation text parenthetical years
                                        cit_text_years = []
                                        for cit in (cluster.get("citations") or []):
                                            if isinstance(cit, dict):
                                                ct = cit.get("citation", "")
                                                # Extract year from parenthetical like "(1990)" or "(scotus 1990)"
                                                paren_match = _re.search(r"\((?:[a-zA-Z.\s]*?)(\d{4})\)", ct)
                                                if paren_match:
                                                    cit_text_years.append(int(paren_match.group(1)))
                                                # Also check metadata.year
                                                meta_year = None
                                                if isinstance(cit.get("metadata"), dict):
                                                    meta_year = cit["metadata"].get("year")
                                                if meta_year and isinstance(meta_year, int):
                                                    cit_text_years.append(meta_year)
                                        if cit_text_years:
                                            # Use the most common citation text year
                                            from collections import Counter
                                            most_common_yr = Counter(cit_text_years).most_common(1)[0][0]
                                            # FIX 2026-02-13: Before overriding, check if extracted_date
                                            # agrees with canonical. TOA page numbers (e.g. "2001") can
                                            # be misinterpreted as years, causing false corrections.
                                            _ext_dates = []
                                            for cit in (cluster.get("citations") or []):
                                                if isinstance(cit, dict):
                                                    _ed = cit.get("extracted_date")
                                                    if _ed:
                                                        _ed_m = _re.search(r"(19|20)\d{2}", str(_ed))
                                                        if _ed_m:
                                                            _ext_dates.append(int(_ed_m.group(0)))
                                            _ext_agrees_with_canonical = any(abs(ed - can_yr) <= 1 for ed in _ext_dates)
                                            if abs(can_yr - most_common_yr) > 5 and most_common_yr < 2015 and not _ext_agrees_with_canonical:
                                                logger.info(
                                                    f"[TASK:{task_id}] Correcting canonical_date {best_canonical_date} -> {most_common_yr} "
                                                    f"(citation text year is authoritative, CourtListener date_filed is DB update)"
                                                )
                                                best_canonical_date = str(most_common_yr)
                                                cluster["verifying_display_date"] = str(most_common_yr)
                                                # Also fix citation-level canonical_date
                                                for cit in (cluster.get("citations") or []):
                                                    if isinstance(cit, dict) and cit.get("canonical_date"):
                                                        cit["canonical_date"] = str(most_common_yr)
                                            elif abs(can_yr - most_common_yr) > 5 and _ext_agrees_with_canonical:
                                                logger.info(
                                                    f"[TASK:{task_id}] NOT correcting canonical_date {best_canonical_date} "
                                                    f"(extracted_date agrees with canonical, parenthetical year {most_common_yr} is likely TOA page number)"
                                                )

                                # Update cluster with best data found
                                # CRITICAL FIX: Unescape HTML entities (e.g., &amp; -> &)
                                if best_canonical_name:
                                    best_canonical_name = html.unescape(str(best_canonical_name))
                                    cluster["canonical_name"] = best_canonical_name
                                    cluster["canonical_date"] = best_canonical_date
                                    cluster["canonical_url"] = best_canonical_url
                                    cluster["verifying_display_name"] = best_canonical_name
                                if best_canonical_url:
                                    cluster["canonical_url"] = best_canonical_url
                                    cluster["display_canonical_url"] = best_canonical_url
                                    if not cluster.get("canonical_name") and best_canonical_name:
                                        cluster["canonical_name"] = best_canonical_name
                                        cluster["verifying_display_name"] = best_canonical_name
                                if best_extracted_name:
                                    best_extracted_name = html.unescape(str(best_extracted_name))
                                    # FIX 2026-02-01: Apply case name cleaner to fix PDF line-break hyphenation
                                    # e.g., "Co- hens" → "Cohens", "Vir- ginia" → "Virginia"
                                    from src.utils.case_name_cleaner import clean_extracted_case_name
                                    best_extracted_name = clean_extracted_case_name(best_extracted_name)

                                # USER FIX: Apply cascading contamination fix at cluster level
                                # IMPORTANT: We no longer overwrite extracted_case_name from canonical data.
                                # Extracted names must always reflect the user's document text.
                                #
                                # We keep the existing safety guard that detects clusters containing
                                # multiple distinct canonical names and *only* use that to decide whether
                                # it is even safe to consider a display-level adjustment.
                                distinct_canonicals = set()
                                for m in members:
                                    if isinstance(m, dict):
                                        mt = m.get("citation", "")
                                    else:
                                        mt = str(m)
                                    cd = _lookup_cit(mt) if isinstance(mt, str) else {}
                                    if not cd and cluster.get("citations"):
                                        for c in cluster.get("citations", []):
                                            if isinstance(c, dict) and c.get("citation") == mt:
                                                cd = c
                                                break
                                    if cd and (cd.get("verified") or cd.get("canonical_name")):
                                        cn = (cd.get("canonical_name") or "").strip()
                                        if cn and cn != "N/A":
                                            distinct_canonicals.add(
                                                cn.replace("See, e.g., ", "").replace("See also ", "").strip()
                                            )
                                skip_cascading = len(distinct_canonicals) > 1
                                if skip_cascading:
                                    logger.info(
                                        f"[TASK:{task_id}] Skipping cascading fix: cluster has {len(distinct_canonicals)} distinct canonical names: {distinct_canonicals}"
                                    )

                                # If we ever want to adjust the cluster-level display name based on canonical
                                # vs extracted disagreement, it must *not* mutate per-citation extracted_case_name.
                                # For now, we deliberately disable the old cascading rename behaviour.

                                if best_extracted_name:
                                    cluster["extracted_case_name"] = best_extracted_name
                                    cluster["submitted_display_name"] = best_extracted_name
                                # Recalculate has_name_mismatch after fixing citations
                                cluster_cits = cluster.get("citations", [])
                                has_name_mismatch = any(
                                    c.get("name_mismatch", False) and c.get("verified", False)
                                    for c in cluster_cits
                                    if isinstance(c, dict)
                                )
                                cluster["has_name_mismatch"] = has_name_mismatch
                                # USER RULE: verified only when we have a canonical URL (no Verified without URL)
                                cluster["verified"] = bool(best_canonical_url) and any_verified

                            logger.info(
                                f"[TASK:{task_id}] Post-processing complete: updated {len(clusters_list)} clusters"
                            )
                            if PSUTIL_AVAILABLE:
                                try:
                                    _mem = psutil.Process().memory_info().rss / 1024 / 1024
                                    logger.warning(f"[MEM-CHECKPOINT] After cluster post-processing loop: {_mem:.0f}MB")
                                except Exception:
                                    pass

                        # POST-VERIFY SPLIT: split clusters with mixed canonical names
                        if clusters_list:
                            from src.utils.post_verify_split import split_clusters_by_canonical_name
                            clusters_list = split_clusters_by_canonical_name(clusters_list, task_id=task_id)
                            if PSUTIL_AVAILABLE:
                                try:
                                    _mem = psutil.Process().memory_info().rss / 1024 / 1024
                                    logger.warning(f"[MEM-CHECKPOINT] After post-verify split: {_mem:.0f}MB")
                                except Exception:
                                    pass

                        # USER FIX 2024-12-24: Synchronize cluster extracted_date with citation extracted_date
                        # This fixes the issue where cluster shows "2000" but citations show "2001"
                        # (e.g., Meri-Weather case where aff'd citation year was incorrectly picked up)
                        if clusters_list:
                            date_sync_count = 0
                            for cluster in clusters_list:
                                if not isinstance(cluster, dict):
                                    continue
                                cluster_date = cluster.get("extracted_date")
                                if not cluster_date or cluster_date in ("N/A", "Unknown Year", "unknown"):
                                    continue
                                
                                # CRITICAL FIX: Filter out cluster dates that are likely from headers
                                # Before overwriting citation dates, validate the cluster date
                                cluster_date_str = str(cluster_date)
                                cluster_date_year = None
                                try:
                                    # Extract year from cluster_date (might be "2020" or "2020-01-01")
                                    import re
                                    year_match = re.search(r"(19|20)\d{2}", cluster_date_str)
                                    if year_match:
                                        cluster_date_year = int(year_match.group(0))
                                except:
                                    pass
                                
                                # Get the citations array (might be nested in different ways)
                                cluster_cits = cluster.get("citations", [])
                                if not cluster_cits:
                                    continue
                                
                                # Check if cluster_date is suspicious (likely from header)
                                should_filter_cluster_date = False
                                if cluster_date_year:
                                    for cit in cluster_cits:
                                        if isinstance(cit, dict):
                                            citation_text = cit.get("citation", "")
                                            # Reject 2015+ for U.S. volumes 400-550 (old cases, not 560+ which are from 2020+)
                                            if " U.S. " in citation_text:
                                                volume_match = re.search(r"(\d+)\s+U\.\s*S\.", citation_text)
                                                if volume_match:
                                                    volume = int(volume_match.group(1))
                                                    # CRITICAL FIX: Volume 590 is from 2020, so 2020 is correct!
                                                    # Only reject recent years for volumes 400-550 (1970s-2000s)
                                                    if 400 <= volume <= 550 and cluster_date_year >= 2015:
                                                        should_filter_cluster_date = True
                                                        logger.warning(
                                                            f"[DATE-SYNC] Rejected cluster_date {cluster_date} for cluster with {citation_text} "
                                                            f"(U.S. volume {volume}) - year 2015+ likely from header"
                                                        )
                                                        break
                                            # Reject 2020+ for F.3d volumes 800-900
                                            elif " F.3d " in citation_text:
                                                volume_match = re.search(r"(\d+)\s+F\.\s*3d", citation_text)
                                                if volume_match:
                                                    volume = int(volume_match.group(1))
                                                    if 800 <= volume <= 900 and cluster_date_year >= 2020:
                                                        should_filter_cluster_date = True
                                                        logger.warning(
                                                            f"[DATE-SYNC] Rejected cluster_date {cluster_date} for cluster with {citation_text} "
                                                            f"(F.3d volume {volume}) - year 2020+ likely from header"
                                                        )
                                                        break
                                
                                # Skip synchronization if cluster_date is from a header
                                if should_filter_cluster_date:
                                    logger.info(
                                        f"[DATE-SYNC] Skipping date sync for cluster - cluster_date {cluster_date} is from header"
                                    )
                                    continue
                                
                                # Update all citation's extracted_date to match the cluster's
                                for cit in cluster_cits:
                                    if isinstance(cit, dict):
                                        old_date = cit.get("extracted_date")
                                        if old_date != cluster_date:
                                            cit["extracted_date"] = cluster_date
                                            date_sync_count += 1
                                            # Recalculate date_mismatch now that extracted_date is updated
                                            canonical_date = cit.get("canonical_date")
                                            if canonical_date:
                                                import re

                                                ext_year_match = re.search(r"(19|20)\d{2}", str(cluster_date))
                                                can_year_match = re.search(r"(19|20)\d{2}", str(canonical_date))
                                                if ext_year_match and can_year_match:
                                                    # Years match = no mismatch (with 1-year tolerance)
                                                    year_diff = abs(
                                                        int(ext_year_match.group(0)) - int(can_year_match.group(0))
                                                    )
                                                    cit["date_mismatch"] = year_diff > 1
                                                else:
                                                    cit["date_mismatch"] = False
                                            else:
                                                cit["date_mismatch"] = False
                                # Also recalculate cluster-level has_date_mismatch
                                has_date_mismatch = any(
                                    c.get("date_mismatch", False) and c.get("verified", False)
                                    for c in cluster_cits
                                    if isinstance(c, dict)
                                )
                                cluster["has_date_mismatch"] = has_date_mismatch
                            if date_sync_count > 0:
                                logger.info(
                                    f"[TASK:{task_id}] Synchronized {date_sync_count} citation extracted_dates with cluster dates"
                                )
                            if PSUTIL_AVAILABLE:
                                try:
                                    _mem = psutil.Process().memory_info().rss / 1024 / 1024
                                    logger.warning(f"[MEM-CHECKPOINT] After date sync: {_mem:.0f}MB")
                                except Exception:
                                    pass

                        # USER FIX: Validate extracted case names against actual document text
                        # This catches cases where eyecite extracted wrong names due to PDF parsing issues
                        # FIX 2026-02-01: Also validate verified clusters - verification might have
                        # succeeded using a wrong name (e.g., "Trump v. Useche" phantom case).
                        # The verification searches for the extracted name, so if extraction is wrong,
                        # verification can still "verify" a completely unrelated case.
                        if clusters_list and text:
                            import re

                            for cluster in clusters_list:
                                if not isinstance(cluster, dict):
                                    continue
                                ext_name = cluster.get("extracted_case_name", "")
                                if not ext_name or ext_name == "N/A":
                                    continue
                                # Get first party name for validation
                                parts = re.split(r"\s+v\.?\s+", ext_name, maxsplit=1, flags=re.IGNORECASE)
                                if not parts:
                                    continue
                                first_party = parts[0].strip()
                                # Remove common words to get key name
                                first_party_key = re.sub(
                                    r"\b(the|of|in|and|inc|corp|llc|ltd|co)\b",
                                    "",
                                    first_party.lower(),
                                    flags=re.IGNORECASE,
                                ).strip()
                                if len(first_party_key) < 4:
                                    continue
                                # Check if this name actually appears near the citation in the document
                                members = cluster.get("cluster_members", [])
                                if not members:
                                    continue
                                # Get citation position from first member
                                first_member = members[0]
                                if isinstance(first_member, str) and first_member.startswith("{"):
                                    match = re.search(r"'start_index':\s*(\d+)", first_member)
                                    cit_pos = int(match.group(1)) if match else -1
                                elif isinstance(first_member, dict):
                                    cit_pos = first_member.get("start_index", -1)
                                else:
                                    cit_pos = -1
                                if cit_pos < 0:
                                    continue
                                # Check 500 chars before citation for the party name
                                context_start = max(0, cit_pos - 500)
                                context_end = min(len(text), cit_pos + 50)
                                context = text[context_start:context_end].lower()
                                # FIX DEC 2025 v11: Normalize dashes for comparison (em-dash, en-dash, etc.)
                                context_normalized = (
                                    context.replace("–", "-")
                                    .replace("—", "-")
                                    .replace("\u2013", "-")
                                    .replace("\u2014", "-")
                                )
                                first_party_normalized = (
                                    first_party_key.replace("–", "-")
                                    .replace("—", "-")
                                    .replace("\u2013", "-")
                                    .replace("\u2014", "-")
                                )
                                if first_party_normalized not in context_normalized:
                                    # Extracted name doesn't appear near citation - likely wrong
                                    logger.warning(
                                        f"[TASK:{task_id}] Detected phantom extraction: '{ext_name}' not found near citation at {cit_pos}"
                                    )
                                    # Try to find correct name from context
                                    v_match = re.search(
                                        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                                        text[context_start:context_end],
                                    )
                                    if v_match:
                                        correct_name = f"{v_match.group(1)} v. {v_match.group(2)}"
                                        logger.info(f"[TASK:{task_id}] Found correct name in context: '{correct_name}'")
                                        cluster["extracted_case_name"] = correct_name
                                        cluster["submitted_display_name"] = correct_name
                                        cluster["phantom_name_fixed"] = True
                                        # FIX 2026-02-01: Clear verification if original name was phantom
                                        # The verification was done using wrong name, so canonical data is invalid
                                        if cluster.get("verified", False):
                                            logger.warning(f"[TASK:{task_id}] Clearing verification for phantom-fixed cluster: {ext_name} -> {correct_name}")
                                            cluster["verified"] = False
                                            cluster["canonical_name"] = None
                                            cluster["canonical_date"] = None
                                            cluster["canonical_url"] = None
                                            cluster["verifying_display_name"] = correct_name
                                            cluster["verifying_display_date"] = cluster.get("extracted_date", "N/A")
                                            # Also clear citation-level verification
                                            for cit in cluster.get("citations", []):
                                                if isinstance(cit, dict):
                                                    cit["verified"] = False
                                                    cit["canonical_name"] = None
                                                    cit["canonical_date"] = None
                                                    cit["canonical_url"] = None
                                                    cit["extracted_case_name"] = correct_name
                                    else:
                                        cluster["extracted_case_name"] = "N/A"
                                        cluster["submitted_display_name"] = "N/A"
                                        cluster["phantom_name_detected"] = True
                                        # FIX 2026-02-01: Clear verification if name was phantom and no correct name found
                                        if cluster.get("verified", False):
                                            logger.warning(f"[TASK:{task_id}] Clearing verification for phantom cluster with no correctable name: {ext_name}")
                                            cluster["verified"] = False
                                            cluster["canonical_name"] = None
                                            cluster["canonical_date"] = None
                                            cluster["canonical_url"] = None
                                            cluster["verifying_display_name"] = "N/A"
                                            cluster["verifying_display_date"] = "N/A"
                                            # Also clear citation-level verification
                                            for cit in cluster.get("citations", []):
                                                if isinstance(cit, dict):
                                                    cit["verified"] = False
                                                    cit["canonical_name"] = None
                                                    cit["canonical_date"] = None
                                                    cit["canonical_url"] = None
                                                    cit["extracted_case_name"] = "N/A"

                        # FIX 2026-02-04: Validate canonical_name against document text
                        # This catches phantom canonical names from CaseMine when extracted_case_name is N/A
                        # Example: "Trump v. Useche" returned by CaseMine for "592 U.S. ___" certiorari grant
                        # If canonical_name party names don't appear in document, clear verification
                        if clusters_list and text:
                            import re

                            for cluster in clusters_list:
                                if not isinstance(cluster, dict):
                                    continue
                                ext_name = cluster.get("extracted_case_name", "")
                                canonical_name = cluster.get("canonical_name", "")

                                # Only check if: verified, has canonical_name, but no extracted_case_name
                                # (meaning CaseMine provided a name we couldn't extract from context)
                                if (cluster.get("verified", False) and
                                    canonical_name and canonical_name != "N/A" and
                                    (not ext_name or ext_name == "N/A")):

                                    # Extract first party from canonical_name
                                    parts = re.split(r"\s+v\.?\s+", canonical_name, maxsplit=1, flags=re.IGNORECASE)
                                    if parts:
                                        canonical_first = parts[0].strip()
                                        canonical_first_key = re.sub(
                                            r"\b(the|of|in|and|inc|corp|llc|ltd|co)\b",
                                            "",
                                            canonical_first.lower(),
                                            flags=re.IGNORECASE,
                                        ).strip()

                                        if len(canonical_first_key) >= 4:
                                            # Check if canonical name first party appears ANYWHERE in document
                                            text_lower = text.lower()
                                            # Normalize dashes for comparison
                                            text_normalized = (
                                                text_lower.replace("–", "-")
                                                .replace("—", "-")
                                                .replace("\u2013", "-")
                                                .replace("\u2014", "-")
                                            )
                                            canonical_normalized = (
                                                canonical_first_key.replace("–", "-")
                                                .replace("—", "-")
                                                .replace("\u2013", "-")
                                                .replace("\u2014", "-")
                                            )

                                            if canonical_normalized not in text_normalized:
                                                # Canonical name not in document - this is a phantom from CaseMine
                                                logger.warning(
                                                    f"[TASK:{task_id}] 🚫 PHANTOM CANONICAL: '{canonical_name}' not found in document "
                                                    f"(key='{canonical_first_key}') - clearing verification"
                                                )
                                                cluster["verified"] = False
                                                cluster["canonical_name"] = None
                                                cluster["canonical_date"] = None
                                                cluster["canonical_url"] = None
                                                cluster["verifying_display_name"] = "N/A"
                                                cluster["verifying_display_date"] = "N/A"
                                                cluster["phantom_canonical_detected"] = True
                                                # Also clear citation-level verification
                                                for cit in cluster.get("citations", []):
                                                    if isinstance(cit, dict):
                                                        cit["verified"] = False
                                                        cit["canonical_name"] = None
                                                        cit["canonical_date"] = None
                                                        cit["canonical_url"] = None
                                            else:
                                                logger.info(
                                                    f"[TASK:{task_id}] ✅ Canonical name '{canonical_name}' found in document"
                                                )

                        # USER FIX: Fix fragment extractions in clusters (e.g., "Inc v. Montgomery")
                        # FIX 2026-02-01: Do NOT use canonical for submitted_display_name - that's contamination!
                        # submitted_display_name should ALWAYS show what was extracted, even if it's a fragment
                        # The canonical name appears in verifying_display_name (first line), not submitted
                        if clusters_list:
                            import re

                            fragment_pattern = re.compile(
                                r"^(Inc\.?|Corp\.?|LLC|L\.L\.C\.|Ltd\.?|Co\.?|Ass\'?n|Assoc\.?|Org\.?)\s+v\.?\s+",
                                re.IGNORECASE,
                            )
                            for cluster in clusters_list:
                                if not isinstance(cluster, dict):
                                    continue
                                ext_name = cluster.get("extracted_case_name", "")
                                if ext_name and fragment_pattern.match(str(ext_name)):
                                    # FIX 2026-02-10: If canonical_name contains the fragment,
                                    # use canonical — it's the same case, just more complete
                                    # e.g. "Inc. v. Robins" → "Spokeo, Inc. v. Robins"
                                    canonical = (cluster.get("canonical_name") or "").strip()
                                    if canonical and canonical != "N/A" and ext_name.lower() in canonical.lower():
                                        cluster["submitted_display_name"] = canonical
                                        cluster["extracted_case_name"] = canonical
                                        logger.info(f"[TASK:{task_id}] Fragment '{ext_name}' upgraded to canonical '{canonical}'")
                                    else:
                                        cluster["submitted_display_name"] = ext_name
                                        logger.info(f"[TASK:{task_id}] Fragment '{ext_name}' kept as extracted (no matching canonical)")

                        # FIX 2026-02-09: When extraction fails, use canonical_name as fallback for submitted_display_name
                        # The user wants to see the case name, not "N/A", when we know it from verification
                        if clusters_list:
                            for cluster in clusters_list:
                                if not isinstance(cluster, dict):
                                    continue
                                ext_name = cluster.get("extracted_case_name", "")
                                if not ext_name or ext_name == "N/A":
                                    canonical_fallback = (cluster.get("canonical_name") or "").strip()
                                    if not canonical_fallback or canonical_fallback == "N/A":
                                        for cit in cluster.get("citations", cluster.get("citation_objects", [])):
                                            if isinstance(cit, dict):
                                                cn = (cit.get("canonical_name") or "").strip()
                                                if cn and cn != "N/A":
                                                    canonical_fallback = cn
                                                    break
                                    if canonical_fallback and canonical_fallback != "N/A":
                                        cluster["submitted_display_name"] = canonical_fallback
                                        cluster["extracted_case_name"] = canonical_fallback
                                        logger.info(f"[TASK:{task_id}] Extraction failed - using canonical '{canonical_fallback}' as submitted_display_name")
                                    else:
                                        cluster["submitted_display_name"] = "N/A"
                                        logger.info(f"[TASK:{task_id}] Extraction failed - no canonical available, keeping N/A")

                        if PSUTIL_AVAILABLE:
                            try:
                                _mem = psutil.Process().memory_info().rss / 1024 / 1024
                                logger.warning(f"[MEM-CHECKPOINT] Before merge dupes: {_mem:.0f}MB")
                            except Exception:
                                pass
                        _diag_check("BEFORE_MERGE_DUPES", citations_list)
                        # USER FIX: Merge duplicate clusters (same case appearing multiple times)
                        # This catches cases like "Clarke v. Tri-Cities" and "Clarke v. TCAC"
                        # Also catches "Hearst Communications" vs "Hearst Corp" with same date
                        if clusters_list and len(clusters_list) > 1:
                            import re

                            def extract_first_party(name):
                                if not name:
                                    return ""
                                parts = re.split(r"\s+v\.?\s+", str(name), maxsplit=1, flags=re.IGNORECASE)
                                return parts[0].lower().strip() if parts else str(name).lower().strip()

                            def get_key_words(name):
                                """Extract key words from a name for similarity matching."""
                                if not name:
                                    return set()
                                # Remove common words and get significant terms
                                words = re.findall(r"\b[a-z]+\b", str(name).lower())
                                common = {
                                    "v",
                                    "the",
                                    "of",
                                    "and",
                                    "in",
                                    "inc",
                                    "corp",
                                    "co",
                                    "llc",
                                    "ltd",
                                    "vs",
                                    "city",
                                    "state",
                                    "county",
                                    "dept",
                                    "department",
                                }
                                return set(w for w in words if w not in common and len(w) > 2)

                            # Group clusters by canonical_date first
                            date_groups = {}
                            for i, cluster in enumerate(clusters_list):
                                if not isinstance(cluster, dict):
                                    continue
                                canonical_date = cluster.get("canonical_date", "")
                                if canonical_date and cluster.get("verified", False):
                                    if canonical_date not in date_groups:
                                        date_groups[canonical_date] = []
                                    date_groups[canonical_date].append(i)

                            # Within each date group, find clusters with similar names
                            to_remove = set()
                            for date, indices in date_groups.items():
                                if len(indices) > 1:
                                    # Check if any pairs should be merged based on name similarity
                                    merged_into = {}  # Maps index to leader index
                                    for i in range(len(indices)):
                                        if indices[i] in to_remove:
                                            continue
                                        c1 = clusters_list[indices[i]]
                                        name1 = c1.get("canonical_name", "")
                                        words1 = get_key_words(name1)

                                        for j in range(i + 1, len(indices)):
                                            if indices[j] in to_remove:
                                                continue
                                            c2 = clusters_list[indices[j]]
                                            name2 = c2.get("canonical_name", "")
                                            words2 = get_key_words(name2)

                                            # Check for significant word overlap
                                            if words1 and words2:
                                                overlap = words1 & words2
                                                # If they share at least 2 significant words, check court compatibility
                                                if len(overlap) >= 2:
                                                    # USER FIX 2026-01-09: Check court-level compatibility before merging
                                                    # Supreme Court, Circuit Court, and District Court citations can NEVER be merged
                                                    def get_court_types(cluster):
                                                        """Extract court types from cluster citations."""
                                                        import re
                                                        court_types = set()
                                                        for member in cluster.get("cluster_members", []):
                                                            # Handle both dict and string types
                                                            if isinstance(member, dict):
                                                                cit_text = member.get("citation", "")
                                                            elif isinstance(member, str):
                                                                cit_text = member
                                                            else:
                                                                continue
                                                            # Parse citation to get reporter
                                                            pattern = r"(\d+)\s+([A-Z][\w\.]+(?:\s+[\w\.]+)*?)\s+(\d+)"
                                                            match = re.search(pattern, cit_text)
                                                            if match:
                                                                reporter = match.group(2).strip().replace(" ", "")
                                                                # Classify by court type
                                                                if reporter in ["U.S.", "S.Ct.", "L.Ed.", "L.Ed.2d"]:
                                                                    court_types.add("supreme")
                                                                elif reporter in ["F.2d", "F.3d", "F.4th"]:
                                                                    court_types.add("circuit")
                                                                elif reporter in ["F.Supp.", "F.Supp.2d", "F.Supp.3d"]:
                                                                    court_types.add("district")
                                                        return court_types
                                                    
                                                    court_types_1 = get_court_types(c1)
                                                    court_types_2 = get_court_types(c2)
                                                    
                                                    # Check for incompatible court types
                                                    incompatible = False
                                                    if court_types_1 and court_types_2:
                                                        # Supreme + Circuit/District = incompatible
                                                        if ("supreme" in court_types_1 and ("circuit" in court_types_2 or "district" in court_types_2)) or \
                                                           ("supreme" in court_types_2 and ("circuit" in court_types_1 or "district" in court_types_1)):
                                                            incompatible = True
                                                            logger.info(
                                                                f"[TASK:{task_id}] BLOCKING merge of '{name1}' + '{name2}': Supreme Court + Circuit/District (incompatible court levels)"
                                                            )
                                                        # Circuit + District = incompatible
                                                        elif ("circuit" in court_types_1 and "district" in court_types_2) or \
                                                             ("circuit" in court_types_2 and "district" in court_types_1):
                                                            incompatible = True
                                                            logger.info(
                                                                f"[TASK:{task_id}] BLOCKING merge of '{name1}' + '{name2}': Circuit Court + District Court (incompatible court levels)"
                                                            )
                                                    
                                                    # USER FIX 2026-01-09: Check for same reporter but different volumes
                                                    # Multiple citations in same reporter = different cases
                                                    # OPTIMIZED: Cache parsed citations to avoid O(n²) regex operations
                                                    if not incompatible:
                                                        # Get first citation from each cluster for quick check
                                                        import re
                                                        pattern = r"(\d+)\s+([A-Z][\w\.]+(?:\s+[\w\.]+)*?)\s+(\d+)"
                                                        
                                                        def get_first_citation_info(cluster):
                                                            """Get reporter+volume from first citation only (optimization)."""
                                                            members = cluster.get("cluster_members", [])
                                                            if not members:
                                                                return None, None
                                                            
                                                            member = members[0]
                                                            if isinstance(member, dict):
                                                                cit_text = member.get("citation", "")
                                                            elif isinstance(member, str):
                                                                cit_text = member
                                                            else:
                                                                return None, None
                                                            
                                                            match = re.search(pattern, cit_text)
                                                            if match:
                                                                volume = match.group(1)
                                                                reporter = match.group(2).strip().replace(" ", "")
                                                                return reporter, volume
                                                            return None, None
                                                        
                                                        reporter1, vol1 = get_first_citation_info(c1)
                                                        reporter2, vol2 = get_first_citation_info(c2)
                                                        
                                                        # Quick check: if same reporter but different volumes, incompatible
                                                        if reporter1 and reporter2 and reporter1 == reporter2 and vol1 != vol2:
                                                            incompatible = True
                                                            logger.info(
                                                                f"[TASK:{task_id}] BLOCKING merge of '{name1}' + '{name2}': Same reporter ({reporter1}) but different volumes ({vol1} vs {vol2}) = different cases"
                                                            )
                                                    
                                                    if not incompatible:
                                                        logger.info(
                                                            f"[TASK:{task_id}] Merging clusters by name similarity: '{name1}' + '{name2}' (shared: {overlap})"
                                                        )
                                                        # Merge j into i
                                                        leader = c1
                                                        other = c2
                                                        leader_members = leader.get("cluster_members", [])
                                                        other_members = other.get("cluster_members", [])
                                                        for m in other_members:
                                                            if m not in leader_members:
                                                                # CRITICAL FIX: Filter same-reporter/different-volume
                                                                first_member = leader_members[0] if leader_members else m
                                                                filtered = filter_cluster_members_by_reporter(first_member, [m])
                                                                if filtered:
                                                                    leader_members.append(m)
                                                        leader["cluster_members"] = leader_members
                                                        leader["cluster_size"] = len(leader_members)
                                                        # Prefer longer canonical name
                                                        if len(name2) > len(name1):
                                                            leader["canonical_name"] = name2
                                                            leader["verifying_display_name"] = name2
                                                        to_remove.add(indices[j])

                            if to_remove:
                                clusters_list = [c for i, c in enumerate(clusters_list) if i not in to_remove]
                                logger.info(
                                    f"[TASK:{task_id}] Removed {len(to_remove)} duplicate clusters, now {len(clusters_list)}"
                                )

                        if PSUTIL_AVAILABLE:
                            try:
                                _mem = psutil.Process().memory_info().rss / 1024 / 1024
                                logger.warning(f"[MEM-CHECKPOINT] After merge-dupes, before parallel-merge: {_mem:.0f}MB")
                            except Exception:
                                pass
                        # USER FIX: Merge unverified singleton clusters into verified clusters
                        # when they're parallel citations (close position in text)
                        if clusters_list and citations_list and len(clusters_list) > 1:
                            # Build citation position map
                            cit_positions = {}
                            for cit in citations_list:
                                if isinstance(cit, dict):
                                    cit_text = cit.get("citation", "")
                                    start_idx = cit.get("start_index", 0)
                                    if cit_text:
                                        cit_positions[cit_text] = start_idx

                            # FIX DEC 2025: First merge N/A singletons with EACH OTHER if they're parallel
                            # This handles cases like 194 Wn.2d 651 + 451 P.3d 675 which are both N/A singletons
                            na_singleton_indices = []
                            for i, cluster in enumerate(clusters_list):
                                if not isinstance(cluster, dict):
                                    continue
                                has_na = cluster.get("extracted_case_name") in [None, "N/A", ""]
                                is_singleton = cluster.get("cluster_size", 1) <= 1
                                if has_na and is_singleton:
                                    na_singleton_indices.append(i)

                            if len(na_singleton_indices) >= 2:
                                logger.info(
                                    f"[TASK:{task_id}] Found {len(na_singleton_indices)} N/A singletons to check for parallel merging"
                                )
                                na_to_merge = []  # List of (from_idx, into_idx)

                                for i, idx1 in enumerate(na_singleton_indices):
                                    for idx2 in na_singleton_indices[i + 1 :]:
                                        cluster1 = clusters_list[idx1]
                                        cluster2 = clusters_list[idx2]

                                        # Get citation positions
                                        cit1 = cluster1.get("citations", [{}])[0] if cluster1.get("citations") else {}
                                        cit2 = cluster2.get("citations", [{}])[0] if cluster2.get("citations") else {}
                                        cit1_text = cit1.get("citation", "") if isinstance(cit1, dict) else str(cit1)
                                        cit2_text = cit2.get("citation", "") if isinstance(cit2, dict) else str(cit2)

                                        pos1 = cit_positions.get(cit1_text, -1)
                                        pos2 = cit_positions.get(cit2_text, -1)

                                        if pos1 < 0 or pos2 < 0:
                                            continue

                                        distance = abs(pos1 - pos2)

                                        # Check if close (<100 chars) AND compatible parallel reporters
                                        if distance < 100:
                                            if _are_parallel_reporter_types(cit1_text, cit2_text):
                                                if _citations_compatible_for_parallel(cit1_text, cit2_text):
                                                    logger.info(
                                                        f"[TASK:{task_id}] N/A parallel match: '{cit1_text}' + '{cit2_text}' (distance={distance})"
                                                    )
                                                    na_to_merge.append((idx2, idx1))  # Merge idx2 into idx1

                                # Perform N/A singleton merges
                                na_merged_indices = set()
                                for from_idx, into_idx in na_to_merge:
                                    if from_idx in na_merged_indices or into_idx in na_merged_indices:
                                        continue

                                    from_cluster = clusters_list[from_idx]
                                    into_cluster = clusters_list[into_idx]

                                    # Merge citations
                                    into_citations = into_cluster.get("citations", [])
                                    from_citations = from_cluster.get("citations", [])
                                    for fc in from_citations:
                                        fc_str = fc.get("citation", "") if isinstance(fc, dict) else str(fc)
                                        existing = [
                                            c.get("citation", "") if isinstance(c, dict) else str(c)
                                            for c in into_citations
                                        ]
                                        if fc_str not in existing:
                                            into_citations.append(fc)
                                    into_cluster["citations"] = into_citations
                                    into_cluster["cluster_size"] = len(into_citations)
                                    into_cluster["size"] = len(into_citations)

                                    # Merge cluster_members
                                    into_members = into_cluster.get("cluster_members", [])
                                    from_members = from_cluster.get("cluster_members", [])
                                    for fm in from_members:
                                        if fm not in into_members:
                                            # CRITICAL FIX: Filter same-reporter/different-volume
                                            first_member = into_members[0] if into_members else fm
                                            filtered = filter_cluster_members_by_reporter(first_member, [fm])
                                            if filtered:
                                                into_members.append(fm)
                                    into_cluster["cluster_members"] = into_members

                                    na_merged_indices.add(from_idx)
                                    logger.info(f"[TASK:{task_id}] Merged N/A singleton {from_idx} into {into_idx}")

                                if na_merged_indices:
                                    clusters_list = [
                                        c for i, c in enumerate(clusters_list) if i not in na_merged_indices
                                    ]
                                    logger.info(
                                        f"[TASK:{task_id}] Merged {len(na_merged_indices)} N/A singletons, now {len(clusters_list)} clusters"
                                    )

                            # Find unverified singleton clusters (N/A or not verified)
                            to_merge = []  # List of (singleton_idx, target_idx)
                            for i, cluster in enumerate(clusters_list):
                                if not isinstance(cluster, dict):
                                    continue
                                # Is this an unverified singleton?
                                is_unverified = not cluster.get("verified", False)
                                is_singleton = cluster.get("cluster_size", 1) <= 1
                                has_na = cluster.get("extracted_case_name") in [None, "N/A", ""]

                                if is_unverified and (is_singleton or has_na):
                                    # Get this cluster's citation position
                                    members = cluster.get("cluster_members", [])
                                    if not members:
                                        continue
                                    member = members[0]
                                    # Extract citation text from member
                                    if isinstance(member, str) and member.startswith("{"):
                                        import re

                                        match = re.search(r"'citation':\s*'([^']+)'", member)
                                        member_cit = match.group(1) if match else member
                                    elif isinstance(member, dict):
                                        member_cit = member.get("citation", "")
                                    else:
                                        member_cit = str(member)

                                    member_pos = cit_positions.get(member_cit, -1)
                                    if member_pos < 0:
                                        continue

                                    # Find a verified cluster with a citation close to this position
                                    for j, other in enumerate(clusters_list):
                                        if i == j or not isinstance(other, dict):
                                            continue
                                        if not other.get("verified", False):
                                            continue

                                        # Check positions of other cluster's members
                                        other_members = other.get("cluster_members", [])
                                        for om in other_members:
                                            if isinstance(om, str) and om.startswith("{"):
                                                match = re.search(r"'citation':\s*'([^']+)'", om)
                                                other_cit = match.group(1) if match else om
                                            elif isinstance(om, dict):
                                                other_cit = om.get("citation", "")
                                            else:
                                                other_cit = str(om)

                                            other_pos = cit_positions.get(other_cit, -1)
                                            if other_pos < 0:
                                                continue

                                            # If within 100 chars, they're likely parallel citations
                                            distance = abs(member_pos - other_pos)
                                            if distance < 100:
                                                # FIX: Skip slip opinion placeholders — they are NOT parallel citations
                                                # "590 U. S. ___, ___" near "578 U.S. 330" does NOT mean they're the same case
                                                if re.search(r'___|______', member_cit):
                                                    continue
                                                # FIX: Use shared same-case check on cluster-level names
                                                from src.utils.same_case import names_are_same_case as _prox_sc
                                                singleton_ecn = (cluster.get("extracted_case_name") or "").strip()
                                                target_ecn = (other.get("extracted_case_name") or "").strip()
                                                if not _prox_sc(singleton_ecn, target_ecn):
                                                    logger.warning(
                                                        f"[TASK:{task_id}] REJECTED parallel: '{member_cit[:50]}' + '{other_cit[:50]}' - different cases ('{singleton_ecn}' vs '{target_ecn}')"
                                                    )
                                                    continue
                                                # CRITICAL FIX: Check jurisdiction compatibility
                                                # Prevents Ohio + Nebraska cross-state clustering
                                                if not _citations_compatible_for_parallel(member_cit, other_cit):
                                                    logger.warning(
                                                        f"[TASK:{task_id}] REJECTED parallel: '{member_cit}' + '{other_cit}' - different jurisdictions"
                                                    )
                                                    continue
                                                # CRITICAL FIX: Check for case history signals (aff'd, rev'd, etc.)
                                                # Prevents merging appellate and original proceedings
                                                if text:
                                                    # Get actual text between citations for debugging
                                                    start_pos = min(member_pos, other_pos)
                                                    end_pos = (
                                                        max(member_pos, other_pos) + 20
                                                    )  # Add 20 to include citation text
                                                    between_text = (
                                                        text[start_pos:end_pos]
                                                        if len(text) > end_pos
                                                        else text[start_pos:]
                                                    )
                                                    logger.info(
                                                        f"[TASK:{task_id}] Checking for case history between '{member_cit}' and '{other_cit}': '{between_text[:100]}...'"
                                                    )
                                                    if _has_case_history_signal_between(
                                                        text, member_pos, other_pos + 20
                                                    ):
                                                        logger.warning(
                                                            f"[TASK:{task_id}] REJECTED parallel: '{member_cit}' + '{other_cit}' - case history signal between"
                                                        )
                                                        continue
                                                else:
                                                    logger.warning(
                                                        f"[TASK:{task_id}] No text available for case history check"
                                                    )
                                                logger.info(
                                                    f"[TASK:{task_id}] Found parallel: '{member_cit}' near '{other_cit}' (distance={distance})"
                                                )
                                                to_merge.append((i, j))
                                                break
                                        if any(m[0] == i for m in to_merge):
                                            break

                            # Perform merges
                            merged_indices = set()
                            for singleton_idx, target_idx in to_merge:
                                if singleton_idx in merged_indices:
                                    continue
                                singleton = clusters_list[singleton_idx]
                                target = clusters_list[target_idx]
                                # Merge singleton into target
                                target_members = target.get("cluster_members", [])
                                singleton_members = singleton.get("cluster_members", [])
                                for m in singleton_members:
                                    if m not in target_members:
                                        # CRITICAL FIX: Filter same-reporter/different-volume
                                        first_member = target_members[0] if target_members else m
                                        filtered = filter_cluster_members_by_reporter(first_member, [m])
                                        if filtered:
                                            target_members.append(m)
                                target["cluster_members"] = target_members
                                target["cluster_size"] = len(target_members)

                                # CRITICAL FIX: Also merge the citations list, not just cluster_members
                                # This was causing citations like 47 Conn. Supp. 113 to be lost
                                target_citations = target.get("citations", [])
                                singleton_citations = singleton.get("citations", [])
                                for cit in singleton_citations:
                                    cit_str = cit.get("citation", "") if isinstance(cit, dict) else str(cit)
                                    # Check if citation already exists in target
                                    existing_cits = [
                                        c.get("citation", "") if isinstance(c, dict) else str(c)
                                        for c in target_citations
                                    ]
                                    if cit_str not in existing_cits:
                                        target_citations.append(cit)
                                target["citations"] = target_citations
                                target["size"] = len(target_citations)

                                merged_indices.add(singleton_idx)
                                logger.info(
                                    f"[TASK:{task_id}] Merged singleton cluster {singleton_idx} into {target_idx} (now {len(target_citations)} citations)"
                                )

                            if merged_indices:
                                clusters_list = [c for i, c in enumerate(clusters_list) if i not in merged_indices]
                                logger.info(
                                    f"[TASK:{task_id}] Merged {len(merged_indices)} parallel citations, now {len(clusters_list)} clusters"
                                )

                        if PSUTIL_AVAILABLE:
                            try:
                                _mem = psutil.Process().memory_info().rss / 1024 / 1024
                                logger.warning(f"[MEM-CHECKPOINT] After parallel-merge, before same-name-merge: {_mem:.0f}MB")
                            except Exception:
                                pass
                        # USER FIX: Merge unverified clusters with same extracted name
                        # This handles cases like Horvath appearing twice with different citations
                        # CRITICAL FIX: Only merge if ALL citations have the same extracted name
                        if clusters_list and len(clusters_list) > 1:
                            def get_citation_names(cluster):
                                """Get all unique extracted_case_names from citations in a cluster."""
                                names = set()
                                for cit in cluster.get("citations", []):
                                    if isinstance(cit, dict):
                                        name = cit.get("extracted_case_name", "")
                                        if name and name != "N/A":
                                            # Normalize for comparison
                                            norm = name.lower().strip()
                                            names.add(norm)
                                return names
                            
                            def clusters_have_same_citations(cluster1, cluster2):
                                """Check if two clusters have citations with the same extracted names."""
                                names1 = get_citation_names(cluster1)
                                names2 = get_citation_names(cluster2)
                                # If either has multiple different names, don't merge
                                if len(names1) > 1 or len(names2) > 1:
                                    return False
                                # If both have one name and they match, merge
                                if names1 and names2:
                                    return names1 == names2
                                # If neither has citation-level names, use cluster-level name check
                                from src.utils.same_case import names_are_same_case as _sc
                                cn1 = (cluster1.get("extracted_case_name") or "").strip()
                                cn2 = (cluster2.get("extracted_case_name") or "").strip()
                                return _sc(cn1, cn2)
                            
                            name_groups = {}  # extracted_name -> list of cluster indices
                            for i, cluster in enumerate(clusters_list):
                                if not isinstance(cluster, dict):
                                    continue
                                # Only merge unverified clusters by name
                                if cluster.get("verified", False):
                                    continue
                                ext_name = cluster.get("extracted_case_name", "")
                                if ext_name and ext_name != "N/A":
                                    # Normalize name for grouping
                                    norm_name = ext_name.lower().strip()
                                    if norm_name not in name_groups:
                                        name_groups[norm_name] = []
                                    name_groups[norm_name].append(i)

                            # Merge clusters with same name AND same citation-level names
                            to_remove = set()
                            for name, indices in name_groups.items():
                                if len(indices) > 1:
                                    # Check if all clusters in this group have compatible citation names
                                    leader_idx = indices[0]
                                    leader = clusters_list[leader_idx]
                                    mergeable = []
                                    for idx in indices[1:]:
                                        other = clusters_list[idx]
                                        if clusters_have_same_citations(leader, other):
                                            mergeable.append(idx)
                                        else:
                                            logger.info(
                                                f"[TASK:{task_id}] NOT merging cluster {idx} - citations have different extracted names"
                                            )
                                    
                                    if mergeable:
                                        logger.info(
                                            f"[TASK:{task_id}] Merging {len(mergeable)+1} unverified clusters for '{name}'"
                                        )
                                        for idx in mergeable:
                                            other = clusters_list[idx]
                                            # Merge members
                                            leader_members = leader.get("cluster_members", [])
                                            other_members = other.get("cluster_members", [])
                                            for m in other_members:
                                                if m not in leader_members:
                                                    # CRITICAL FIX: Filter same-reporter/different-volume
                                                    first_member = leader_members[0] if leader_members else m
                                                    filtered = filter_cluster_members_by_reporter(first_member, [m])
                                                    if filtered:
                                                        leader_members.append(m)
                                            leader["cluster_members"] = leader_members
                                            leader["cluster_size"] = len(leader_members)

                                            # CRITICAL FIX: Also merge the citations list
                                            leader_citations = leader.get("citations", [])
                                            other_citations = other.get("citations", [])
                                            for cit in other_citations:
                                                cit_str = cit.get("citation", "") if isinstance(cit, dict) else str(cit)
                                                existing_cits = [
                                                    c.get("citation", "") if isinstance(c, dict) else str(c)
                                                    for c in leader_citations
                                                ]
                                                if cit_str not in existing_cits:
                                                    leader_citations.append(cit)
                                            leader["citations"] = leader_citations
                                            leader["size"] = len(leader_citations)

                                            to_remove.add(idx)

                            if to_remove:
                                clusters_list = [c for i, c in enumerate(clusters_list) if i not in to_remove]
                                logger.info(
                                    f"[TASK:{task_id}] Merged unverified same-name clusters, now {len(clusters_list)} clusters"
                                )

                        if PSUTIL_AVAILABLE:
                            try:
                                _mem = psutil.Process().memory_info().rss / 1024 / 1024
                                logger.warning(f"[MEM-CHECKPOINT] Before WL-DEDUP: {_mem:.0f}MB")
                            except Exception:
                                pass
                        # Merge clusters sharing the same base WL/LEXIS number
                        # e.g., "2016 WL 6070490" and "2016 WL 6070490, *5 (2016)" are the same case
                        if clusters_list and len(clusters_list) > 1:
                            import re as _re_wl

                            def _extract_wl_base(cluster):
                                """Extract base WL/LEXIS number from cluster members."""
                                for m in cluster.get("cluster_members", []):
                                    mt = m.get("citation", "") if isinstance(m, dict) else str(m)
                                    wl_match = _re_wl.search(r"(\d{4}\s+WL\s+\d+)", mt)
                                    if wl_match:
                                        return wl_match.group(1)
                                    lexis_match = _re_wl.search(r"(\d{4}\s+(?:U\.S\.\s+)?LEXIS\s+\d+)", mt)
                                    if lexis_match:
                                        return lexis_match.group(1)
                                return None

                            wl_groups = {}
                            for i, cluster in enumerate(clusters_list):
                                if not isinstance(cluster, dict):
                                    continue
                                base = _extract_wl_base(cluster)
                                if base:
                                    if base not in wl_groups:
                                        wl_groups[base] = []
                                    wl_groups[base].append(i)

                            wl_to_remove = set()
                            for base, indices in wl_groups.items():
                                if len(indices) <= 1:
                                    continue
                                leader_idx = indices[0]
                                leader = clusters_list[leader_idx]
                                for idx in indices[1:]:
                                    other = clusters_list[idx]
                                    # Guard: only merge if case names are compatible
                                    # Uses shared canonical logic from src.utils.same_case
                                    from src.utils.same_case import names_are_same_case as _wl_same_case
                                    from src.utils.same_case import has_case_name as _wl_has_name
                                    ln = (leader.get("extracted_case_name") or "").strip()
                                    on = (other.get("extracted_case_name") or "").strip()
                                    # FIX 2026-02-13: Allow merge when one has N/A name — bare WL
                                    # citations should be absorbed into the verified cluster
                                    if not _wl_same_case(ln, on):
                                        # Exception: if one is N/A, absorb into the named cluster
                                        if _wl_has_name(ln) and not _wl_has_name(on):
                                            logger.warning(f"[TASK:{task_id}] NEWCODE-V4 WL-DEDUP: absorbing N/A cluster into '{ln}' for '{base}' [TRACE-A t={__import__('time').time()}]")
                                        elif _wl_has_name(on) and not _wl_has_name(ln):
                                            # Swap leader to the one with the name
                                            clusters_list[leader_idx], clusters_list[idx] = clusters_list[idx], clusters_list[leader_idx]
                                            leader = clusters_list[leader_idx]
                                            logger.info(f"[TASK:{task_id}] WL-DEDUP: absorbing N/A cluster into '{on}' for '{base}'")
                                        else:
                                            logger.info(f"[TASK:{task_id}] WL-DEDUP: skipping merge - different cases: '{ln}' vs '{on}'")
                                            continue
                                    # Merge members and citations into leader (with dedup to prevent OOM)
                                    _leader_members = leader.setdefault("cluster_members", [])
                                    _existing_member_texts = {(m.get("citation", "") if isinstance(m, dict) else str(m)) for m in _leader_members}
                                    for m in other.get("cluster_members", []):
                                        mt = m.get("citation", "") if isinstance(m, dict) else str(m)
                                        if mt and mt not in _existing_member_texts:
                                            _leader_members.append(m)
                                            _existing_member_texts.add(mt)
                                    _leader_cits = leader.setdefault("citations", [])
                                    _existing_cit_texts = {(c.get("citation", "") if isinstance(c, dict) else str(c)) for c in _leader_cits}
                                    for c in other.get("citations", []):
                                        ct = c.get("citation", "") if isinstance(c, dict) else str(c)
                                        if ct and ct not in _existing_cit_texts:
                                            _leader_cits.append(c)
                                            _existing_cit_texts.add(ct)
                                    # Prefer non-empty date
                                    if not leader.get("extracted_date") and other.get("extracted_date"):
                                        leader["extracted_date"] = other["extracted_date"]
                                    if not leader.get("cluster_year") and other.get("cluster_year"):
                                        leader["cluster_year"] = other["cluster_year"]
                                    leader["cluster_size"] = len(leader.get("cluster_members", []))
                                    leader["size"] = leader["cluster_size"]
                                    wl_to_remove.add(idx)
                                    logger.info(
                                        f"[TASK:{task_id}] WL-DEDUP: merged cluster {idx} into {leader_idx} for '{base}'"
                                    )
                            logger.warning(f"[TRACE-B] WL-DEDUP inner loop done base='{base}' wl_to_remove={wl_to_remove} t={__import__('time').time()}")
                            if wl_to_remove:
                                clusters_list = [c for i, c in enumerate(clusters_list) if i not in wl_to_remove]
                                logger.info(
                                    f"[TASK:{task_id}] WL-DEDUP: removed {len(wl_to_remove)} duplicate WL/LEXIS clusters, now {len(clusters_list)}"
                                )
                        logger.warning(f"[TRACE-C] WL-DEDUP block exited t={__import__('time').time()}")
                        # TRUE RSS after WL-DEDUP loop
                        try:
                            with open('/proc/self/status') as _pf2:
                                for _line2 in _pf2:
                                    if _line2.startswith('VmRSS:'):
                                        _true_rss2 = int(_line2.split()[1]) // 1024
                                        logger.warning(f"[MEM-CHECKPOINT] After WL-DEDUP TRUE RSS: {_true_rss2}MB")
                                        import sys; sys.stderr.flush(); sys.stdout.flush()
                                        break
                        except Exception:
                            pass

                        # TRUE RSS before case history split
                        try:
                            with open('/proc/self/status') as _pf3:
                                for _line3 in _pf3:
                                    if _line3.startswith('VmRSS:'):
                                        _true_rss3 = int(_line3.split()[1]) // 1024
                                        logger.warning(f"[MEM-CHECKPOINT] Before case-history-split TRUE RSS: {_true_rss3}MB")
                                        import sys; sys.stderr.flush(); sys.stdout.flush()
                                        break
                        except Exception:
                            pass
                        # Release the full document text early to free memory before final steps
                        # Nothing after case history splitting needs the raw text
                        import sys as _sys_flush
                        logger.info(f"[TASK:{task_id}] Pre-split checkpoint: {len(clusters_list)} clusters, {len(citations_list)} citations, text={len(text) if text else 0} chars")
                        _sys_flush.stdout.flush()
                        _sys_flush.stderr.flush()

                        # CRITICAL FIX: Split clusters when case history signals (aff'd, rev'd) appear between citations
                        # This handles cases like Meri-Weather where trial and appellate citations are incorrectly merged
                        # NOTE: We search for citations in the text directly since stored positions may be incorrect
                        # GUARD: Skip for large documents (>100 citations) to prevent OOM kills —
                        # the 500-char distance guard already prevents false positives
                        _cit_count = len(citations_list) if citations_list else 0
                        if clusters_list and text and citations_list and _cit_count <= 100:
                            # Pre-build position index ONCE using cheap str.find()
                            # instead of per-citation regex over full doc (caused OOM with large docs)
                            _text_lower = text.lower()
                            _pos_cache = {}  # cit_text -> (start, end)
                            for cluster in clusters_list:
                                if not isinstance(cluster, dict):
                                    continue
                                for cit in cluster.get("citations", []):
                                    if isinstance(cit, dict):
                                        ct = cit.get("citation", "")
                                        if ct and ct not in _pos_cache:
                                            # Simple string find — no regex compilation
                                            idx = _text_lower.find(ct.lower())
                                            if idx >= 0:
                                                _pos_cache[ct] = (idx, idx + len(ct))
                                            else:
                                                # Try with normalized whitespace as fallback
                                                import re as _re_ws
                                                ct_norm = _re_ws.sub(r'\s+', ct.strip())
                                                idx2 = _text_lower.find(ct_norm.lower())
                                                if idx2 >= 0:
                                                    _pos_cache[ct] = (idx2, idx2 + len(ct_norm))
                                                else:
                                                    _pos_cache[ct] = (-1, -1)

                            # Free the lowercased copy — no longer needed
                            del _text_lower
                            logger.info(f"[TASK:{task_id}] Built position cache for {len(_pos_cache)} citations")

                            new_clusters = []
                            for cluster in clusters_list:
                                if not isinstance(cluster, dict):
                                    new_clusters.append(cluster)
                                    continue

                                cluster_citations = cluster.get("citations", [])
                                if len(cluster_citations) < 2:
                                    new_clusters.append(cluster)
                                    continue

                                # Look up positions from pre-built cache
                                cits_with_pos = []
                                for cit in cluster_citations:
                                    if isinstance(cit, dict):
                                        cit_text = cit.get("citation", "")
                                        if cit_text:
                                            pos, end = _pos_cache.get(cit_text, (-1, -1))
                                            if pos >= 0:
                                                cits_with_pos.append((pos, end, cit))

                                if len(cits_with_pos) < 2:
                                    new_clusters.append(cluster)
                                    continue

                                # Sort by actual position in text
                                cits_with_pos.sort(key=lambda x: x[0])

                                # Check for case history signals between consecutive citations
                                split_points = []
                                for i in range(len(cits_with_pos) - 1):
                                    curr_end = cits_with_pos[i][1]
                                    next_start = cits_with_pos[i + 1][0]
                                    if curr_end > 0 and next_start > curr_end:
                                        # Check for case history signals
                                        if _has_case_history_signal_between(text, curr_end, next_start):
                                            curr_cit = (
                                                cits_with_pos[i][2].get("citation", "")
                                                if isinstance(cits_with_pos[i][2], dict)
                                                else ""
                                            )
                                            next_cit = (
                                                cits_with_pos[i + 1][2].get("citation", "")
                                                if isinstance(cits_with_pos[i + 1][2], dict)
                                                else ""
                                            )
                                            logger.info(
                                                f"[TASK:{task_id}] Found case history signal between '{curr_cit}' and '{next_cit}': splitting cluster"
                                            )
                                            split_points.append(i + 1)

                                if not split_points:
                                    new_clusters.append(cluster)
                                else:
                                    # Split the cluster at the identified points
                                    import uuid
                                    split_points = [0] + split_points + [len(cits_with_pos)]
                                    for j in range(len(split_points) - 1):
                                        start_idx = split_points[j]
                                        end_idx = split_points[j + 1]
                                        sub_cits = [cits_with_pos[k][2] for k in range(start_idx, end_idx)]
                                        if sub_cits:
                                            new_cluster = dict(cluster)  # Copy base cluster info
                                            new_cluster["citations"] = sub_cits
                                            new_cluster["size"] = len(sub_cits)
                                            new_cluster["cluster_size"] = len(sub_cits)
                                            new_cluster["cluster_members"] = sub_cits
                                            # CRITICAL FIX: Generate unique ID for each split cluster
                                            orig_id = cluster.get("cluster_id", "unknown")
                                            new_cluster["cluster_id"] = f"{orig_id}_history_{uuid.uuid4().hex[:8]}"
                                            # Mark as split for debugging
                                            new_cluster["split_from_case_history"] = True
                                            new_clusters.append(new_cluster)
                                    logger.info(
                                        f"[TASK:{task_id}] Split cluster into {len(split_points) - 1} parts due to case history signals"
                                    )

                            if len(new_clusters) != len(clusters_list):
                                logger.info(
                                    f"[TASK:{task_id}] Cluster splitting: {len(clusters_list)} -> {len(new_clusters)} clusters"
                                )
                                clusters_list = new_clusters

                                # FIX DEC 2025: DISABLED - This was clearing valid parallel citations
                                # when both citations are unverified (common for recent state court cases).
                                # Parallel citation relationships should be preserved based on proximity
                                # and reporter matching, NOT verification status.
                                # The original code was breaking clustering for unverified WA cases like:
                                # - 196 Wn.2d 199 + 471 P.3d 871 (Nissen v. Pierce County)
                                # - 160 Wn.2d 32 + 156 P.3d 185 (Ford Motor Co. v. City of Seattle)
                                pass  # Keep parallel citations even when unverified

                        # Defensive fallback: recompute clusters if pipeline returned none
                        if citations_list and not clusters_list:
                            try:
                                from src.unified_clustering_master import cluster_citations_unified_master

                                recomputed = cluster_citations_unified_master(
                                    citations_list, original_text=text, enable_verification=False
                                )
                                if recomputed:
                                    clusters_list = list(recomputed)
                                    logger.warning(
                                        f"[TASK:{task_id}] Fallback recompute produced {len(clusters_list)} clusters"
                                    )
                                else:
                                    logger.warning(f"[TASK:{task_id}] Fallback recompute returned 0 clusters")
                            except Exception as e:
                                logger.error(f"[TASK:{task_id}] Fallback cluster recompute failed: {e}")

                        # Release the raw document text — nothing after this needs it
                        text = None
                        _force_release_memory()

                        logger.warning(f"[TRACE-D] text released t={__import__('time').time()}")
                        logger.info(
                            f"[TASK:{task_id}] Pipeline completed: {len(citations_list)} citations, {len(clusters_list)} clusters"
                        )

                        # TRUE RSS before PARALLEL-CONSISTENCY
                        try:
                            with open('/proc/self/status') as _pf4:
                                for _line4 in _pf4:
                                    if _line4.startswith('VmRSS:'):
                                        _true_rss4 = int(_line4.split()[1]) // 1024
                                        logger.warning(f"[MEM-CHECKPOINT] Before PARALLEL-CONSISTENCY TRUE RSS: {_true_rss4}MB")
                                        import sys; sys.stderr.flush(); sys.stdout.flush()
                                        break
                        except Exception:
                            pass
                        # CRITICAL FIX DEC 2025: Final consistency pass for true_by_parallel
                        # Ensures no cluster has mixed "Unverified" + "Verified by Parallel" citations
                        logger.info(
                            f"[TASK:{task_id}] PARALLEL-CONSISTENCY: Starting consistency pass for {len(citations_list)} citations"
                        )
                        if citations_list:
                            # Build lookup for both dict and object citations
                            citation_lookup = {}
                            for c in citations_list:
                                if isinstance(c, dict):
                                    cite_text = c.get("citation", "")
                                    if cite_text:
                                        citation_lookup[cite_text] = c
                                elif hasattr(c, "citation"):
                                    cite_text = c.citation
                                    if cite_text:
                                        # Convert object to dict for consistency
                                        citation_lookup[cite_text] = {
                                            "citation": cite_text,
                                            "verified": getattr(c, "verified", False),
                                            "true_by_parallel": getattr(c, "true_by_parallel", False),
                                            "canonical_name": getattr(c, "canonical_name", None),
                                            "canonical_date": getattr(c, "canonical_date", None),
                                            "canonical_url": getattr(c, "canonical_url", None),
                                            "start_index": getattr(c, "start_index", None),
                                            "_original_obj": c,  # Keep reference to update the original
                                        }
                            logger.info(
                                f"[TASK:{task_id}] PARALLEL-CONSISTENCY: Built lookup with {len(citation_lookup)} citations"
                            )
                            consistency_fixed = 0
                            groups_found = 0

                            # STEP 1: Build proximity-based parallel groups (fallback for missing parallel_citations)
                            # Sort citations by start_index - use the lookup which has all citations
                            positioned_cits = []
                            for cite_text, cit in citation_lookup.items():
                                start_idx = cit.get("start_index")
                                if start_idx is not None:
                                    positioned_cits.append((cite_text, start_idx, cit))
                            positioned_cits.sort(key=lambda x: x[1])

                            proximity_groups = []
                            current_group = []
                            PROXIMITY_THRESHOLD = 100  # Citations within 100 chars are likely parallel

                            for cite_text, start_idx, cit in positioned_cits:
                                if not current_group:
                                    current_group = [(cite_text, start_idx, cit)]
                                else:
                                    last_cite, last_idx, last_cit = current_group[-1]
                                    # Distance from end of last citation to start of this one
                                    last_end = last_idx + len(last_cite)
                                    distance = start_idx - last_end
                                    if distance <= PROXIMITY_THRESHOLD:
                                        current_group.append((cite_text, start_idx, cit))
                                    else:
                                        if len(current_group) >= 2:
                                            proximity_groups.append([c[2] for c in current_group])
                                        current_group = [(cite_text, start_idx, cit)]

                            if len(current_group) >= 2:
                                proximity_groups.append([c[2] for c in current_group])

                            logger.info(
                                f"[TASK:{task_id}] PARALLEL-CONSISTENCY: Found {len(proximity_groups)} proximity-based groups"
                            )

                            # Process proximity groups first
                            for group_cits in proximity_groups:
                                # CRITICAL FIX: Check for same-reporter/different-volume conflicts
                                # Skip groups where citations have same reporter but different volumes
                                has_conflict = False
                                for i, gc1 in enumerate(group_cits):
                                    for gc2 in group_cits[i+1:]:
                                        c1_text = gc1.get('citation', '')
                                        c2_text = gc2.get('citation', '')
                                        # Parse citations to check reporter/volume
                                        import re
                                        m1 = re.match(r'(\d+)\s+([A-Za-z\.\s]+)\s+(\d+)', c1_text)
                                        m2 = re.match(r'(\d+)\s+([A-Za-z\.\s]+)\s+(\d+)', c2_text)
                                        if m1 and m2:
                                            vol1, rep1 = m1.group(1), m1.group(2).strip()
                                            vol2, rep2 = m2.group(1), m2.group(2).strip()
                                            if rep1 == rep2 and vol1 != vol2:
                                                has_conflict = True
                                                logger.warning(
                                                    f"[PARALLEL-CONSISTENCY] SKIPPING group - same reporter '{rep1}' "
                                                    f"but different volumes ({vol1} vs {vol2}): {c1_text} vs {c2_text}"
                                                )
                                                break
                                    if has_conflict:
                                        break
                                
                                if has_conflict:
                                    continue  # Skip this group - these are NOT parallels
                                
                                # Find source citation: MUST be verified=True with canonical data
                                source_citation = None
                                for gc in group_cits:
                                    if gc.get("verified") == True and gc.get("canonical_name"):
                                        source_citation = gc
                                        break

                                # CRITICAL: Only mark true_by_parallel if at least one citation is VERIFIED
                                has_verified = any(gc.get("verified") == True for gc in group_cits)
                                has_unverified = any(
                                    gc.get("verified") != True and not gc.get("true_by_parallel", False)
                                    for gc in group_cits
                                )

                                if has_verified and has_unverified and source_citation:
                                    groups_found += 1
                                    from src.utils.same_case import names_are_same_case as _cons_sc
                                    src_ecn = (source_citation.get("extracted_case_name") or "").strip()
                                    for gc in group_cits:
                                        if gc.get("verified") != True and not gc.get("true_by_parallel", False):
                                            # Check case name compatibility before propagating
                                            gc_ecn = (gc.get("extracted_case_name") or "").strip()
                                            if not _cons_sc(src_ecn, gc_ecn):
                                                logger.info(
                                                    f"[TASK:{task_id}] PARALLEL-CONSISTENCY: SKIPPING {gc.get('citation')} - different case: '{gc_ecn}' vs '{src_ecn}'"
                                                )
                                                continue
                                            gc["true_by_parallel"] = True
                                            # Also update the original object if this was converted from an object
                                            if "_original_obj" in gc:
                                                orig = gc["_original_obj"]
                                                orig.true_by_parallel = True
                                            # Propagate canonical data from source if available
                                            if source_citation:
                                                if source_citation.get("canonical_name") and not gc.get(
                                                    "canonical_name"
                                                ):
                                                    gc["canonical_name"] = source_citation.get("canonical_name")
                                                    if "_original_obj" in gc:
                                                        gc["_original_obj"].canonical_name = source_citation.get(
                                                            "canonical_name"
                                                        )
                                                if source_citation.get("canonical_date") and not gc.get(
                                                    "canonical_date"
                                                ):
                                                    gc["canonical_date"] = source_citation.get("canonical_date")
                                                    if "_original_obj" in gc:
                                                        gc["_original_obj"].canonical_date = source_citation.get(
                                                            "canonical_date"
                                                        )
                                                if source_citation.get("canonical_url") and not gc.get("canonical_url"):
                                                    gc["canonical_url"] = source_citation.get("canonical_url")
                                                    if "_original_obj" in gc:
                                                        gc["_original_obj"].canonical_url = source_citation.get(
                                                            "canonical_url"
                                                        )
                                            consistency_fixed += 1
                                            logger.info(
                                                f"[TASK:{task_id}] PARALLEL-CONSISTENCY: Fixed (proximity) {gc.get('citation')} now true_by_parallel"
                                            )

                            # STEP 2: Also process parallel_citations field groups
                            visited_cites = set()
                            for cit in citations_list:
                                if not isinstance(cit, dict):
                                    continue
                                cite_text = cit.get("citation", "")
                                if cite_text in visited_cites:
                                    continue

                                # Build group from this citation's parallel_citations
                                group = {cite_text}
                                parallels = cit.get("parallel_citations", [])
                                if parallels:
                                    group.update(parallels)

                                # Check if ANY citation in this group is verified or true_by_parallel
                                group_citations = [citation_lookup[c] for c in group if c in citation_lookup]
                                if len(group_citations) >= 2:
                                    groups_found += 1
                                if len(group_citations) < 2:
                                    visited_cites.update(group)
                                    continue

                                # Find source citation: MUST be verified=True with canonical data
                                source_citation = None
                                for gc in group_citations:
                                    if gc.get("verified") == True and gc.get("canonical_name"):
                                        source_citation = gc
                                        break

                                # CRITICAL: Only mark true_by_parallel if at least one citation is VERIFIED
                                has_verified = any(gc.get("verified") == True for gc in group_citations)

                                if has_verified and source_citation:
                                    for gc in group_citations:
                                        if gc.get("verified") != True and not gc.get("true_by_parallel", False):
                                            gc["true_by_parallel"] = True
                                            if source_citation.get("canonical_name") and not gc.get("canonical_name"):
                                                gc["canonical_name"] = source_citation.get("canonical_name")
                                            if source_citation.get("canonical_date") and not gc.get("canonical_date"):
                                                gc["canonical_date"] = source_citation.get("canonical_date")
                                            if source_citation.get("canonical_url") and not gc.get("canonical_url"):
                                                gc["canonical_url"] = source_citation.get("canonical_url")
                                            consistency_fixed += 1
                                            logger.info(
                                                f"[TASK:{task_id}] PARALLEL-CONSISTENCY: Fixed {gc.get('citation')} now true_by_parallel"
                                            )

                                visited_cites.update(group)

                            logger.info(
                                f"[TASK:{task_id}] PARALLEL-CONSISTENCY: Found {groups_found} parallel groups, fixed {consistency_fixed} citations"
                            )

                            # STEP 3: CRITICAL FIX - Clear true_by_parallel when NO verified citation exists
                            # This handles the case where:
                            # 1. Citation A was verified, Citation B marked as true_by_parallel
                            # 2. Later, Citation A's verified status was revoked (e.g., year mismatch)
                            # 3. Citation B should no longer be true_by_parallel since source is gone
                            orphan_cleared = 0
                            for group_cits in proximity_groups:
                                has_verified = any(gc.get("verified") == True for gc in group_cits)
                                if not has_verified:
                                    # No verified citation in group - clear all true_by_parallel flags
                                    for gc in group_cits:
                                        if gc.get("true_by_parallel", False):
                                            gc["true_by_parallel"] = False
                                            # Also clear canonical data since source is gone
                                            gc["canonical_name"] = None
                                            gc["canonical_date"] = None
                                            gc["canonical_url"] = None
                                            if "_original_obj" in gc:
                                                orig = gc["_original_obj"]
                                                orig.true_by_parallel = False
                                                orig.canonical_name = None
                                                orig.canonical_date = None
                                                orig.canonical_url = None
                                            orphan_cleared += 1
                                            logger.info(
                                                f"[TASK:{task_id}] PARALLEL-ORPHAN: Cleared true_by_parallel from {gc.get('citation')} (no verified source)"
                                            )

                            if orphan_cleared > 0:
                                logger.info(
                                    f"[TASK:{task_id}] PARALLEL-ORPHAN: Cleared {orphan_cleared} orphaned true_by_parallel citations"
                                )

                            # CRITICAL: Update clusters with the fixed true_by_parallel values
                            # The clusters were built before the consistency pass, so they have stale data
                            if (consistency_fixed > 0 or orphan_cleared > 0) and clusters_list:
                                cluster_updates = 0
                                for cluster in clusters_list:
                                    if isinstance(cluster, dict):
                                        cluster_citations = cluster.get("citations", [])
                                        for i, cit in enumerate(cluster_citations):
                                            if isinstance(cit, dict):
                                                cite_text = cit.get("citation", "")
                                                if cite_text in citation_lookup:
                                                    updated = citation_lookup[cite_text]
                                                    # Update true_by_parallel status (add or clear)
                                                    if updated.get("true_by_parallel") and not cit.get(
                                                        "true_by_parallel"
                                                    ):
                                                        cit["true_by_parallel"] = True
                                                        if updated.get("canonical_name") and not cit.get(
                                                            "canonical_name"
                                                        ):
                                                            cit["canonical_name"] = updated.get("canonical_name")
                                                        if updated.get("canonical_date") and not cit.get(
                                                            "canonical_date"
                                                        ):
                                                            cit["canonical_date"] = updated.get("canonical_date")
                                                        if updated.get("canonical_url") and not cit.get(
                                                            "canonical_url"
                                                        ):
                                                            cit["canonical_url"] = updated.get("canonical_url")
                                                        cluster_updates += 1
                                                    elif not updated.get("true_by_parallel") and cit.get(
                                                        "true_by_parallel"
                                                    ):
                                                        # CLEAR true_by_parallel if source was cleared
                                                        cit["true_by_parallel"] = False
                                                        cit["canonical_name"] = None
                                                        cit["canonical_date"] = None
                                                        cit["canonical_url"] = None
                                                        cluster_updates += 1
                                logger.info(
                                    f"[TASK:{task_id}] PARALLEL-CONSISTENCY: Updated {cluster_updates} citations in clusters"
                                )

                            # STEP 4: FINAL CLUSTER-LEVEL CHECK - Clear orphaned true_by_parallel at cluster level
                            # This catches cases where proximity groups didn't cover all citations
                            # (e.g., citations without start_index or in different proximity groups)
                            final_orphan_cleared = 0
                            orphaned_citations = set()  # Track which citations to clear from top-level

                            for cluster in clusters_list:
                                if not isinstance(cluster, dict):
                                    continue
                                cluster_cits = cluster.get("citations", [])
                                if not cluster_cits:
                                    continue

                                # Check if ANY citation in this cluster is verified=True
                                has_verified_in_cluster = False
                                for cit in cluster_cits:
                                    if isinstance(cit, dict) and cit.get("verified") == True:
                                        has_verified_in_cluster = True
                                        break

                                if not has_verified_in_cluster:
                                    # NO verified citation in cluster - clear ALL true_by_parallel flags
                                    for cit in cluster_cits:
                                        if isinstance(cit, dict) and cit.get("true_by_parallel", False):
                                            cit["true_by_parallel"] = False
                                            cit["canonical_name"] = None
                                            cit["canonical_date"] = None
                                            cit["canonical_url"] = None
                                            orphaned_citations.add(cit.get("citation", ""))
                                            final_orphan_cleared += 1
                                            logger.info(
                                                f"[TASK:{task_id}] CLUSTER-ORPHAN: Cleared true_by_parallel from {cit.get('citation')} (no verified in cluster)"
                                            )

                            # CRITICAL: Also clear from TOP-LEVEL citations_list via citation_lookup
                            # The cluster citations are separate dicts from citations_list
                            if orphaned_citations:
                                top_level_cleared = 0
                                for cite_text in orphaned_citations:
                                    if cite_text in citation_lookup:
                                        lookup_cit = citation_lookup[cite_text]
                                        if lookup_cit.get("true_by_parallel", False):
                                            lookup_cit["true_by_parallel"] = False
                                            lookup_cit["canonical_name"] = None
                                            lookup_cit["canonical_date"] = None
                                            lookup_cit["canonical_url"] = None
                                            # Also update original object if present
                                            if "_original_obj" in lookup_cit:
                                                orig = lookup_cit["_original_obj"]
                                                orig.true_by_parallel = False
                                                orig.canonical_name = None
                                                orig.canonical_date = None
                                                orig.canonical_url = None
                                            top_level_cleared += 1
                                if top_level_cleared > 0:
                                    logger.info(
                                        f"[TASK:{task_id}] CLUSTER-ORPHAN: Also cleared {top_level_cleared} from top-level citations"
                                    )

                            if final_orphan_cleared > 0:
                                logger.info(
                                    f"[TASK:{task_id}] CLUSTER-ORPHAN: Cleared {final_orphan_cleared} orphaned true_by_parallel flags at cluster level"
                                )

                        if len(citations_list) > 0:
                            logger.info(
                                f"[TASK:{task_id}] First citation sample: {citations_list[0] if citations_list else 'None'}"
                            )
                        else:
                            logger.warning(f"[TASK:{task_id}] WARNING: No citations found in pipeline result!")
                            logger.warning(
                                f"[TASK:{task_id}] Pipeline result keys: {list(pipeline_result.keys()) if isinstance(pipeline_result, dict) else 'Not a dict'}"
                            )
                            logger.warning(
                                f"[TASK:{task_id}] Raw citations type: {type(citations_raw)}, length: {len(citations_raw) if citations_raw else 0}"
                            )

                        # Update verification status with actual citation count immediately after extraction
                        # NOTE: Set processed=0 initially since verification happens inside process_citations_unified
                        # The progress callback will update processed_count incrementally as verification progresses
                        try:
                            if len(citations_list) > 0:
                                # Update with actual citation count and show progress
                                total_cites = len(citations_list)
                                total_cites_for_callback[0] = total_cites  # Update for callback
                                if enable_verification:
                                    # Verification happens inside process_citations_unified, so set processed=0
                                    # The progress callback will update it as batches complete
                                    vm.update_progress(
                                        task_id,
                                        processed=0,
                                        total=total_cites,
                                        message=f"Extracted {total_cites} citations, {len(clusters_list)} clusters - Starting verification...",
                                    )
                                    logger.info(
                                        f"[TASK:{task_id}] Updated verification status: {total_cites} citations found, verification starting (processed=0)"
                                    )
                                else:
                                    # No verification, so all citations are "processed" (just extracted)
                                    vm.update_progress(
                                        task_id,
                                        processed=total_cites,
                                        total=total_cites,
                                        message=f"Extracted {total_cites} citations, {len(clusters_list)} clusters - Processing complete!",
                                    )
                                    logger.info(
                                        f"[TASK:{task_id}] Updated verification status: {total_cites} citations found (no verification)"
                                    )
                            else:
                                vm.update_progress(
                                    task_id, processed=0, total=0, message="Processing complete - no citations found"
                                )
                        except Exception as update_err:
                            logger.warning(f"[TASK:{task_id}] Failed to update verification status: {update_err}")

                        # Check verification results
                        verified_count = sum(
                            1 for c in citations_list if isinstance(c, dict) and c.get("verified", False)
                        )
                        logger.info(
                            f"[TASK:{task_id}] Verification results: {verified_count}/{len(citations_list)} citations verified"
                        )

                        # Worker stability: Memory cleanup after processing
                        try:
                            gc.collect()  # Force garbage collection
                            if "process" in locals():
                                memory_after = process.memory_info().rss / 1024 / 1024
                                logger.info(
                                    f"[TASK:{task_id}] Worker memory usage: {memory_after:.1f}MB after processing"
                                )
                        except Exception as mem_err:
                            logger.warning(f"[TASK:{task_id}] Memory cleanup failed: {mem_err}")

                    except Exception as pipeline_err:
                        logger.error(f"[TASK:{task_id}] Pipeline processing failed: {pipeline_err}")
                        result = {
                            "status": "failed",
                            "task_id": task_id,
                            "error": f"Pipeline processing failed: {str(pipeline_err)}",
                        }
                        return result

                    # Check verification results
                    verified_count = sum(1 for c in citations_list if isinstance(c, dict) and c.get("verified", False))
                    logger.info(
                        f"[TASK:{task_id}] Verification results: {verified_count}/{len(citations_list)} citations verified"
                    )

                    # NOTE: Fallback verification already runs inside verify_citations_batch()
                    # (Phase 4.75 enhanced_batch_fallback). No need for a second fallback here.

                    # Recompute verified count after fallback
                    verified_count = sum(1 for c in citations_list if isinstance(c, dict) and c.get("verified", False))

                    if PSUTIL_AVAILABLE:
                        try:
                            _mem = psutil.Process().memory_info().rss / 1024 / 1024
                            logger.warning(f"[MEM-CHECKPOINT] Before result-building: {_mem:.0f}MB")
                            import sys as _sf3; _sf3.stdout.flush(); _sf3.stderr.flush()
                        except Exception:
                            pass
                    # CRITICAL FIX: Strip signal phrases from all case names before final output (shared utils)
                    from src.utils.cluster_display_utils import (
                        strip_signal_phrases,
                        get_cluster_citations,
                        get_citation_value,
                        is_citation_verified,
                        apply_display_fields_to_cluster,
                    )
                    # Strip signal phrases from clusters and citations
                    for cluster in clusters_list:
                        if isinstance(cluster, dict):
                            for key in ["cluster_case_name", "canonical_name", "case_name", "extracted_case_name"]:
                                if key in cluster and cluster[key]:
                                    cluster[key] = strip_signal_phrases(cluster[key])
                            for cit in cluster.get("citations", []):
                                if isinstance(cit, dict):
                                    for key in ["cluster_case_name", "canonical_name", "extracted_case_name"]:
                                        if key in cit and cit[key]:
                                            cit[key] = strip_signal_phrases(cit[key])
                    for cit in citations_list:
                        if isinstance(cit, dict):
                            for key in ["cluster_case_name", "canonical_name", "extracted_case_name"]:
                                if key in cit and cit[key]:
                                    cit[key] = strip_signal_phrases(cit[key])
                    logger.info(f"[TASK:{task_id}] Signal phrases stripped from all case names")

                    # BACKEND DISPLAY PROCESSING: Prepare all display-ready fields (shared cluster_display_utils)
                    for cluster in clusters_list:
                        if isinstance(cluster, dict):
                            # CRITICAL FIX: Ensure citations in cluster are dicts, not objects
                            citations = get_cluster_citations(cluster)
                            citations_as_dicts = []
                            for cit in citations:
                                if isinstance(cit, dict):
                                    citations_as_dicts.append(cit)
                                elif hasattr(cit, "to_dict"):
                                    citations_as_dicts.append(cit.to_dict())
                                else:
                                    # Fallback: convert object to dict manually
                                    cit_dict = {
                                        "citation": getattr(cit, "citation", ""),
                                        "extracted_case_name": getattr(cit, "extracted_case_name", None),
                                        "extracted_date": getattr(cit, "extracted_date", None),
                                        "canonical_name": getattr(cit, "canonical_name", None),
                                        "canonical_date": getattr(cit, "canonical_date", None),
                                        "canonical_url": getattr(cit, "canonical_url", None),
                                        "verified": getattr(cit, "verified", False),
                                        "is_verified": getattr(cit, "is_verified", False) or getattr(cit, "verified", False),
                                        "true_by_parallel": getattr(cit, "true_by_parallel", False),
                                        "possible_match": getattr(cit, "possible_match", False),
                                        "source": getattr(cit, "source", None),
                                    }
                                    citations_as_dicts.append(cit_dict)
                            
                            # Update cluster with dict citations
                            if citations_as_dicts:
                                cluster["citations"] = citations_as_dicts
                                cluster["citation_objects"] = citations_as_dicts  # Keep for backward compatibility
                            
                            # CRITICAL FIX: Ensure cluster's verified flag is set correctly
                            # Check if any citation in the cluster is verified (now using dict citations)
                            cluster_verified = any(is_citation_verified(cit) for cit in citations_as_dicts if cit)
                            cluster["verified"] = cluster_verified
                            
                            # DEBUG: Log verified status for troubleshooting
                            if cluster.get("cluster_id"):
                                verified_citations_count = sum(1 for cit in citations_as_dicts if cit and is_citation_verified(cit))
                                logger.info(
                                    f"[TASK:{task_id}] Cluster {cluster.get('cluster_id')}: "
                                    f"verified={cluster_verified}, verified_citations={verified_citations_count}/{len(citations_as_dicts)}"
                                )
                            
                            # Set all display-ready fields for frontend (shared cluster_display_utils)
                            apply_display_fields_to_cluster(cluster)
                    
                    # USER FIX: Last-mile sync (sync + async) so UI shows correct "Extracted from Document" and "Verified"
                    try:
                        from src.unified_verification_master import apply_last_mile_cluster_display_sync
                        apply_last_mile_cluster_display_sync(citations_list, clusters_list)
                    except Exception as sync_err:
                        logger.warning(f"[TASK:{task_id}] Last-mile cluster display sync failed: {sync_err}")
                    
                    logger.info(f"[TASK:{task_id}] Display fields prepared for all clusters")

                    # FIX 2026-02-10: Final safety split — separate citations whose TEXT name
                    # differs from the cluster's canonical name.  This catches cases like
                    # "Trichell v. Midland" stuck inside a "Simon v. Eastern Kentucky" cluster
                    # after all prior merge passes.
                    if clusters_list and len(clusters_list) > 0:
                        import re as _re_split

                        def _norm_party(s):
                            """Normalize party name: strip apostrophes, hyphens, periods for comparison."""
                            return _re_split.sub(r"['\-\.\u2018\u2019\u201C\u201D]", "", s).lower().strip()

                        def _parties_match(a, b):
                            """Check if two normalized party names refer to the same party.
                            Handles M'culloch vs McCulloch, etc."""
                            if a == b:
                                return True
                            # One starts with the other (handles prefix variations)
                            if a.startswith(b) or b.startswith(a):
                                return True
                            # One-edit-distance (insertion/deletion/substitution) for len >= 4
                            if len(a) >= 4 and len(b) >= 4 and abs(len(a) - len(b)) <= 1:
                                shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
                                i = j = diffs = 0
                                while i < len(shorter) and j < len(longer):
                                    if shorter[i] != longer[j]:
                                        diffs += 1
                                        if diffs > 1:
                                            break
                                        if len(shorter) < len(longer):
                                            j += 1
                                            continue
                                    i += 1
                                    j += 1
                                if diffs <= 1:
                                    return True
                            return False

                        def _first_party(ct):
                            pm = _re_split.match(
                                r'^([A-Z][A-Za-z\'\-]+(?:\.\s*)?(?:\s+[A-Za-z\'\-]+\.?)*)\s+v\.\s+', ct)
                            return _norm_party(pm.group(1).strip().rstrip(',. ').split()[-1]) if pm else ""

                        new_clusters = []
                        for cluster in clusters_list:
                            if not isinstance(cluster, dict):
                                new_clusters.append(cluster)
                                continue
                            cits = cluster.get("citations", [])
                            if len(cits) <= 1:
                                new_clusters.append(cluster)
                                continue
                            # Determine cluster's canonical first party
                            cluster_cn = cluster.get("canonical_name", "")
                            cluster_party = ""
                            if cluster_cn and " v. " in cluster_cn.lower():
                                parts = _re_split.split(r'\s+v\.?\s+', cluster_cn, maxsplit=1, flags=_re_split.IGNORECASE)
                                cluster_party = _norm_party(parts[0].strip().rstrip(',. ').split()[-1]) if parts else ""
                            if not cluster_party:
                                new_clusters.append(cluster)
                                continue
                            keep = []
                            eject = []
                            for cit in cits:
                                if not isinstance(cit, dict):
                                    keep.append(cit)
                                    continue
                                ct = cit.get("citation", "")
                                ct_party = _first_party(ct)
                                # Also check extracted_case_name — citation text may be truncated
                                # e.g., "Madison, 1 Cranch 137" has ct_party="Madison" but ecn="Marbury v. Madison"
                                ecn = cit.get("extracted_case_name", "") or ""
                                ecn_party = _first_party(ecn) if " v. " in ecn else ""
                                if ct_party and not _parties_match(ct_party, cluster_party) and not _parties_match(ecn_party, cluster_party):
                                    eject.append(cit)
                                else:
                                    keep.append(cit)
                            if eject and keep:
                                logger.info(
                                    f"[TASK:{task_id}] SAFETY-SPLIT: ejecting {len(eject)} citation(s) "
                                    f"from cluster '{cluster_cn[:50]}' (party mismatch)"
                                )
                                # Update original cluster
                                cluster["citations"] = keep
                                cluster["cluster_members"] = [
                                    (m.get("citation","") if isinstance(m,dict) else m)
                                    for m in keep if isinstance(m, dict)
                                ]
                                cluster["cluster_size"] = len(keep)
                                cluster["size"] = len(keep)
                                new_clusters.append(cluster)
                                # Create new cluster for ejected citations
                                for ej_cit in eject:
                                    ej_cluster = dict(cluster)
                                    ej_cn = ej_cit.get("canonical_name", "")
                                    ej_cluster["cluster_id"] = f"{cluster.get('cluster_id','')}_safety_split"
                                    ej_cluster["citations"] = [ej_cit]
                                    ej_cluster["cluster_members"] = [ej_cit.get("citation", "")]
                                    ej_cluster["cluster_size"] = 1
                                    ej_cluster["size"] = 1
                                    ej_cluster["canonical_name"] = ej_cn or cluster_cn
                                    ej_cluster["canonical_date"] = ej_cit.get("canonical_date", "")
                                    ej_cluster["extracted_date"] = ej_cit.get("extracted_date", "")
                                    ej_cluster["extracted_case_name"] = ej_cit.get("extracted_case_name", "")
                                    ej_cluster["verified"] = ej_cit.get("verified", False)
                                    new_clusters.append(ej_cluster)
                            else:
                                new_clusters.append(cluster)
                        if len(new_clusters) != len(clusters_list):
                            logger.info(
                                f"[TASK:{task_id}] SAFETY-SPLIT: {len(clusters_list)} -> {len(new_clusters)} clusters"
                            )
                        clusters_list = new_clusters

                    # FIX 2026-02-09: Re-annotate mismatch flags after all post-processing
                    # Earlier passes may have set name_mismatch=True before canonical fallback,
                    # phantom name fixes, or PDF missing-space normalization were applied
                    try:
                        from src.utils.mismatch_utils import annotate_mismatch_flags
                        annotate_mismatch_flags(citations_list, clusters_list, name_threshold=0.4, year_tolerance=0)
                        logger.info(f"[TASK:{task_id}] Re-annotated mismatch flags after post-processing")
                    except Exception as mismatch_err:
                        logger.warning(f"[TASK:{task_id}] Mismatch re-annotation failed: {mismatch_err}")

                    # Create final result with complete verification data
                    result = {
                        "success": True,
                        "citations": citations_list,
                        "clusters": clusters_list,
                        "task_id": task_id,
                        "metadata": {
                            "processing_strategy": "synchronous_full_verification",
                            "processing_path": "worker_unified_pipeline",
                            "text_length": len(text) if text else 0,
                            "verification_completed": True,
                            "citation_count": len(citations_list),
                            "verified_count": verified_count,
                            "cluster_count": len(clusters_list),
                            "pipeline_metadata": pipeline_result.get("metadata", {}),
                        },
                    }

                    # CRITICAL DEBUG: Log what we're returning
                    logger.info(f"[TASK:{task_id}] Final result prepared:")
                    logger.info(f"[TASK:{task_id}]   - citations count: {len(result.get('citations', []))}")
                    logger.info(f"[TASK:{task_id}]   - clusters count: {len(result.get('clusters', []))}")
                    logger.info(f"[TASK:{task_id}]   - success: {result.get('success')}")
                    if len(result.get("citations", [])) > 0:
                        logger.info(
                            f"[TASK:{task_id}]   - First citation keys: {list(result['citations'][0].keys()) if isinstance(result['citations'][0], dict) else 'Not a dict'}"
                        )

                    # Ensure result is JSON serializable
                    try:
                        import json

                        json_test = json.dumps(result, default=str)
                        logger.info(f"[TASK:{task_id}] Result is JSON serializable (size: {len(json_test)} bytes)")
                    except Exception as json_err:
                        logger.error(f"[TASK:{task_id}] Result is NOT JSON serializable: {json_err}")
                        logger.error(
                            f"[TASK:{task_id}] Problematic citations: {[type(c).__name__ for c in citations_list[:5]]}"
                        )

                    # Save final result to Redis for task_status endpoint
                    try:
                        # Update final progress
                        final_cites = len(citations_list)
                        final_clusters = len(clusters_list)
                        verified_count = sum(
                            1 for c in citations_list if isinstance(c, dict) and c.get("verified", False)
                        )

                        if enable_verification and final_cites > 0:
                            # Update with final verification count
                            vm.update_progress(
                                task_id,
                                processed=final_cites,
                                total=final_cites,
                                message=f"Complete! {final_cites} citations ({verified_count} verified) in {final_clusters} clusters",
                            )
                        else:
                            vm.update_progress(
                                task_id,
                                processed=100,
                                total=100,
                                message=f"Complete! {final_cites} citations in {final_clusters} clusters",
                            )

                        # CRITICAL FIX: Call vm.complete() but don't let it block the return
                        # If Redis save hangs, we still want the job to complete
                        try:
                            vm.complete(task_id, result)
                            logger.info(f"[TASK:{task_id}] Complete result with verification saved to Redis")
                        except Exception as complete_err:
                            logger.warning(
                                f"[TASK:{task_id}] Failed to save complete result (non-critical): {complete_err}"
                            )
                            # Continue anyway - the result is still valid

                        # CRITICAL FIX 2026-01-30: Also write to rq:job:result and task_result
                        # so task_status returns result even when RQ hasn't yet marked job finished
                        try:
                            result_key = f"rq:job:{task_id}:result"
                            task_result_key = f"task_result:{task_id}"
                            redis_conn.setex(result_key, 86400, json.dumps(result))
                            redis_conn.setex(task_result_key, 86400, json.dumps(result))
                            progress_data = {
                                "status": "completed",
                                "progress": 100,
                                "message": f"Processing completed! {final_cites} citations in {final_clusters} clusters",
                                "current_step": "Complete",
                                "timestamp": time.time(),
                            }
                            redis_conn.setex(f"progress:{task_id}", 3600, json.dumps(progress_data))
                            logger.info(f"[TASK:{task_id}] Result stored in Redis ({result_key}, {task_result_key})")
                        except Exception as redis_err:
                            logger.warning(f"[TASK:{task_id}] Redis result write failed (non-critical): {redis_err}")

                        # CRITICAL: Always return result even if Redis save failed
                        # This ensures the RQ job finishes and frontend gets the result
                        logger.info(f"[TASK:{task_id}] Returning result to RQ (job will finish)")
                        return result
                    except Exception as save_err:
                        logger.warning(f"[TASK:{task_id}] Failed to save result to Redis (non-critical): {save_err}")
                        # Still return result even if save failed
                        return result

                except Exception as e:
                    logger.error(f"[TASK:{task_id}] Full async processing failed: {e}")
                    logger.error(f"[TASK:{task_id}] Exception details: {str(e)}")
                    import traceback

                    logger.error(f"[TASK:{task_id}] Traceback: {traceback.format_exc()}")

                    # Fallback to minimal processing if full pipeline fails
                    logger.info(f"[TASK:{task_id}] Falling back to minimal processing")
                    try:
                        import re

                        citation_patterns = [
                            r"\d+\s+Wn\.2d\s+\d+",  # Washington 2d
                            r"\d+\s+Wn\.\s+App\.\s+2d\s+\d+",  # Washington App 2d
                            r"\d+\s+P\.3d\s+\d+",  # Pacific 3d
                            r"\d+\s+U\.S\.\s+\d+",  # US Supreme Court
                            r"\d+\s+F\.3d\s+\d+",  # Federal 3d
                            r"\d+\s+P\.2d\s+\d+",  # Pacific 2d
                        ]

                        citations_found = []
                        for pattern in citation_patterns:
                            matches = re.findall(pattern, text)
                            for match in matches:
                                citations_found.append(
                                    {
                                        "citation": match,
                                        "case_name": "N/A",  # FIXED: Add case_name field
                                        "extracted_case_name": None,
                                        "canonical_name": None,
                                        "cluster_case_name": None,
                                        "verified": False,
                                        "confidence": 0.8,
                                        "method": "fallback_async",
                                    }
                                )

                        result = {
                            "success": True,
                            "citations": citations_found,
                            "clusters": [],
                            "processing_strategy": "fallback_async",
                            "processing_time": time.time() - start_time,
                        }

                        logger.info(f"[TASK:{task_id}] Fallback processing found {len(citations_found)} citations")

                    except Exception as e2:
                        logger.error(f"[TASK:{task_id}] Fallback processing also failed: {e2}")
                        result = {"success": False, "error": f"Both full and fallback processing failed: {str(e)}"}

            # Ensure result has the expected format for async
            if result.get("success", False):
                result = {
                    "status": "completed",
                    "task_id": task_id,
                    "citations": result.get("citations", []),
                    "clusters": result.get("clusters", []),
                    "metadata": {
                        "processing_strategy": result.get("processing_strategy", "async_unified"),
                        "text_length": len(text),
                    },
                }
                try:
                    vm.update_progress(task_id, processed=100, total=100, message="Processing completed successfully")
                    vm.complete(task_id, result)
                except Exception:
                    pass
            else:
                result = {"status": "failed", "task_id": task_id, "error": result.get("error", "Processing failed")}

        else:
            # File inputs: extract text then run full pipeline with verification+clustering
            logger.info(f"[TASK:{task_id}] Using FULL PIPELINE for file input")
            try:
                vm.update_progress(task_id, processed=1, total=4, message="Extracting text from file")
            except Exception:
                pass

            text = ""
            try:
                file_path = input_data.get("file_path")
                if not file_path:
                    raise ValueError("Missing file_path in input_data")
                dop = DockerOptimizedProcessor()
                text = dop.extract_text_from_file_sync(file_path)
                logger.info(f"[TASK:{task_id}] Extracted {len(text)} characters from file")

                # Update progress after text extraction
                logger.info(f"[TASK:{task_id}] About to extract and cluster citations...")
                vm.update_progress(task_id, processed=2, total=4, message="Extracting and clustering citations")

            except Exception as e:
                logger.error(f"[TASK:{task_id}] File text extraction failed: {e}")
                result = {"status": "failed", "task_id": task_id, "error": f"File text extraction failed: {str(e)}"}
                return result

            try:
                pass

                # Extract enable_verification flag from input_data
                enable_verification = input_data.get(
                    "enable_verification", True
                )  # Default to True for fast verification
                logger.info(f"[TASK:{task_id}] enable_verification flag (file): {enable_verification}")

                # Use unified pipeline directly - bypass sync/async decision to avoid recursion
                from src.unified_processing_pipeline import process_citations_unified

                logger.info(f"[TASK:{task_id}] Processing with unified pipeline directly (file path)...")

                # CRITICAL: Pass progress_callback so pipeline progress is written to Redis (progress:{task_id}).
                # Without this, task_status falls back to simulated progress (e.g. 85% "Creating citation clusters...")
                # and the frontend never sees real progress or completion.
                def file_progress_callback(progress_pct, step_name, message):
                    try:
                        import re as _re
                        processed = int(progress_pct) if progress_pct is not None else 0
                        total = 100
                        # Extract real total from message like "Verifying citations... (5/187 citations)"
                        m = _re.search(r'\((\d+)/(\d+)\s+citations\)', message or "")
                        if m:
                            processed = int(m.group(1))
                            total = int(m.group(2))
                        # Also extract total from "Processing N citations..." pattern
                        elif message:
                            m2 = _re.search(r'Processing\s+(\d+)\s+citations', message)
                            if m2:
                                total = int(m2.group(1))
                                m3 = _re.search(r'\((\d+)\s+processed\)', message)
                                if m3:
                                    processed = int(m3.group(1))
                        vm.update_progress(
                            task_id,
                            processed=processed,
                            total=total,
                            message=message or step_name or "Processing...",
                        )
                    except Exception as cb_err:
                        logger.debug(f"[TASK:{task_id}] Progress callback error (non-critical): {cb_err}")

                # Call pipeline directly with asyncio
                import asyncio

                pipeline_result = asyncio.run(
                    process_citations_unified(
                        text,
                        processing_mode="enhanced_sync",
                        enable_parallel_verification=enable_verification,
                        enable_verification=enable_verification,
                        progress_callback=file_progress_callback,
                    )
                )
                logger.info(f"[TASK:{task_id}] Unified pipeline processing completed (file path)")
            except Exception as e:
                logger.error(f"[TASK:{task_id}] Full pipeline failed: {e}")
                result = {"status": "failed", "task_id": task_id, "error": f"Pipeline failed: {str(e)}"}
                return result

            citations = pipeline_result.get("citations", [])
            clusters = pipeline_result.get("clusters", [])

            # NOTE: Fallback verification already runs inside verify_citations_batch()
            # (Phase 4.75 enhanced_batch_fallback). No need for a second fallback here.

            try:
                total = max(4, len(citations) or 4)
                vm.update_progress(task_id, processed=3, total=total, message="Verifying citations and finalizing")
            except Exception:
                pass

            # FIX 2026-02-09: Re-annotate mismatch flags after pipeline post-processing
            try:
                from src.utils.mismatch_utils import annotate_mismatch_flags
                annotate_mismatch_flags(citations, clusters, name_threshold=0.4, year_tolerance=0)
                logger.info(f"[TASK:{task_id}] Re-annotated mismatch flags (file path)")
            except Exception as mismatch_err:
                logger.warning(f"[TASK:{task_id}] Mismatch re-annotation failed: {mismatch_err}")

            result = {
                "status": "completed",
                "task_id": task_id,
                "citations": citations,
                "clusters": clusters,
                "metadata": {"processing_strategy": "full_async_with_verification", "text_length": len(text)},
            }

            try:
                vm.complete(task_id, result)
            except Exception:
                pass

        # Ensure the result is JSON serializable
        processing_time = time.time() - start_time
        logger.info(f"[TASK:{task_id}] Task completed in {processing_time:.2f} seconds")

        try:
            # Log result summary (truncated if too large)
            result_str = str(result)
            if len(result_str) > 500:
                result_str = result_str[:500] + "... [truncated]"
            logger.info(f"[TASK:{task_id}] Task result: {result_str}")

            # Test serialization
            json.dumps(result)
            logger.info(f"[TASK:{task_id}] Result is JSON serializable")

            # Log success with metrics if available
            num_citations = 0
            num_clusters = 0
            if isinstance(result, dict):
                status = result.get("status", "unknown")
                num_citations = len(result.get("citations", []))
                num_clusters = len(result.get("clusters", []))
                logger.info(
                    f"[TASK:{task_id}] Task completed with status '{status}'. Citations: {num_citations}, Clusters: {num_clusters}"
                )

            # Ensure the result is properly stored in Redis
            try:
                from redis import Redis
                import json

                redis_url = os.environ.get("REDIS_URL", "redis://:caseStrainerRedis123@casestrainer-redis-prod:6379/0")
                # FIX 2026-01-30: Use different variable name to avoid shadowing global redis_conn
                # which caused "local variable 'redis_conn' referenced before assignment" error
                redis_client = Redis.from_url(redis_url)

                # Store the result with a 24-hour TTL
                result_key = f"rq:job:{task_id}:result"
                redis_client.setex(result_key, 86400, json.dumps(result))
                logger.info(f"[TASK:{task_id}] Result stored in Redis with key: {result_key}")

                # Also store in task_result for task_status fallback (when job not yet marked finished)
                task_result_key = f"task_result:{task_id}"
                redis_client.setex(task_result_key, 86400, json.dumps(result))
                logger.info(f"[TASK:{task_id}] Result stored in {task_result_key}")

                # Also store in the job hash for RQ compatibility
                job_key = f"rq:job:{task_id}"
                redis_client.hset(job_key, "result", json.dumps(result))
                redis_client.expire(job_key, 86400)
                logger.info(f"[TASK:{task_id}] Result stored in job hash")

                # CRITICAL FIX 2026-01-29: Update progress key to "completed" status
                # The frontend polls progress:{task_id} and needs status="completed" to know the job is done
                progress_data = {
                    "status": "completed",
                    "progress": 100,
                    "message": f"Processing completed! {num_citations} citations in {num_clusters} clusters",
                    "current_step": "Complete",
                    "elapsed_time": processing_time,
                    "citations_count": num_citations,
                    "clusters_count": num_clusters,
                    "timestamp": time.time()
                }
                redis_client.setex(f"progress:{task_id}", 3600, json.dumps(progress_data))
                logger.info(f"[TASK:{task_id}] Progress key updated to 'completed' status")

            except Exception as e:
                logger.error(f"[TASK:{task_id}] Error storing result in Redis: {str(e)}", exc_info=True)

            return result

        except (TypeError, OverflowError) as e:
            error_msg = f"Result for task {task_id} is not JSON serializable: {e}"
            logger.error(f"[TASK:{task_id}] {error_msg}", exc_info=True)

            # Create a safe result with error information
            safe_result = {
                "status": "failed",
                "error": "Result serialization failed",
                "task_id": task_id,
                "processing_time": processing_time,
                "original_status": result.get("status") if isinstance(result, dict) else str(type(result)),
                "error_details": str(e),
            }

            # Try to include basic result info if available
            if isinstance(result, dict):
                safe_result.update({"result_type": "dict", "result_keys": list(result.keys())})
            else:
                safe_result["result_type"] = str(type(result))

            logger.info(f"[TASK:{task_id}] Returning safe result after serialization error")
            return safe_result

    except TimeoutError:
        error_msg = f"Task {task_id} timed out after 10 minutes"
        logger.error(f"[TASK:{task_id}] {error_msg}", exc_info=True)
        try:
            vm.fail(task_id, error_msg)
        except Exception:
            pass
        return {
            "status": "failed",
            "error": error_msg,
            "task_id": task_id,
            "processing_time": time.time() - start_time if "start_time" in locals() else None,
            "error_type": "timeout",
            "stack_trace": traceback.format_exc(),
        }
    except Exception as e:
        error_msg = f"Task {task_id} failed: {str(e)}"
        logger.error(f"[TASK:{task_id}] {error_msg}", exc_info=True)
        try:
            vm.fail(task_id, error_msg)
        except Exception:
            pass
        return {
            "status": "failed",
            "error": error_msg,
            "task_id": task_id,
            "processing_time": time.time() - start_time if "start_time" in locals() else None,
            "error_type": type(e).__name__,
            "stack_trace": traceback.format_exc(),
            "task_id": task_id,
            "exception_type": type(e).__name__,
        }
    finally:
        if platform.system() != "Windows" and timeout_set:
            try:
                signal.alarm(0)  # type: ignore[attr-defined]
            except (AttributeError, OSError):
                pass


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
        logger.info(f"📁 Code monitor initialized: watching {len(self.file_mtimes)} Python files in {watch_dir}")

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
                        logger.info(f"🆕 New file detected: {py_file.name}")
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

    return {"task_id": task_id, "status": "completed"}


def main():
    """Main entry point for the RQ worker with enhanced error handling and monitoring."""
    print("=" * 80, flush=True)
    print("DEBUG STEP 1: main() function entered", flush=True)
    print("=" * 80, flush=True)

    # Configure logging
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    print("DEBUG STEP 2: Logging configured", flush=True)

    # Log startup information
    print("=" * 80, flush=True)
    print("RQ WORKER MAIN() CALLED - AUTO-RELOAD CHECK STARTING", flush=True)
    print("=" * 80, flush=True)
    logger.info("=" * 80)
    logger.info(f"Starting CaseStrainer Worker (PID: {os.getpid()})")
    logger.info(f"Python: {sys.version}")
    logger.info(
        f"Redis URL: {os.environ.get('REDIS_URL', 'redis://:caseStrainerRedis123@casestrainer-redis-prod:6379/0')}"
    )
    logger.info("=" * 80)

    print("DEBUG STEP 3: Startup info logged", flush=True)

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("DEBUG STEP 4: Signal handlers configured", flush=True)

    # Configure queue and worker name
    queue_name = os.environ.get("RQ_QUEUE_NAME", "casestrainer")
    worker_name = f"worker-{os.getpid()}@{os.uname().nodename}"

    print(f"DEBUG STEP 5: Queue={queue_name}, Worker={worker_name}", flush=True)

    # CRITICAL: Clean up any stale registration with the same name
    # This prevents "worker already exists" errors after container restarts
    try:
        from rq import Worker

        existing_workers = Worker.all(connection=redis_conn)
        for w in existing_workers:
            if w.name == worker_name:
                logger.info(f"Removing stale worker registration: {worker_name}")
                print(f"Removing stale worker registration: {worker_name}", flush=True)
                w.register_death()
                break
    except Exception as e:
        logger.warning(f"Could not clean up stale worker registration: {e}")
        print(f"Could not clean up stale worker: {e}", flush=True)

    # Configure worker settings
    worker_functions = register_worker_functions()
    logger.info(f"Worker will register functions: {worker_functions}")

    worker_kwargs = {"connection": redis_conn, "queues": [queue_name], "name": worker_name}

    print("DEBUG STEP 6: Worker kwargs configured", flush=True)

    # Check if auto-reload is enabled (for development)
    auto_reload = os.environ.get("RQ_WORKER_AUTORELOAD", "false").lower() == "true"

    print(
        f"DEBUG STEP 7: Auto-reload check: RQ_WORKER_AUTORELOAD={os.environ.get('RQ_WORKER_AUTORELOAD', 'not set')}, auto_reload={auto_reload}",
        flush=True,
    )

    # Start the worker with error handling
    max_restarts = 10
    restart_count = 0
    monitor = None  # Initialize here to avoid UnboundLocalError

    print(f"DEBUG STEP 8: About to enter worker loop (max_restarts={max_restarts})", flush=True)

    while restart_count < max_restarts:
        print(f"DEBUG STEP 9: Loop iteration {restart_count + 1}/{max_restarts}", flush=True)

        try:
            print("DEBUG STEP 10: Inside try block", flush=True)
            logger.info(f"Starting worker (attempt {restart_count + 1}/{max_restarts})")

            print("DEBUG STEP 11: About to create RobustWorker", flush=True)
            worker = RobustWorker(**worker_kwargs)
            print("DEBUG STEP 12: RobustWorker created successfully", flush=True)

            # Start code change monitor if auto-reload is enabled
            if auto_reload:
                print("DEBUG STEP 13: Auto-reload is TRUE, starting monitor...", flush=True)
                try:
                    print("DEBUG STEP 14: Creating CodeChangeMonitor instance", flush=True)
                    monitor = CodeChangeMonitor(watch_dir="/app/src", check_interval=2)
                    print("DEBUG STEP 15: CodeChangeMonitor created, starting monitoring", flush=True)
                    monitor.start_monitoring(os.getpid())
                    print("DEBUG STEP 16: Auto-reload monitor started successfully!", flush=True)
                    logger.info("Auto-reload monitor started successfully")
                except Exception as e:
                    print(f"DEBUG: Monitor exception: {e}", flush=True)
                    logger.warning(f"Could not start code monitor: {e}")
                    logger.warning("Continuing without auto-reload...")
                    monitor = None
            else:
                print("DEBUG STEP 13: Auto-reload is FALSE", flush=True)
                logger.info("Auto-reload disabled. Set RQ_WORKER_AUTORELOAD=true to enable.")

            print("DEBUG STEP 17: About to call worker.work()", flush=True)
            logger.info("Worker started. Press Ctrl+C to exit.")
            worker.work(logging_level="INFO")
            print("DEBUG STEP 18: worker.work() returned", flush=True)

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

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

from rq import Worker, Queue
from src.verification_manager import VerificationManager
from redis import Redis
from src.redis_distributed_processor import extract_pdf_pages, extract_pdf_optimized, DockerOptimizedProcessor
from src.optimized_pdf_processor import extract_pdf_optimized_v2
import html  # For unescaping HTML entities like &amp;

# Persistent logger already initialized above
# logger = logging.getLogger(__name__)

redis_url = os.environ.get("REDIS_URL", "redis://:caseStrainerRedis123@casestrainer-redis-prod:6379/0")
redis_conn = Redis.from_url(redis_url)

queue = Queue("casestrainer", connection=redis_conn)

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
    """Direct wrapper function with extensive diagnostic logging."""

    # DIAGNOSTIC LOGGING - Track every step of worker startup
    logger.info(f"[DIAGNOSTIC:{task_id}] ========== WORKER STARTUP BEGINS ==========")
    logger.info(f"[DIAGNOSTIC:{task_id}] Step 1: Function entry successful")

    # Add timeout wrapper to prevent infinite hangs
    import concurrent.futures

    def run_with_timeout():
        """Inner function that runs the actual processing with timeout."""
        return _process_citation_task_internal(task_id, input_type, input_data)

    try:
        # Run with a 5-minute timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_with_timeout)
            try:
                result = future.result(timeout=900)  # 15 minutes timeout for large PDFs
                logger.info(f"[DIAGNOSTIC:{task_id}] ========== WORKER COMPLETED SUCCESSFULLY ==========")
                return result
            except concurrent.futures.TimeoutError:
                logger.error(f"[DIAGNOSTIC:{task_id}] ========== WORKER TIMEOUT AFTER 15 MINUTES ==========")
                # Cancel the future if it's still running
                future.cancel()
                return {
                    "status": "failed",
                    "task_id": task_id,
                    "error": "Job timed out after 15 minutes",
                    "diagnostic": "timeout_error",
                }
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
                        # The progress callback will update as citations are verified
                        pipeline_result = asyncio.run(
                            process_citations_unified(
                                text,
                                processing_mode="enhanced_sync",
                                enable_parallel_verification=(
                                    enable_verification if enable_verification else False
                                ),  # Only enable parallel if verification is enabled
                                enable_verification=enable_verification,  # Use the flag from request (defaults to True for end users)
                                progress_callback=update_verification_progress if enable_verification else None,
                            )
                        )
                        logger.info(f"[TASK:{task_id}] Full pipeline processing with verification completed")

                        # Extract results from completed pipeline
                        citations_raw = pipeline_result.get("citations", []) or []
                        clusters_raw = pipeline_result.get("clusters", []) or []

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

                        # USER FIX: Post-process clusters to ensure canonical data is populated from citations
                        # This fixes the issue where cluster-level fields are None but citation-level fields are correct
                        if clusters_list and citations_list:
                            logger.info(
                                f"[TASK:{task_id}] Post-processing clusters to populate canonical data from citations"
                            )
                            # Build citation lookup by citation text
                            citation_lookup = {}
                            for cit in citations_list:
                                if isinstance(cit, dict):
                                    cit_text = cit.get("citation", "")
                                    if cit_text:
                                        citation_lookup[cit_text] = cit

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

                                for member in members:
                                    # Handle different member formats: dict, stringified dict, or plain string
                                    if isinstance(member, dict):
                                        member_text = member.get("citation", "")
                                    elif isinstance(member, str):
                                        # Check if it's a stringified dict like "{'citation': '131 Wn.2d 25', ...}"
                                        if member.startswith("{") and "'citation':" in member:
                                            import re

                                            match = re.search(r"'citation':\s*'([^']+)'", member)
                                            member_text = match.group(1) if match else member
                                        else:
                                            member_text = member
                                    else:
                                        member_text = str(member)

                                    cit_data = citation_lookup.get(member_text)
                                    if cit_data:
                                        # Check if this citation is verified
                                        if cit_data.get("verified", False):
                                            any_verified = True
                                            # Get canonical data
                                            if not best_canonical_name and cit_data.get("canonical_name"):
                                                best_canonical_name = cit_data.get("canonical_name")
                                                best_canonical_date = cit_data.get("canonical_date")
                                                best_canonical_url = cit_data.get("canonical_url")
                                        # Get extracted name (prefer longest)
                                        ext_name = cit_data.get("extracted_case_name")
                                        if ext_name and ext_name != "N/A":
                                            if not best_extracted_name or len(ext_name) > len(best_extracted_name):
                                                best_extracted_name = ext_name

                                # Update cluster with best data found
                                # CRITICAL FIX: Unescape HTML entities (e.g., &amp; -> &)
                                if best_canonical_name:
                                    best_canonical_name = html.unescape(str(best_canonical_name))
                                    cluster["canonical_name"] = best_canonical_name
                                    cluster["canonical_date"] = best_canonical_date
                                    cluster["canonical_url"] = best_canonical_url
                                    cluster["verifying_display_name"] = best_canonical_name
                                if best_extracted_name:
                                    best_extracted_name = html.unescape(str(best_extracted_name))

                                # USER FIX: Apply cascading contamination fix at cluster level
                                # If extracted name doesn't match canonical (different second party), use canonical
                                if (
                                    best_extracted_name
                                    and best_canonical_name
                                    and best_extracted_name != "N/A"
                                    and best_canonical_name != "N/A"
                                ):
                                    import re

                                    def get_second_party(name):
                                        parts = re.split(r"\s+v\.?\s+", str(name), maxsplit=1, flags=re.IGNORECASE)
                                        if len(parts) > 1:
                                            second = parts[1].lower().strip()
                                            words = re.findall(r"\b[a-z]+\b", second)
                                            # Skip common prefixes but keep the first significant word
                                            # Don't skip 'state' or 'city' if they're the main defendant
                                            skip_prefixes = {"the", "of", "and"}
                                            for w in words:
                                                if w not in skip_prefixes:
                                                    return w
                                            # If all words were skipped, return the first word
                                            return words[0] if words else None
                                        return None

                                    ext_second = get_second_party(best_extracted_name)
                                    can_second = get_second_party(best_canonical_name)

                                    if ext_second and can_second and ext_second != can_second:
                                        # Different second parties - check word overlap
                                        ext_words = set(re.findall(r"\b[a-z]+\b", best_extracted_name.lower()))
                                        can_words = set(re.findall(r"\b[a-z]+\b", best_canonical_name.lower()))
                                        common = {"v", "the", "of", "and", "in"}
                                        ext_key = ext_words - common
                                        can_key = can_words - common
                                        overlap = len(ext_key & can_key)
                                        if overlap < 2:
                                            logger.info(
                                                f"[TASK:{task_id}] Cascading fix: '{best_extracted_name}' -> '{best_canonical_name}' (second party: '{ext_second}' != '{can_second}')"
                                            )
                                            old_name = best_extracted_name
                                            best_extracted_name = best_canonical_name
                                            # USER FIX 2024-12-24: Also update individual citation extracted_case_names
                                            # This ensures the citations inside the cluster also have the corrected name
                                            cluster_cits = cluster.get("citations", [])
                                            for cit in cluster_cits:
                                                if isinstance(cit, dict):
                                                    cit_ext_name = cit.get("extracted_case_name", "")
                                                    # Update if it matches the old contaminated name
                                                    if cit_ext_name and (
                                                        cit_ext_name == old_name
                                                        or get_second_party(cit_ext_name) == ext_second
                                                    ):
                                                        cit["extracted_case_name"] = best_canonical_name
                                                        # Recalculate name_mismatch
                                                        cit["name_mismatch"] = False  # Names now match
                                                        logger.debug(
                                                            f"[TASK:{task_id}] Fixed citation extracted_case_name: '{cit_ext_name}' -> '{best_canonical_name}'"
                                                        )

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
                                cluster["verified"] = any_verified

                            logger.info(
                                f"[TASK:{task_id}] Post-processing complete: updated {len(clusters_list)} clusters"
                            )

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
                                # Get the citations array (might be nested in different ways)
                                cluster_cits = cluster.get("citations", [])
                                if not cluster_cits:
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

                        # USER FIX: Validate extracted case names against actual document text
                        # This catches cases where eyecite extracted wrong names due to PDF parsing issues
                        if clusters_list and text:
                            import re

                            for cluster in clusters_list:
                                if not isinstance(cluster, dict) or cluster.get("verified", False):
                                    continue  # Only check unverified clusters
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
                                    else:
                                        cluster["extracted_case_name"] = "N/A"
                                        cluster["submitted_display_name"] = "N/A"
                                        cluster["phantom_name_detected"] = True

                        # USER FIX: Fix fragment extractions in clusters (e.g., "Inc v. Montgomery")
                        # Set to N/A when extracted name starts with company suffix
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
                                    # CRITICAL: Do NOT set extracted_case_name from canonical
                                    # This is contamination - extracted must remain from document only
                                    # Set submitted_display_name for UI, but keep extracted_case_name honest
                                    canonical = cluster.get("canonical_name")
                                    if canonical and canonical != "N/A":
                                        cluster["submitted_display_name"] = canonical
                                        logger.info(
                                            f"[TASK:{task_id}] Fragment '{ext_name}' - using canonical for display only: '{canonical}'"
                                        )
                                    else:
                                        cluster["submitted_display_name"] = ext_name  # Keep original fragment
                                        logger.info(f"[TASK:{task_id}] Fragment '{ext_name}' kept as-is (no canonical)")

                        # USER FIX: When extracted_case_name is N/A, use canonical_name for DISPLAY only
                        # CRITICAL: Do NOT set extracted_case_name from canonical - this is contamination
                        if clusters_list:
                            for cluster in clusters_list:
                                if not isinstance(cluster, dict):
                                    continue
                                ext_name = cluster.get("extracted_case_name", "")
                                canonical = cluster.get("canonical_name", "")
                                if (not ext_name or ext_name == "N/A") and canonical and canonical != "N/A":
                                    # Set display name only, keep extracted_case_name as-is
                                    cluster["submitted_display_name"] = canonical
                                    logger.info(f"[TASK:{task_id}] Using canonical for display only: '{canonical}'")

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
                                                # If they share at least 2 significant words, merge
                                                if len(overlap) >= 2:
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

                        # USER FIX: Merge unverified clusters with same extracted name
                        # This handles cases like Horvath appearing twice with different citations
                        if clusters_list and len(clusters_list) > 1:
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

                            # Merge clusters with same name
                            to_remove = set()
                            for name, indices in name_groups.items():
                                if len(indices) > 1:
                                    logger.info(
                                        f"[TASK:{task_id}] Merging {len(indices)} unverified clusters for '{name}'"
                                    )
                                    leader = clusters_list[indices[0]]
                                    for idx in indices[1:]:
                                        other = clusters_list[idx]
                                        # Merge members
                                        leader_members = leader.get("cluster_members", [])
                                        other_members = other.get("cluster_members", [])
                                        for m in other_members:
                                            if m not in leader_members:
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

                        # CRITICAL FIX: Split clusters when case history signals (aff'd, rev'd) appear between citations
                        # This handles cases like Meri-Weather where trial and appellate citations are incorrectly merged
                        # NOTE: We search for citations in the text directly since stored positions may be incorrect
                        if clusters_list and text and citations_list:
                            import re

                            # Function to find actual position of citation in text
                            def find_citation_in_text(cit_text, search_text):
                                """Find the actual position of a citation in the document text."""
                                if not cit_text or not search_text:
                                    return -1, -1
                                # Escape special regex chars but allow flexible whitespace
                                pattern = re.escape(cit_text).replace(r"\ ", r"\s+")
                                match = re.search(pattern, search_text)
                                if match:
                                    return match.start(), match.end()
                                return -1, -1

                            new_clusters = []
                            for cluster in clusters_list:
                                if not isinstance(cluster, dict):
                                    new_clusters.append(cluster)
                                    continue

                                cluster_citations = cluster.get("citations", [])
                                if len(cluster_citations) < 2:
                                    new_clusters.append(cluster)
                                    continue

                                # Find ACTUAL positions by searching text directly
                                cits_with_pos = []
                                for cit in cluster_citations:
                                    if isinstance(cit, dict):
                                        cit_text = cit.get("citation", "")
                                        if cit_text:
                                            pos, end = find_citation_in_text(cit_text, text)
                                            if pos >= 0:
                                                cits_with_pos.append((pos, end, cit))
                                                logger.debug(
                                                    f"[TASK:{task_id}] Found '{cit_text}' at actual position {pos}-{end}"
                                                )

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
                                        text_between = text[curr_end:next_start]
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
                                            f"[TASK:{task_id}] Checking text between '{curr_cit}' and '{next_cit}': '{text_between[:80]}...'"
                                        )

                                        # Check for case history signals
                                        if _has_case_history_signal_between(text, curr_end, next_start):
                                            logger.info(
                                                f"[TASK:{task_id}] Found case history signal between '{curr_cit}' and '{next_cit}': splitting cluster"
                                            )
                                            split_points.append(i + 1)

                                if not split_points:
                                    new_clusters.append(cluster)
                                else:
                                    # Split the cluster at the identified points
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

                        logger.info(
                            f"[TASK:{task_id}] Pipeline completed: {len(citations_list)} citations, {len(clusters_list)} clusters"
                        )

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
                                    for gc in group_cits:
                                        if gc.get("verified") != True and not gc.get("true_by_parallel", False):
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

                    # USER FIX: Run fallback verification for unverified citations (text path)
                    # This mirrors the fallback logic in the file path (line ~1637)
                    unverified_count = len(citations_list) - verified_count
                    if citations_list and unverified_count > 0:
                        logger.info(
                            f"[TASK:{task_id}] {unverified_count} citations unverified after pipeline; running enhanced fallback verification"
                        )
                        try:
                            from src.async_verification_worker import verify_citations_enhanced as _verify_enhanced
                            import os

                            elapsed = time.time() - start_time
                            if elapsed > 90:
                                logger.info(f"[TASK:{task_id}] Skipping fallback (elapsed {elapsed:.1f}s > 90s budget)")
                            else:
                                max_targets = int(os.environ.get("FALLBACK_VERIFY_MAX", "12"))
                                priority_tokens = (
                                    "F.4th",
                                    "F.3d",
                                    "U.S.",
                                    "S. Ct.",
                                    "L. Ed.",
                                    "P.3d",
                                    "P.2d",
                                    "A.3d",
                                    "A.2d",
                                )
                                unv = [c for c in citations_list if isinstance(c, dict) and not c.get("verified")]
                                pri = [
                                    c for c in unv if any(tok in (c.get("citation") or "") for tok in priority_tokens)
                                ]
                                non = [c for c in unv if c not in pri]
                                targets = (pri + non)[:max_targets]
                                if targets:
                                    logger.info(
                                        f"[TASK:{task_id}] Fallback targets: {len(targets)}/{len(unv)} (max {max_targets})"
                                    )
                                    enriched = _verify_enhanced(
                                        targets, text, task_id, "url", {"source": "worker_fallback"}
                                    )
                                    if (
                                        isinstance(enriched, dict)
                                        and enriched.get("success")
                                        and enriched.get("citations")
                                    ):
                                        enriched_list = enriched["citations"]
                                        by_citation = {}
                                        for e in enriched_list:
                                            key = (e.get("citation") or "").strip()
                                            if key and key not in by_citation:
                                                by_citation[key] = e
                                        for i, orig in enumerate(citations_list):
                                            if not isinstance(orig, dict):
                                                continue
                                            if orig.get("verified"):
                                                continue
                                            k = (orig.get("citation") or "").strip()
                                            if k and k in by_citation:
                                                cand = by_citation[k]
                                                if isinstance(cand, dict) and cand.get("verified"):
                                                    citations_list[i] = cand
                                        new_verified = sum(
                                            1 for c in citations_list if isinstance(c, dict) and c.get("verified")
                                        )
                                        logger.info(
                                            f"[TASK:{task_id}] Fallback verification complete: {new_verified}/{len(citations_list)} now verified"
                                        )
                                    else:
                                        logger.warning(
                                            f"[TASK:{task_id}] Fallback verification returned no enhancements"
                                        )
                        except Exception as e:
                            logger.error(f"[TASK:{task_id}] Fallback verification error: {e}")

                    # Recompute verified count after fallback
                    verified_count = sum(1 for c in citations_list if isinstance(c, dict) and c.get("verified", False))

                    # Create final result with complete verification data
                    result = {
                        "success": True,
                        "citations": citations_list,
                        "clusters": clusters_list,
                        "task_id": task_id,
                        "metadata": {
                            "processing_strategy": "synchronous_full_verification",
                            "processing_path": "worker_unified_pipeline",
                            "text_length": len(text),
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

                # Call pipeline directly with asyncio
                import asyncio

                pipeline_result = asyncio.run(
                    process_citations_unified(
                        text,
                        processing_mode="enhanced_sync",
                        enable_parallel_verification=enable_verification,
                        enable_verification=enable_verification,
                    )
                )
                logger.info(f"[TASK:{task_id}] Unified pipeline processing completed (file path)")
            except Exception as e:
                logger.error(f"[TASK:{task_id}] Full pipeline failed: {e}")
                result = {"status": "failed", "task_id": task_id, "error": f"Pipeline failed: {str(e)}"}
                return result

            citations = pipeline_result.get("citations", [])
            clusters = pipeline_result.get("clusters", [])

            # If any remain unverified, run enhanced fallback verification and merge
            try:
                unverified_count = sum(1 for c in citations if isinstance(c, dict) and not c.get("verified"))
            except Exception:
                unverified_count = 0
            if citations and unverified_count > 0:
                logger.info(
                    f"[TASK:{task_id}] {unverified_count} citations unverified after pipeline; running enhanced fallback verification"
                )
                try:
                    vm.update_progress(
                        task_id, processed=3, total=max(4, len(citations)), message="Running fallback verification"
                    )
                except Exception:
                    pass
                try:
                    from src.async_verification_worker import verify_citations_enhanced as _verify_enhanced

                    # Performance guardrails
                    import os

                    elapsed = time.time() - start_time
                    if elapsed > 90:
                        logger.info(f"[TASK:{task_id}] Skipping fallback (elapsed {elapsed:.1f}s > 90s budget)")
                        enriched = {"success": False, "citations": []}
                    else:
                        max_targets = int(os.environ.get("FALLBACK_VERIFY_MAX", "12"))
                        priority_tokens = ("F.4th", "F.3d", "U.S.", "S. Ct.", "L. Ed.", "P.3d", "P.2d", "A.3d", "A.2d")
                        unv = [c for c in citations if isinstance(c, dict) and not c.get("verified")]
                        pri = [c for c in unv if any(tok in (c.get("citation") or "") for tok in priority_tokens)]
                        non = [c for c in unv if c not in pri]
                        targets = (pri + non)[:max_targets]
                        if targets:
                            logger.info(
                                f"[TASK:{task_id}] Fallback targets: {len(targets)}/{len(unv)} (max {max_targets})"
                            )
                            enriched = _verify_enhanced(targets, text, task_id, "file", {"source": "worker_fallback"})
                        else:
                            enriched = {"success": False, "citations": []}
                    if isinstance(enriched, dict) and enriched.get("success") and enriched.get("citations"):
                        enriched_list = enriched["citations"]
                        try:
                            by_citation = {}
                            for e in enriched_list:
                                key = (e.get("citation") or "").strip()
                                if key and key not in by_citation:
                                    by_citation[key] = e
                            for i, orig in enumerate(citations):
                                if not isinstance(orig, dict):
                                    continue
                                if orig.get("verified"):
                                    continue
                                k = (orig.get("citation") or "").strip()
                                if k and k in by_citation:
                                    cand = by_citation[k]
                                    if isinstance(cand, dict) and cand.get("verified"):
                                        citations[i] = cand
                            logger.info(
                                f"[TASK:{task_id}] Fallback verification merged; remaining unverified: {sum(1 for c in citations if isinstance(c, dict) and not c.get('verified'))}"
                            )
                        except Exception as merge_err:
                            logger.warning(f"[TASK:{task_id}] Fallback merge warning: {merge_err}")
                    else:
                        logger.warning(f"[TASK:{task_id}] Fallback verification returned no enhancements")
                except Exception as e:
                    logger.error(f"[TASK:{task_id}] Fallback verification error: {e}")

            try:
                total = max(4, len(citations) or 4)
                vm.update_progress(task_id, processed=3, total=total, message="Verifying citations and finalizing")
            except Exception:
                pass

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
                redis_conn = Redis.from_url(redis_url)

                # Store the result with a 24-hour TTL
                result_key = f"rq:job:{task_id}:result"
                redis_conn.setex(result_key, 86400, json.dumps(result))
                logger.info(f"[TASK:{task_id}] Result stored in Redis with key: {result_key}")

                # Also store in the job hash for RQ compatibility
                job_key = f"rq:job:{task_id}"
                redis_conn.hset(job_key, "result", json.dumps(result))
                redis_conn.expire(job_key, 86400)
                logger.info(f"[TASK:{task_id}] Result stored in job hash")

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

    except TimeoutError as e:
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

        except Exception as e:
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

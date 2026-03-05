"""
RQ worker pipeline: citation task logic (extracted from rq_worker for maintainability).

run_citation_task(task_id, input_type, input_data, logger=None) runs the full citation
processing pipeline. Pass logger from the RQ worker so logs are consistent.
"""

import html
import json
import logging
import os
import platform
import re
import signal
import sys
import time
import traceback

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from src.verification_manager import VerificationManager
from src.redis_distributed_processor import DockerOptimizedProcessor
from src.rq_worker_helpers import (
    _force_release_memory,
    _get_citation_state,
    _citations_compatible_for_parallel,
    _has_case_history_signal_between,
    _extract_reporter_type_simple,
    _are_parallel_reporter_types,
)
from src.utils.cluster_filter import filter_cluster_members_by_reporter
from src.utils.mismatch_utils import compute_cluster_mismatch_flags
from src.utils.same_case import names_are_same_case
from src.utils.date_utils import validate_year_match
from src.utils.cluster_postprocess_pipeline import apply_post_verify_cluster_splits

__all__ = ["run_citation_task"]


def _ensure_redis_and_service(task_id: str, input_type: str, input_data: dict, logger):
    """Wait for Redis and create CitationService. Returns (service, None) or (None, error_result)."""
    try:
        logger.info(f"[TASK:{task_id}] Starting: type={input_type}, keys={list(input_data.keys())}")
        try:
            import redis
            from src.config import REDIS_URL
            redis_client = redis.from_url(REDIS_URL)
            max_wait = 30
            for attempt in range(max_wait):
                try:
                    redis_client.ping()
                    break
                except redis.exceptions.BusyLoadingError:  # pyright: ignore
                    if attempt % 5 == 0:
                        logger.info(f"[TASK:{task_id}] Waiting for Redis ({attempt}s)...")
                    time.sleep(1)
                except Exception:
                    if attempt < 5:
                        time.sleep(1)
                    else:
                        raise
            else:
                logger.error(f"[TASK:{task_id}] Redis not ready after {max_wait} seconds")
                return None, {
                    "status": "failed",
                    "task_id": task_id,
                    "error": f"Redis not ready after {max_wait} seconds - dataset still loading",
                }
        except Exception as e:
            logger.error(f"[TASK:{task_id}] Redis readiness error: {str(e)}")

        from src.api.services.citation_service import CitationService
        service = CitationService()
        logger.info(f"[TASK:{task_id}] Worker startup complete")
        return service, None
    except Exception as e:
        logger.error(f"[TASK:{task_id}] Startup failed: {str(e)}")
        logger.error(f"[TASK:{task_id}] Traceback: {traceback.format_exc()}")
        return None, {
            "status": "failed",
            "task_id": task_id,
            "error": f"Worker startup failed: {str(e)}",
        }


def run_citation_task(task_id: str, input_type: str, input_data: dict, logger=None):  # pyright: ignore
    import os  # Ensure os in local scope (avoids "referenced before assignment" from inner imports)
    if logger is None:
        logger = logging.getLogger(__name__)

    service, error_result = _ensure_redis_and_service(task_id, input_type, input_data, logger)
    if error_result is not None:
        return error_result

    # Setup timeout handler - disabled since we use ThreadPoolExecutor for timeout
    # Note: signal only works in main thread, so we rely on ThreadPoolExecutor timeout instead
    timeout_set = False
    logger.info(f"[TASK:{task_id}] Using ThreadPoolExecutor timeout (5 minutes) instead of signal handler")

    try:
        start_time = time.time()
        logger.info(f"[TASK:{task_id}] Main processing begins: type={input_type}")

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
                        f"[TASK:{task_id}] [WARNING] CRITICAL: Low memory detected! "
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
                        f"[TASK:{task_id}] [WARNING] WARNING: Low memory warning! "
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
        try:
            vm = VerificationManager()
            vm.register_verification(task_id, task_id, total_citations=0)
            vm.update_progress(task_id, processed=0, total=0, message="Initializing async processing")
        except Exception as _e:
            logger.error(f"[TASK:{task_id}] VerificationManager failed: {_e}")

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
                except Exception as progress_err:
                    logger.debug(f"[TASK:{task_id}] Initial URL progress update skipped: {progress_err}")

                # Extract text from URL first
                try:
                    logger.info(f"[TASK:{task_id}] Extracting text from URL...")
                    import requests
                    import tempfile
                    # os already imported at module level

                    # Download the content
                    # CRITICAL FIX: Follow redirects to handle HTTP->HTTPS redirects
                    response = requests.get(url, timeout=30, allow_redirects=True)
                    response.raise_for_status()

                    # Update progress: Downloaded, extracting text (no citation totals yet)
                    try:
                        vm.update_progress(
                            task_id, processed=0, total=0, message="Downloaded document, extracting text..."
                        )
                    except Exception as progress_err:
                        logger.debug(f"[TASK:{task_id}] URL extraction progress update skipped: {progress_err}")

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
                try:
                    # Verification is enabled by default for end users
                    # Can be disabled for testing/troubleshooting via enable_verification parameter
                    raw_ev = input_data.get("enable_verification", True)
                    if isinstance(raw_ev, str):
                        enable_verification = raw_ev.strip().lower() in ("true", "1", "yes", "on")
                    else:
                        enable_verification = bool(raw_ev)
                    # Note: URLs can have many citations, but verification is still the default behavior

                    logger.info(f"[TASK:{task_id}] Running full pipeline with verification={enable_verification} (raw from input_data: {raw_ev!r})")
                    if enable_verification:
                        try:
                            from src.config import COURTLISTENER_API_KEY
                            cl_set = bool(COURTLISTENER_API_KEY and COURTLISTENER_API_KEY.strip())
                            logger.info(f"[TASK:{task_id}] COURTLISTENER_API_KEY is {'set' if cl_set else 'NOT SET'}; verification will {'run' if cl_set else 'return unverified (set env in worker to fix)'}")
                        except Exception as _e:
                            logger.warning(f"[TASK:{task_id}] Could not check COURTLISTENER_API_KEY: {_e}")

                    # Create progress callback for worker

                    # SYNCHRONOUS COMPLETION - Wait for full verification
                    # Import required modules for synchronous processing
                    import asyncio
                    import gc  # Garbage collection for memory management
                    from src.unified_processing_pipeline import process_citations_unified

                    # Worker stability: Monitor memory usage before processing
                    if PSUTIL_AVAILABLE:
                        try:
                            process = psutil.Process()
                            memory_mb = process.memory_info().rss / 1024 / 1024
                            logger.info(f"[TASK:{task_id}] Worker memory usage: {memory_mb:.1f}MB before processing")

                            # If memory usage is high, force garbage collection
                            if memory_mb > 500:  # 500MB threshold
                                logger.warning(f"[TASK:{task_id}] High memory usage detected, forcing garbage collection")
                                gc.collect()
                        except Exception as mem_err:
                            logger.debug(f"[TASK:{task_id}] Memory check failed: {mem_err}")
                    else:
                        logger.info(f"[TASK:{task_id}] psutil not available for memory monitoring")

                    # Run full pipeline with verification and wait for completion
                    logger.info(f"[TASK:{task_id}] Processing with verification={enable_verification}...")

                    # Update progress: Starting citation extraction (no citation totals yet)
                    try:
                        vm.update_progress(
                            task_id, processed=0, total=0, message="Extracting citations from document..."
                        )
                    except Exception as progress_err:
                        logger.debug(f"[TASK:{task_id}] Citation extraction progress update skipped: {progress_err}")

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

                        pipeline_text = text if isinstance(text, str) else (text or "")
                        async def run_pipeline_with_timeout():
                            return await asyncio.wait_for(
                                process_citations_unified(
                                    pipeline_text,
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
                            except Exception as progress_err:
                                logger.debug(f"[TASK:{task_id}] Timeout progress update skipped: {progress_err}")
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
                        # Diagnostic: compare sync vs async pipeline output (see docs/PIPELINE_ENTRY_POINTS.md)
                        citations_raw = pipeline_result.get("citations", []) or []
                        logger.info(
                            f"[SYNC-ASYNC-DIAG] ASYNC (text) pipeline out: len(text)={len(pipeline_text)}, "
                            f"len(citations)={len(citations_raw)}, len(clusters)={len(pipeline_result.get('clusters', []))}"
                        )

                        # Extract results from completed pipeline
                        clusters_raw = pipeline_result.get("clusters", []) or []
                        logger.info(f"[TASK:{task_id}] Extracted {len(citations_raw)} citations, {len(clusters_raw)} clusters")

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

                        # LAST-MILE: Apply known federal citations + clear verified without URL (shared with sync path)
                        try:
                            from src.verification import (
                                apply_known_federal_citations_and_clear_verified_without_url,
                                apply_verification_paradox_fix,
                            )
                            apply_known_federal_citations_and_clear_verified_without_url(citations_list, clusters_list)
                            apply_verification_paradox_fix(citations_list)
                        except Exception as e:
                            logger.warning(f"[KNOWN-CITATION] Could not apply known citations / clear verified: {e}")

                        # Free accumulated garbage before heavy post-processing
                        _force_release_memory()

                        # USER FIX: Post-process clusters to ensure canonical data is populated from citations
                        # This fixes the issue where cluster-level fields are None but citation-level fields are correct
                        if clusters_list and citations_list:
                            logger.info(
                                f"[TASK:{task_id}] Post-processing clusters to populate canonical data from citations"
                            )
                            # Build citation lookup by citation text (and normalized form so "426 U. S. 26" matches "426 U.S. 26")
                            citation_lookup = {}
                            try:
                                from src.verification import _normalize_citation_for_known_lookup as _norm_cit
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
                                                f"from cluster '{cluster.get('cluster_id', '?')}' - doesn't match any citation ecn "
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
                                                _m_date = member.get("canonical_date")
                                                # FIX: When same canonical_url, prefer date from opinion (date_filed).
                                                # E.g. Chalkley: one member may have 2016 (context bleed), another 1928
                                                # from CourtListener. Prefer 1928 when citation is old reporter.
                                                if best_canonical_url and member.get("canonical_url") == best_canonical_url and _m_date and best_canonical_date:
                                                    _m_yr = re.search(r"(19|20)\d{2}", str(_m_date))
                                                    _b_yr = re.search(r"(19|20)\d{2}", str(best_canonical_date))
                                                    if _m_yr and _b_yr:
                                                        _m_i, _b_i = int(_m_yr.group(0)), int(_b_yr.group(0))
                                                        if _m_i != _b_i and "/opinion/" in str(best_canonical_url):
                                                            _old_reporter = bool(re.search(r"\b(?:Va\.|S\.\s*E\.\s*\d+|Tenn\.|N\.\s*E\.\s*\d+)\b", member_text))
                                                            if _old_reporter and min(_m_i, _b_i) < 1950:
                                                                best_canonical_date = str(min(_m_i, _b_i))
                                                                continue
                                                best_canonical_date = _m_date or best_canonical_date
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
                                    # Sync citation-level canonical_date when we picked opinion date over context-bleed
                                    if best_canonical_url and "/opinion/" in str(best_canonical_url):
                                        for _c in (cluster.get("citations") or []):
                                            if isinstance(_c, dict) and _c.get("canonical_url") == best_canonical_url:
                                                if _c.get("canonical_date") != best_canonical_date:
                                                    _c["canonical_date"] = best_canonical_date
                                                    _c["date_mismatch"] = False
                                        compute_cluster_mismatch_flags(cluster)
                                    # canonical_url set only in best_canonical_url block (never use Google as canonical)
                                    cluster["verifying_display_name"] = best_canonical_name
                                if best_canonical_url:
                                    _url = str(best_canonical_url).strip()
                                    _is_google = _url.startswith("https://www.google.com/search") or _url.startswith("http://www.google.com/search")
                                    if not _is_google:
                                        cluster["canonical_url"] = best_canonical_url
                                        cluster["display_canonical_url"] = best_canonical_url
                                    if not cluster.get("canonical_name") and best_canonical_name:
                                        cluster["canonical_name"] = best_canonical_name
                                        cluster["verifying_display_name"] = best_canonical_name
                                if best_extracted_name:
                                    best_extracted_name = html.unescape(str(best_extracted_name))
                                    # FIX 2026-02-01: Apply case name cleaner to fix PDF line-break hyphenation
                                    # e.g., "Co- hens" -> "Cohens", "Vir- ginia" -> "Virginia"
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
                                # Recalculate cluster mismatch flags after fixing citations
                                compute_cluster_mismatch_flags(cluster)
                                # USER RULE: verified only when we have a canonical URL (no Verified without URL)
                                cluster["verified"] = bool(best_canonical_url) and any_verified
                                # Display guard: do not present canonical/verifying identity for plain unverified clusters.
                                # Keep canonical context for diagnostic states (date mismatch / possible match),
                                # otherwise users lose the "why" (e.g., Gomes 2020 extracted vs 2021 canonical).
                                cluster_has_diagnostic_context = bool(cluster.get("has_date_mismatch") or cluster.get("has_name_mismatch"))
                                for _dc in (cluster.get("citations") or []):
                                    if not isinstance(_dc, dict):
                                        continue
                                    if _dc.get("date_mismatch") is True:
                                        cluster_has_diagnostic_context = True
                                        break
                                    if _dc.get("possible_match") is True or _dc.get("possible_match") == "true":
                                        cluster_has_diagnostic_context = True
                                        break
                                    _vstat = str(_dc.get("verification_status") or "").strip().lower()
                                    if _vstat in ("year_mismatch", "possible_match_with_url", "possible_match_gate_reject", "possible_match_no_canonical_url"):
                                        cluster_has_diagnostic_context = True
                                        break
                                if not cluster.get("verified", False) and not cluster_has_diagnostic_context:
                                    sub_name = (
                                        cluster.get("submitted_display_name")
                                        or cluster.get("extracted_case_name")
                                        or "N/A"
                                    )
                                    sub_date = (
                                        cluster.get("submitted_display_date")
                                        or cluster.get("extracted_date")
                                        or "N/A"
                                    )
                                    # FIX 2026-02-24: Preserve canonical date for display even when not verified
                                    # This allows frontend to show "Different date" information (e.g., 1831 vs 2023)
                                    found_canonical_date = best_canonical_date or cluster.get("canonical_date")
                                    cluster["canonical_url"] = None
                                    cluster["display_canonical_url"] = None
                                    cluster["canonical_name"] = sub_name
                                    cluster["verifying_display_name"] = sub_name
                                    # Use extracted date for verifying_display_date, but preserve canonical for comparison
                                    cluster["verifying_display_date"] = sub_date
                                    # Preserve found canonical date so frontend can show date mismatch info
                                    if found_canonical_date and found_canonical_date != sub_date:
                                        cluster["found_canonical_date"] = found_canonical_date
                                        logger.info(
                                            f"[TASK:{task_id}] Preserved found_canonical_date '{found_canonical_date}' "
                                            f"for unverified cluster (extracted_date='{sub_date}')"
                                        )
                                    for _cit in (cluster.get("citations") or []):
                                        if not isinstance(_cit, dict):
                                            continue
                                        _has_url = bool(
                                            str(_cit.get("canonical_url") or _cit.get("url") or "").strip()
                                        )
                                        _is_verified = bool(
                                            _cit.get("verified") is True
                                            or _cit.get("verified") == "true"
                                            or _cit.get("is_verified") is True
                                        )
                                        _has_diagnostic = bool(
                                            _cit.get("date_mismatch") is True
                                            or _cit.get("possible_match") is True
                                            or _cit.get("possible_match") == "true"
                                            or str(_cit.get("verification_status") or "").strip().lower()
                                            in ("year_mismatch", "possible_match_with_url", "possible_match_gate_reject", "possible_match_no_canonical_url")
                                        )
                                        if not (_has_url and _is_verified) and not _has_diagnostic:
                                            _cit["canonical_url"] = None
                                            _cit["url"] = None
                                            _cit["canonical_name"] = None
                                            _cit["canonical_date"] = None

                            logger.info(
                                f"[TASK:{task_id}] Post-processing complete: updated {len(clusters_list)} clusters"
                            )

                        # POST-VERIFY SPLIT: split clusters that mix Supreme Court (U.S.) and District (F. Supp.)
                        if clusters_list:
                            clusters_list = apply_post_verify_cluster_splits(clusters_list, run_id=task_id)

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
                                except Exception as year_extract_err:
                                    logger.debug(
                                        f"[TASK:{task_id}] Cluster date year extraction skipped for '{cluster_date_str}': {year_extract_err}"
                                    )
                                
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
                                
                                # Backfill only missing citation extracted_date values from cluster_date.
                                # Do NOT overwrite citation-specific extracted years, because mixed
                                # same-name clusters can legitimately contain different years
                                # (e.g., Gomes 2020 and Gomes 2021 lanes).
                                for cit in cluster_cits:
                                    if isinstance(cit, dict):
                                        old_date = cit.get("extracted_date")
                                        old_date_text = str(old_date or "").strip()
                                        if old_date_text and old_date_text not in ("N/A", "Unknown Year", "unknown"):
                                            continue
                                        cit["extracted_date"] = cluster_date
                                        date_sync_count += 1
                                        # Recalculate date_mismatch now that extracted_date is updated
                                        canonical_date = cit.get("canonical_date")
                                        if canonical_date:
                                            is_valid, _ = validate_year_match(
                                                str(cluster_date), str(canonical_date), tolerance=0
                                            )
                                            cit["date_mismatch"] = not is_valid
                                        else:
                                            cit["date_mismatch"] = False
                                # Recalculate cluster mismatch flags after date sync
                                compute_cluster_mismatch_flags(cluster)
                            if date_sync_count > 0:
                                logger.info(
                                    f"[TASK:{task_id}] Synchronized {date_sync_count} citation extracted_dates with cluster dates"
                                )

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
                                    context.replace("-", "-")
                                    .replace("-", "-")
                                    .replace("\u2013", "-")
                                    .replace("\u2014", "-")
                                )
                                first_party_normalized = (
                                    first_party_key.replace("-", "-")
                                    .replace("-", "-")
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
                                                text_lower.replace("-", "-")
                                                .replace("-", "-")
                                                .replace("\u2013", "-")
                                                .replace("\u2014", "-")
                                            )
                                            canonical_normalized = (
                                                canonical_first_key.replace("-", "-")
                                                .replace("-", "-")
                                                .replace("\u2013", "-")
                                                .replace("\u2014", "-")
                                            )

                                            if canonical_normalized not in text_normalized:
                                                # Canonical name not in document - this is a phantom from CaseMine
                                                logger.warning(
                                                    f"[TASK:{task_id}] [BLOCK] PHANTOM CANONICAL: '{canonical_name}' not found in document "
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
                                                    f"[TASK:{task_id}] [OK] Canonical name '{canonical_name}' found in document"
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
                                    # Only trust canonical upgrades when cluster is effectively verified.
                                    _eff_verified = bool(
                                        cluster.get("verified", False)
                                        and str(cluster.get("canonical_url") or cluster.get("display_canonical_url") or "").strip()
                                    )
                                    # FIX 2026-02-10: If canonical_name contains the fragment,
                                    # use canonical - it's the same case, just more complete
                                    # e.g. "Inc. v. Robins" -> "Spokeo, Inc. v. Robins"
                                    canonical = (cluster.get("canonical_name") or "").strip()
                                    if _eff_verified and canonical and canonical != "N/A" and ext_name.lower() in canonical.lower():
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
                                    _eff_verified = bool(
                                        cluster.get("verified", False)
                                        and str(cluster.get("canonical_url") or cluster.get("display_canonical_url") or "").strip()
                                    )
                                    canonical_fallback = (cluster.get("canonical_name") or "").strip()
                                    if not canonical_fallback or canonical_fallback == "N/A":
                                        for cit in cluster.get("citations", cluster.get("citation_objects", [])):
                                            if isinstance(cit, dict):
                                                cn = (cit.get("canonical_name") or "").strip()
                                                if cn and cn != "N/A":
                                                    canonical_fallback = cn
                                                    break
                                    if _eff_verified and canonical_fallback and canonical_fallback != "N/A":
                                        cluster["submitted_display_name"] = canonical_fallback
                                        cluster["extracted_case_name"] = canonical_fallback
                                        logger.info(f"[TASK:{task_id}] Extraction failed - using canonical '{canonical_fallback}' as submitted_display_name")
                                    else:
                                        cluster["submitted_display_name"] = "N/A"
                                        logger.info(f"[TASK:{task_id}] Extraction failed - no canonical available, keeping N/A")

                        # Upstream hardening: merge duplicates only on stable identity signals.
                        # Avoid name-similarity merges that can collapse different same-name cases
                        # across years (e.g., Gomes 2020 vs Gomes 2021, Doe variants).
                        if clusters_list and len(clusters_list) > 1:
                            to_remove = set()
                            by_identity = {}
                            for i, cluster in enumerate(clusters_list):
                                if not isinstance(cluster, dict):
                                    continue
                                cu = str(cluster.get("canonical_url") or cluster.get("display_canonical_url") or "").strip()
                                if cu:
                                    by_identity.setdefault(f"url:{cu}", []).append(i)
                                    continue
                                # fallback identity: exact base WL/LEXIS cite in members
                                wl_base = None
                                for m in cluster.get("cluster_members", []) or []:
                                    mt = m.get("citation", "") if isinstance(m, dict) else str(m)
                                    wm = re.search(r"(\d{4}\s+(?:WL|U\.S\.?\s*LEXIS|LEXIS)\s+\d+)", mt, re.IGNORECASE)
                                    if wm:
                                        wl_base = re.sub(r"\s+", " ", wm.group(1).strip().lower())
                                        break
                                if wl_base:
                                    by_identity.setdefault(f"wl:{wl_base}", []).append(i)

                            for _id, idxs in by_identity.items():
                                if len(idxs) <= 1:
                                    continue
                                leader_idx = idxs[0]
                                leader = clusters_list[leader_idx]
                                merged_this_id = 0
                                for idx in idxs[1:]:
                                    other = clusters_list[idx]
                                    # Do not merge clusters that were split by extracted name (e.g. Soo Line vs In re Southwest)
                                    leader_ecn = (leader.get("extracted_case_name") or "").strip() or None
                                    other_ecn = (other.get("extracted_case_name") or "").strip() or None
                                    if not names_are_same_case(leader_ecn, other_ecn):
                                        continue
                                    leader_members = leader.get("cluster_members", [])
                                    for m in other.get("cluster_members", []):
                                        if m not in leader_members:
                                            first_member = leader_members[0] if leader_members else m
                                            filtered = filter_cluster_members_by_reporter(first_member, [m])
                                            if filtered:
                                                leader_members.append(m)
                                    leader["cluster_members"] = leader_members
                                    leader["cluster_size"] = len(leader_members)
                                    # merge citations
                                    lc = leader.get("citations", [])
                                    ec = {(c.get("citation", "") if isinstance(c, dict) else str(c)) for c in lc}
                                    for c in other.get("citations", []):
                                        ct = c.get("citation", "") if isinstance(c, dict) else str(c)
                                        if ct and ct not in ec:
                                            lc.append(c)
                                            ec.add(ct)
                                    leader["citations"] = lc
                                    leader["size"] = len(lc)
                                    to_remove.add(idx)
                                    merged_this_id += 1
                                if merged_this_id:
                                    logger.info(
                                        f"[TASK:{task_id}] Identity-merged {merged_this_id + 1} clusters for {_id}"
                                    )

                            if to_remove:
                                clusters_list = [c for i, c in enumerate(clusters_list) if i not in to_remove]
                                logger.info(f"[TASK:{task_id}] Removed {len(to_remove)} identity-duplicate clusters, now {len(clusters_list)}")

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
                                                # FIX: Skip slip opinion placeholders - they are NOT parallel citations
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
                                    # Same WL/LEXIS base denotes the same citation identity.
                                    # Merge even when extracted names drift due OCR/context contamination.
                                    from src.utils.same_case import has_case_name as _wl_has_name
                                    ln = (leader.get("extracted_case_name") or "").strip()
                                    on = (other.get("extracted_case_name") or "").strip()
                                    if _wl_has_name(on) and not _wl_has_name(ln):
                                        # Prefer named cluster as leader.
                                        clusters_list[leader_idx], clusters_list[idx] = clusters_list[idx], clusters_list[leader_idx]
                                        leader = clusters_list[leader_idx]
                                        ln, on = on, ln
                                    elif _wl_has_name(on) and _wl_has_name(ln):
                                        # Prefer the more specific textual name (contains "v." or longer token span).
                                        ln_score = (1 if " v. " in ln.lower() else 0, len(ln))
                                        on_score = (1 if " v. " in on.lower() else 0, len(on))
                                        if on_score > ln_score:
                                            clusters_list[leader_idx], clusters_list[idx] = clusters_list[idx], clusters_list[leader_idx]
                                            leader = clusters_list[leader_idx]
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
                            if wl_to_remove:
                                clusters_list = [c for i, c in enumerate(clusters_list) if i not in wl_to_remove]
                                logger.info(
                                    f"[TASK:{task_id}] WL-DEDUP: removed {len(wl_to_remove)} duplicate WL/LEXIS clusters, now {len(clusters_list)}"
                                )

                        # Merge clusters that share any citation (catches duplicates with different extracted names/years)
                        if clusters_list and len(clusters_list) > 1:
                            try:
                                from src.utils.response_enrichment import merge_clusters_by_shared_citation
                                before_shared = len(clusters_list)
                                clusters_list = merge_clusters_by_shared_citation(clusters_list)
                                if len(clusters_list) < before_shared:
                                    logger.info(
                                        f"[TASK:{task_id}] Shared-citation merge: {before_shared} -> {len(clusters_list)} clusters"
                                    )
                            except Exception as _merge_err:
                                logger.warning(f"[TASK:{task_id}] Shared-citation merge skipped: {_merge_err}")

                        # Merge clusters that are the same case: same normalized name, same year, ≥1 citation in common
                        if clusters_list and len(clusters_list) > 1:
                            try:
                                from src.utils.response_enrichment import merge_clusters_by_same_case_identity
                                before_same_case = len(clusters_list)
                                clusters_list = merge_clusters_by_same_case_identity(clusters_list)
                                if len(clusters_list) < before_same_case:
                                    logger.info(
                                        f"[TASK:{task_id}] Same-case merge: {before_same_case} -> {len(clusters_list)} clusters"
                                    )
                            except Exception as _merge_err:
                                logger.warning(f"[TASK:{task_id}] Same-case merge skipped: {_merge_err}")

                        logger.info(f"[TASK:{task_id}] Pre-split: {len(clusters_list)} clusters, {len(citations_list)} citations")

                        # CRITICAL FIX: Split clusters when case history signals (aff'd, rev'd) appear between citations
                        # This handles cases like Meri-Weather where trial and appellate citations are incorrectly merged
                        # NOTE: We search for citations in the text directly since stored positions may be incorrect
                        # GUARD: Skip for large documents (>100 citations) to prevent OOM kills -
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
                                            # Simple string find - no regex compilation
                                            idx = _text_lower.find(ct.lower())
                                            if idx >= 0:
                                                _pos_cache[ct] = (idx, idx + len(ct))
                                            else:
                                                # Try with normalized whitespace as fallback
                                                import re as _re_ws
                                                ct_norm = _re_ws.sub(r'\s+', ' ', ct.strip())
                                                idx2 = _text_lower.find(ct_norm.lower())
                                                if idx2 >= 0:
                                                    _pos_cache[ct] = (idx2, idx2 + len(ct_norm))
                                                else:
                                                    _pos_cache[ct] = (-1, -1)

                            # Free the lowercased copy - no longer needed
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
                                logger.debug(
                                    f"[TASK:{task_id}] Preserving unverified parallel relationships by design"
                                )

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

                        # Release the raw document text - nothing after this needs it
                        text = None
                        _force_release_memory()

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
                                            "source": getattr(c, "source", None),
                                            "verification_status": getattr(c, "verification_status", None),
                                            "verification_error": getattr(c, "verification_error", None),
                                            "extracted_case_name": getattr(c, "extracted_case_name", None),
                                            # Preserve explicit parallel mappings and TOA metadata from object citations.
                                            # Without these, Step 2 cannot propagate verified parallels and TOA filtering
                                            # silently fails for object-backed citations.
                                            "parallel_citations": getattr(c, "parallel_citations", []) or [],
                                            "metadata": getattr(c, "metadata", {}) or {},
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

                            def _is_toa_citation(c):
                                if not isinstance(c, dict):
                                    return False
                                md = c.get("metadata")
                                if isinstance(md, dict) and md.get("in_toa_section"):
                                    return True
                                # Defensive fallback for object->dict conversions where TOA metadata
                                # may be missing: detect common TOA header leakage in citation text.
                                ctext = str(c.get("citation", "") or "")
                                return bool(
                                    "table of authorities" in ctext.lower()
                                    or "cases-continued:" in ctext.lower()
                                )

                            from src.utils.same_case import names_are_same_case as _cons_sc
                            import re as _re_cons

                            def _year_num(v):
                                m = _re_cons.search(r"\b(17|18|19|20)\d{2}\b", str(v or ""))
                                return int(m.group(0)) if m else None

                            def _strong_case_name(v):
                                s = str(v or "").strip()
                                if not s or s.upper() == "N/A":
                                    return False
                                if " v" not in s.lower():
                                    return False
                                return len([t for t in s.split() if t]) >= 3

                            def _same_case_parallel_strict(src, gc):
                                src_name = (
                                    src.get("extracted_case_name")
                                    or src.get("canonical_name")
                                    or ""
                                ).strip()
                                gc_name = (
                                    gc.get("extracted_case_name")
                                    or gc.get("canonical_name")
                                    or ""
                                ).strip()
                                if not (_strong_case_name(src_name) and _strong_case_name(gc_name)):
                                    return False
                                if not _cons_sc(src_name, gc_name):
                                    return False
                                # Source is a verified citation: prefer canonical year over extracted year.
                                src_year = _year_num(src.get("canonical_date")) or _year_num(src.get("extracted_date"))
                                # Target year: prefer citation-intrinsic year (especially WL year), then extracted/canonical.
                                gc_cit_year = _year_num(gc.get("citation"))
                                gc_year = gc_cit_year or _year_num(gc.get("extracted_date")) or _year_num(gc.get("canonical_date"))
                                # Parallel means same case; require exact year when both are known.
                                if src_year is not None and gc_year is not None and src_year != gc_year:
                                    return False
                                return True

                            # Process proximity groups first
                            for group_cits in proximity_groups:
                                # TOA citations are often adjacent but are not true parallel cites.
                                # Skip propagation for groups containing TOA entries.
                                if any(_is_toa_citation(gc) for gc in group_cits):
                                    continue
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
                                
                                # Find source citation: MUST be verified=True with canonical data and real URL (not Google search)
                                source_citation = None
                                for gc in group_cits:
                                    if gc.get("verified") == True and gc.get("canonical_name"):
                                        src_url = (gc.get("canonical_url") or gc.get("url") or "").strip()
                                        if src_url and (src_url.startswith("https://www.google.com/search") or src_url.startswith("http://www.google.com/search")):
                                            continue  # Google search URL = not real verification
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
                                            # Strict guard: parallel only for same case (and same year when known).
                                            if not _same_case_parallel_strict(source_citation, gc):
                                                logger.info(
                                                    f"[TASK:{task_id}] PARALLEL-CONSISTENCY: SKIPPING {gc.get('citation')} "
                                                    f"- not strict same-case/same-year as source"
                                                )
                                                continue
                                            # Court-tier guard: prevent cross-tier promotion.
                                            # F. Supp. <-> F.* <-> U.S./S.Ct./L.Ed. must remain separate.
                                            try:
                                                from src.utils.post_verify_split import reporter_tier, reporter_court_label

                                                src_tier = reporter_tier(source_citation.get("citation", ""))
                                                tgt_tier = reporter_tier(gc.get("citation", ""))
                                                if src_tier in {"supreme", "district", "circuit"} and tgt_tier in {"supreme", "district", "circuit"} and src_tier != tgt_tier:
                                                    gc["court_mismatch"] = True
                                                    logger.info(
                                                        f"[TASK:{task_id}] PARALLEL-CONSISTENCY: SKIPPING {gc.get('citation')} "
                                                        f"- court mismatch ({reporter_court_label(source_citation.get('citation',''))} vs "
                                                        f"{reporter_court_label(gc.get('citation',''))})"
                                                    )
                                                    continue
                                            except Exception:
                                                pass
                                            # Do NOT mark true_by_parallel if source has Google search URL
                                            src_url = (source_citation.get("canonical_url") or source_citation.get("url") or "").strip()
                                            if src_url and (src_url.startswith("https://www.google.com/search") or src_url.startswith("http://www.google.com/search")):
                                                logger.info(
                                                    f"[TASK:{task_id}] PARALLEL-CONSISTENCY: SKIPPING {gc.get('citation')} "
                                                    f"- source has Google search URL (not real verification)"
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
                                if _is_toa_citation(cit):
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
                                if any(_is_toa_citation(gc) for gc in group_citations):
                                    visited_cites.update(group)
                                    continue
                                if len(group_citations) >= 2:
                                    groups_found += 1
                                if len(group_citations) < 2:
                                    visited_cites.update(group)
                                    continue

                                # Find source citation: MUST be verified=True with canonical data and real URL (not Google search)
                                source_citation = None
                                for gc in group_citations:
                                    if gc.get("verified") == True and gc.get("canonical_name"):
                                        src_url = (gc.get("canonical_url") or gc.get("url") or "").strip()
                                        if src_url and (src_url.startswith("https://www.google.com/search") or src_url.startswith("http://www.google.com/search")):
                                            continue  # Google search URL = not real verification
                                        source_citation = gc
                                        break

                                # CRITICAL: Only mark true_by_parallel if at least one citation is VERIFIED
                                has_verified = any(gc.get("verified") == True for gc in group_citations)

                                if has_verified and source_citation:
                                    for gc in group_citations:
                                        if gc.get("verified") != True and not gc.get("true_by_parallel", False):
                                            if not _same_case_parallel_strict(source_citation, gc):
                                                logger.info(
                                                    f"[TASK:{task_id}] PARALLEL-CONSISTENCY: SKIPPING {gc.get('citation')} "
                                                    f"- explicit group but not strict same-case/same-year"
                                                )
                                                continue
                                            # Court-tier guard: keep Supreme/District/Circuit evidence separate.
                                            try:
                                                from src.utils.post_verify_split import reporter_tier, reporter_court_label

                                                src_tier = reporter_tier(source_citation.get("citation", ""))
                                                tgt_tier = reporter_tier(gc.get("citation", ""))
                                                if src_tier in {"supreme", "district", "circuit"} and tgt_tier in {"supreme", "district", "circuit"} and src_tier != tgt_tier:
                                                    gc["court_mismatch"] = True
                                                    logger.info(
                                                        f"[TASK:{task_id}] PARALLEL-CONSISTENCY: SKIPPING {gc.get('citation')} "
                                                        f"- court mismatch ({reporter_court_label(source_citation.get('citation',''))} vs "
                                                        f"{reporter_court_label(gc.get('citation',''))})"
                                                    )
                                                    continue
                                            except Exception:
                                                pass
                                            # Do NOT mark true_by_parallel if source has Google search URL
                                            src_url = (source_citation.get("canonical_url") or source_citation.get("url") or "").strip()
                                            if src_url and (src_url.startswith("https://www.google.com/search") or src_url.startswith("http://www.google.com/search")):
                                                logger.info(
                                                    f"[TASK:{task_id}] PARALLEL-CONSISTENCY: SKIPPING {gc.get('citation')} "
                                                    f"- source has Google search URL (explicit group)"
                                                )
                                                continue
                                            gc["true_by_parallel"] = True
                                            if source_citation.get("canonical_name") and not gc.get("canonical_name"):
                                                gc["canonical_name"] = source_citation.get("canonical_name")
                                            if source_citation.get("canonical_date") and not gc.get("canonical_date"):
                                                gc["canonical_date"] = source_citation.get("canonical_date")
                                            if source_citation.get("canonical_url") and not gc.get("canonical_url"):
                                                gc["canonical_url"] = source_citation.get("canonical_url")
                                            # Promote explicit parallel citations to verified when they inherit
                                            # canonical data from a verified source citation in the same explicit group.
                                            # This avoids later cluster-orphan cleanup wiping valid WL/parallel links.
                                            if gc.get("canonical_name") and gc.get("canonical_url"):
                                                gc["verified"] = True
                                                gc["source"] = gc.get("source") or "Parallel-Citation"
                                                gc["verification_status"] = gc.get("verification_status") or "verified"
                                                gc["verification_error"] = None
                                                if "_original_obj" in gc:
                                                    orig = gc["_original_obj"]
                                                    orig.verified = True
                                                    orig.source = getattr(orig, "source", None) or "Parallel-Citation"
                                                    orig.verification_status = (
                                                        getattr(orig, "verification_status", None) or "verified"
                                                    )
                                                    orig.verification_error = None
                                            consistency_fixed += 1
                                            logger.info(
                                                f"[TASK:{task_id}] PARALLEL-CONSISTENCY: Fixed {gc.get('citation')} now true_by_parallel"
                                            )

                                visited_cites.update(group)

                            # STEP 2.5: Name+year rescue lane for WL/Lexis citations.
                            # Some normalized citation rows lose explicit parallel_citations links
                            # before this stage. For proprietary cites, recover from a verified
                            # sibling using strict same-case matching and conservative year check.
                            try:
                                verified_sources = []
                                for _c in citation_lookup.values():
                                    if (
                                        isinstance(_c, dict)
                                        and _c.get("verified") == True
                                        and _c.get("canonical_name")
                                        and _c.get("canonical_url")
                                    ):
                                        verified_sources.append(_c)

                                for gc in citation_lookup.values():
                                    if not isinstance(gc, dict):
                                        continue
                                    if gc.get("verified") == True or gc.get("true_by_parallel", False):
                                        continue
                                    if _is_toa_citation(gc):
                                        continue

                                    cit_txt = str(gc.get("citation", "") or "")
                                    is_proprietary = (" WL " in cit_txt) or (" Lexis " in cit_txt) or (" U.S. Lexis " in cit_txt)
                                    if not is_proprietary:
                                        continue

                                    gc_name = (gc.get("extracted_case_name") or "").strip()
                                    # Require minimally strong case name before rescue
                                    if (
                                        not gc_name
                                        or gc_name.upper() == "N/A"
                                        or (" v" not in gc_name.lower())
                                        or len([t for t in gc_name.split() if t]) < 3
                                    ):
                                        continue

                                    gc_year = _year_num(gc.get("extracted_date")) or _year_num(gc.get("canonical_date"))
                                    matched_source = None
                                    for src in verified_sources:
                                        if not _same_case_parallel_strict(src, gc):
                                            continue
                                        matched_source = src
                                        break

                                    if not matched_source:
                                        continue

                                    # Do NOT mark true_by_parallel if source has Google search URL
                                    src_url = (matched_source.get("canonical_url") or matched_source.get("url") or "").strip()
                                    if src_url and (src_url.startswith("https://www.google.com/search") or src_url.startswith("http://www.google.com/search")):
                                        continue
                                    gc["true_by_parallel"] = True
                                    if matched_source.get("canonical_name") and not gc.get("canonical_name"):
                                        gc["canonical_name"] = matched_source.get("canonical_name")
                                    if matched_source.get("canonical_date") and not gc.get("canonical_date"):
                                        gc["canonical_date"] = matched_source.get("canonical_date")
                                    if matched_source.get("canonical_url") and not gc.get("canonical_url"):
                                        gc["canonical_url"] = matched_source.get("canonical_url")

                                    # Promote to verified only when canonical URL is present.
                                    if gc.get("canonical_name") and gc.get("canonical_url"):
                                        gc["verified"] = True
                                        gc["source"] = gc.get("source") or "Parallel-Citation"
                                        gc["verification_status"] = gc.get("verification_status") or "verified"
                                        gc["verification_error"] = None

                                    if "_original_obj" in gc:
                                        orig = gc["_original_obj"]
                                        orig.true_by_parallel = True
                                        if getattr(orig, "canonical_name", None) is None and gc.get("canonical_name"):
                                            orig.canonical_name = gc.get("canonical_name")
                                        if getattr(orig, "canonical_date", None) is None and gc.get("canonical_date"):
                                            orig.canonical_date = gc.get("canonical_date")
                                        if getattr(orig, "canonical_url", None) is None and gc.get("canonical_url"):
                                            orig.canonical_url = gc.get("canonical_url")
                                        if gc.get("verified") == True:
                                            orig.verified = True
                                            orig.source = getattr(orig, "source", None) or "Parallel-Citation"
                                            orig.verification_status = (
                                                getattr(orig, "verification_status", None) or "verified"
                                            )
                                            orig.verification_error = None

                                    consistency_fixed += 1
                                    logger.info(
                                        f"[TASK:{task_id}] PARALLEL-CONSISTENCY: Fixed (name-year rescue) "
                                        f"{gc.get('citation')} now true_by_parallel"
                                    )
                            except Exception as _cons_err:
                                logger.warning(
                                    f"[TASK:{task_id}] PARALLEL-CONSISTENCY: name-year rescue skipped due to error: {_cons_err}"
                                )

                            logger.info(
                                f"[TASK:{task_id}] PARALLEL-CONSISTENCY: Found {groups_found} parallel groups, fixed {consistency_fixed} citations"
                            )

                            def _should_keep_orphan_parallel(c):
                                if not isinstance(c, dict):
                                    return False
                                if not c.get("true_by_parallel", False):
                                    return False
                                if c.get("canonical_name") and c.get("canonical_url"):
                                    return True
                                if _is_toa_citation(c):
                                    return True

                                cit_txt = str(c.get("citation", "") or "")
                                is_proprietary = (
                                    (" WL " in cit_txt)
                                    or (" Lexis " in cit_txt)
                                    or (" U.S. Lexis " in cit_txt)
                                )
                                if not is_proprietary:
                                    return False

                                c_name = (c.get("extracted_case_name") or "").strip()
                                if (
                                    not c_name
                                    or c_name.upper() == "N/A"
                                    or (" v" not in c_name.lower())
                                    or len([t for t in c_name.split() if t]) < 3
                                ):
                                    return False

                                import re as _re_orphan
                                from src.utils.same_case import names_are_same_case as _orphan_sc

                                def _year_num_orphan(v):
                                    m = _re_orphan.search(r"\b(17|18|19|20)\d{2}\b", str(v or ""))
                                    return int(m.group(0)) if m else None

                                c_year = (
                                    _year_num_orphan(c.get("citation"))
                                    or _year_num_orphan(c.get("extracted_date"))
                                    or _year_num_orphan(c.get("canonical_date"))
                                )
                                for src in citation_lookup.values():
                                    if not isinstance(src, dict):
                                        continue
                                    if src.get("verified") != True:
                                        continue
                                    src_name = (
                                        src.get("extracted_case_name")
                                        or src.get("canonical_name")
                                        or ""
                                    ).strip()
                                    if not src_name or not _strong_case_name(src_name):
                                        continue
                                    if not _orphan_sc(src_name, c_name):
                                        continue
                                    # Source is verified: prefer canonical year.
                                    src_year = _year_num_orphan(src.get("canonical_date")) or _year_num_orphan(
                                        src.get("extracted_date")
                                    )
                                    if c_year is not None and src_year is not None and c_year != src_year:
                                        continue

                                    # Hydrate canonical evidence from verified sibling before orphan cleanup.
                                    if src.get("canonical_name") and not c.get("canonical_name"):
                                        c["canonical_name"] = src.get("canonical_name")
                                    if src.get("canonical_date") and not c.get("canonical_date"):
                                        c["canonical_date"] = src.get("canonical_date")
                                    if src.get("canonical_url") and not c.get("canonical_url"):
                                        c["canonical_url"] = src.get("canonical_url")
                                    if "_original_obj" in c:
                                        orig = c["_original_obj"]
                                        if getattr(orig, "canonical_name", None) is None and c.get("canonical_name"):
                                            orig.canonical_name = c.get("canonical_name")
                                        if getattr(orig, "canonical_date", None) is None and c.get("canonical_date"):
                                            orig.canonical_date = c.get("canonical_date")
                                        if getattr(orig, "canonical_url", None) is None and c.get("canonical_url"):
                                            orig.canonical_url = c.get("canonical_url")
                                    return True

                                return False

                            def _is_real_canonical_url(url):
                                """Check if URL is a real canonical URL (not Google search)."""
                                if not url:
                                    return False
                                url_str = str(url).lower()
                                return not (url_str.startswith('https://www.google.com') or 
                                           url_str.startswith('http://www.google.com'))

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
                                            # Keep propagated citations with canonical evidence or recoverable sibling match.
                                            if _should_keep_orphan_parallel(gc):
                                                logger.info(
                                                    f"[TASK:{task_id}] PARALLEL-ORPHAN: Preserved {gc.get('citation')} (recoverable proprietary parallel)"
                                                )
                                                continue
                                            gc["true_by_parallel"] = False
                                            # Also clear canonical data since source is gone
                                            # PRESERVE real canonical URLs - only clear if Google search URL
                                            existing_url = gc.get("canonical_url")
                                            gc["canonical_name"] = None
                                            gc["canonical_date"] = None
                                            if not _is_real_canonical_url(existing_url):
                                                gc["canonical_url"] = None
                                            else:
                                                logger.info(f"[TASK:{task_id}] PRESERVED real URL during orphan cleanup: {existing_url[:80]}...")
                                            if "_original_obj" in gc:
                                                orig = gc["_original_obj"]
                                                orig.true_by_parallel = False
                                                orig.canonical_name = None
                                                orig.canonical_date = None
                                                # Only clear URL if not real
                                                if not _is_real_canonical_url(getattr(orig, 'canonical_url', None)):
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
                                                    # Do NOT propagate true_by_parallel if source has Google search URL
                                                    upd_url = (updated.get("canonical_url") or updated.get("url") or "").strip()
                                                    upd_has_google = upd_url and (upd_url.startswith("https://www.google.com/search") or upd_url.startswith("http://www.google.com/search"))
                                                    if updated.get("true_by_parallel") and not cit.get(
                                                        "true_by_parallel"
                                                    ) and not upd_has_google:
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
                                                        # PRESERVE real canonical URLs
                                                        existing_url = cit.get("canonical_url")
                                                        cit["canonical_name"] = None
                                                        cit["canonical_date"] = None
                                                        if not _is_real_canonical_url(existing_url):
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
                                            # Keep propagated citations with canonical evidence or recoverable sibling match.
                                            if _should_keep_orphan_parallel(cit):
                                                logger.info(
                                                    f"[TASK:{task_id}] CLUSTER-ORPHAN: Preserved {cit.get('citation')} (recoverable proprietary parallel)"
                                                )
                                                continue
                                            cit["true_by_parallel"] = False
                                            # PRESERVE real canonical URLs
                                            existing_url = cit.get("canonical_url")
                                            cit["canonical_name"] = None
                                            cit["canonical_date"] = None
                                            if not _is_real_canonical_url(existing_url):
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
                                            # PRESERVE real canonical URLs
                                            existing_url = lookup_cit.get("canonical_url")
                                            lookup_cit["canonical_name"] = None
                                            lookup_cit["canonical_date"] = None
                                            if not _is_real_canonical_url(existing_url):
                                                lookup_cit["canonical_url"] = None
                                            # Also update original object if present
                                            if "_original_obj" in lookup_cit:
                                                orig = lookup_cit["_original_obj"]
                                                orig.true_by_parallel = False
                                                orig.canonical_name = None
                                                orig.canonical_date = None
                                                # PRESERVE real canonical URLs on original object
                                                if not _is_real_canonical_url(getattr(orig, 'canonical_url', None)):
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

                            # STEP 5: Google search URL → Unverified
                            # When canonical_url is a Google search, status must be unverified (not Verified or Verified by Parallel)
                            def _is_google_url(u):
                                if not u or not str(u).strip():
                                    return False
                                s = str(u).strip()
                                return s.startswith("https://www.google.com/search") or s.startswith("http://www.google.com/search")

                            google_downgraded = 0
                            for _c in citation_lookup.values():
                                if not isinstance(_c, dict):
                                    continue
                                url = (_c.get("canonical_url") or _c.get("url") or "").strip()
                                if not _is_google_url(url):
                                    continue
                                if _c.get("verified") == True:
                                    _c["verified"] = False
                                    _c["is_verified"] = False
                                    _c["verification_status"] = _c.get("verification_status") or "unverified"
                                    if "_original_obj" in _c:
                                        orig = _c["_original_obj"]
                                        orig.verified = False
                                        orig.is_verified = False
                                    google_downgraded += 1
                                    logger.info(
                                        f"[TASK:{task_id}] GOOGLE-URL: Downgraded verified {_c.get('citation')} to unverified"
                                    )
                                if _c.get("true_by_parallel", False):
                                    _c["true_by_parallel"] = False
                                    if "_original_obj" in _c:
                                        orig = _c["_original_obj"]
                                        orig.true_by_parallel = False
                                    google_downgraded += 1
                                    logger.info(
                                        f"[TASK:{task_id}] GOOGLE-URL: Cleared true_by_parallel from {_c.get('citation')}"
                                    )
                            for cluster in (clusters_list or []):
                                if not isinstance(cluster, dict):
                                    continue
                                for cit in cluster.get("citations", []):
                                    if not isinstance(cit, dict):
                                        continue
                                    url = (cit.get("canonical_url") or cit.get("url") or "").strip()
                                    if not _is_google_url(url):
                                        continue
                                    if cit.get("verified") == True:
                                        cit["verified"] = False
                                        cit["is_verified"] = False
                                        cit["verification_status"] = cit.get("verification_status") or "unverified"
                                        google_downgraded += 1
                                    if cit.get("true_by_parallel", False):
                                        cit["true_by_parallel"] = False
                                        google_downgraded += 1
                            if google_downgraded > 0:
                                logger.info(
                                    f"[TASK:{task_id}] GOOGLE-URL: Downgraded {google_downgraded} citations with Google search canonical URL to unverified"
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
                        from src.verification import apply_last_mile_cluster_display_sync
                        apply_last_mile_cluster_display_sync(citations_list, clusters_list)
                    except Exception as sync_err:
                        logger.warning(f"[TASK:{task_id}] Last-mile cluster display sync failed: {sync_err}")
                    
                    logger.info(f"[TASK:{task_id}] Display fields prepared for all clusters")

                    # FIX 2026-02-10: Final safety split - separate citations whose TEXT name
                    # differs from the cluster's canonical name.  This catches cases like
                    # "Trichell v. Midland" stuck inside a "Simon v. Eastern Kentucky" cluster
                    # after all prior merge passes.
                    if clusters_list and len(clusters_list) > 0:
                        import re as _re_split
                        from src.utils.date_utils import extract_year_from_citation as _year_from_cit
                        from src.utils.date_utils import extract_year_value as _year_val

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
                            # Determine dominant verified year in cluster (for mixed-year ejection).
                            _verified_years = []
                            for _c in cits:
                                if not isinstance(_c, dict):
                                    continue
                                _v = bool(
                                    _c.get("verified") is True
                                    or _c.get("verified") == "true"
                                    or _c.get("is_verified") is True
                                )
                                _u = bool(str(_c.get("canonical_url") or _c.get("url") or "").strip())
                                if _v and _u:
                                    _y = _year_val(_c.get("canonical_date")) or _year_from_cit(str(_c.get("citation") or ""))
                                    if _y:
                                        _verified_years.append(str(_y))
                            _cluster_verified_year = _verified_years[0] if _verified_years else ""
                            # Determine cluster's canonical first party
                            cluster_cn = cluster.get("canonical_name", "")
                            cluster_party = ""
                            if cluster_cn and " v. " in cluster_cn.lower():
                                parts = _re_split.split(r'\s+v\.?\s+', cluster_cn, maxsplit=1, flags=_re_split.IGNORECASE)
                                cluster_party = _norm_party(parts[0].strip().rstrip(',. ').split()[-1]) if parts else ""
                            keep = []
                            eject = []
                            for cit in cits:
                                if not isinstance(cit, dict):
                                    keep.append(cit)
                                    continue
                                ct = cit.get("citation", "")
                                ct_party = _first_party(ct)
                                # Also check extracted_case_name - citation text may be truncated
                                # e.g., "Madison, 1 Cranch 137" has ct_party="Madison" but ecn="Marbury v. Madison"
                                ecn = cit.get("extracted_case_name", "") or ""
                                ecn_party = _first_party(ecn) if " v. " in ecn else ""
                                _party_mismatch = bool(
                                    cluster_party
                                    and ct_party
                                    and not _parties_match(ct_party, cluster_party)
                                    and not _parties_match(ecn_party, cluster_party)
                                )
                                _cit_year = (
                                    _year_from_cit(str(ct))
                                    or _year_val(cit.get("extracted_date"))
                                    or _year_val(cit.get("canonical_date"))
                                )
                                _is_verified_cit = bool(
                                    (cit.get("verified") is True or cit.get("verified") == "true" or cit.get("is_verified") is True)
                                    and str(cit.get("canonical_url") or cit.get("url") or "").strip()
                                )
                                _is_parallel = bool(cit.get("true_by_parallel") is True or cit.get("true_by_parallel") == "true")
                                _year_mismatch = bool(
                                    _cluster_verified_year
                                    and _cit_year
                                    and str(_cluster_verified_year) != str(_cit_year)
                                    and (not _is_verified_cit or _is_parallel)
                                )
                                if _party_mismatch or _year_mismatch:
                                    if _year_mismatch and _is_parallel:
                                        # Do not keep year-mismatched citations as parallel to a different-year case.
                                        cit["true_by_parallel"] = False
                                        if not _is_verified_cit:
                                            cit["verified"] = False
                                            cit["is_verified"] = False
                                            cit["canonical_name"] = None
                                            cit["canonical_date"] = None
                                            cit["canonical_url"] = None
                                            cit["url"] = None
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

                    # Final structural safety split: ensure no late-stage re-mixed clusters
                    # (e.g., U.S. + WL + F. Supp. combined after downstream passes).
                    try:
                        clusters_list = apply_post_verify_cluster_splits(
                            clusters_list,
                            run_id=f"{task_id}:final",
                        )
                    except Exception as split_err:
                        logger.warning(f"[TASK:{task_id}] Final post-verify split failed: {split_err}")

                    # FINAL DISPLAY/IDENTITY GUARD (shared helper):
                    # one source of truth for submitted/verifying identity on unverified clusters.
                    try:
                        from src.utils.cluster_display_utils import (
                            finalize_cluster_for_response,
                        )
                        from src.utils.response_enrichment import (
                            apply_proprietary_display_fallback,
                            deduplicate_clusters_for_response,
                        )
                        apply_proprietary_display_fallback(citations_list)
                        for _cl in clusters_list or []:
                            if not isinstance(_cl, dict):
                                continue
                            apply_proprietary_display_fallback(_cl.get("citations") or [])
                            finalize_cluster_for_response(
                                _cl,
                                clean_names=True,
                                clear_unverified_canonical=True,
                                clear_unverified_citations=True,
                            )
                        clusters_list = deduplicate_clusters_for_response(clusters_list)
                    except Exception as _final_guard_err:
                        logger.warning(f"[TASK:{task_id}] Final display guard failed: {_final_guard_err}")

                    # Create final result with complete verification data (include cluster_sections for frontend)
                    try:
                        from src.utils.response_enrichment import compute_cluster_sections
                        cluster_sections = compute_cluster_sections(clusters_list)
                    except Exception as _cs_err:
                        logger.debug(f"[TASK:{task_id}] cluster_sections computation skipped: {_cs_err}")
                        cluster_sections = {}
                    meta = {
                        "processing_strategy": "synchronous_full_verification",
                        "processing_path": "worker_unified_pipeline",
                        "text_length": len(text) if text else 0,
                        "verification_completed": enable_verification,
                        "citation_count": len(citations_list),
                        "verified_count": verified_count,
                        "cluster_count": len(clusters_list),
                        "pipeline_metadata": pipeline_result.get("metadata", {}),
                    }
                    if enable_verification and len(citations_list) > 0 and verified_count == 0:
                        meta["verification_requested_but_none_matched"] = True
                        meta["verification_hint"] = "No citations were matched. Ensure COURTLISTENER_API_KEY is set in the worker environment (see worker logs)."
                    result = {
                        "success": True,
                        "citations": citations_list,
                        "clusters": clusters_list,
                        "cluster_sections": cluster_sections,
                        "task_id": task_id,
                        "metadata": meta,
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

                        # Broad coverage: regional reporters, state reporters, federal
                        citation_patterns = [
                            # Washington
                            r"\d+\s+Wn\.2d\s+\d+",
                            r"\d+\s+Wn\.\s+App\.\s+2d\s+\d+",
                            # Pacific
                            r"\d+\s+P\.3d\s+\d+",
                            r"\d+\s+P\.2d\s+\d+",
                            # Federal
                            r"\d+\s+U\.S\.\s+\d+",
                            r"\d+\s+F\.3d\s+\d+",
                            r"\d+\s+F\.2d\s+\d+",
                            r"\d+\s+F\.4th\s+\d+",
                            r"\d+\s+F\.\s*Supp\.\s*2d\s+\d+",
                            r"\d+\s+F\.\s*Supp\.\s*3d\s+\d+",
                            r"\d+\s+F\.\s*Supp\.\s+\d+",
                            # Regional: N.E., S.E., N.W., S.W., A., So.
                            r"\d+\s+N\.E\.2d\s+\d+",
                            r"\d+\s+N\.E\.3d\s+\d+",
                            r"\d+\s+N\.E\.\s+\d+",
                            r"\d+\s+S\.E\.2d\s+\d+",
                            r"\d+\s+S\.E\.\s+\d+",
                            r"\d+\s+N\.W\.2d\s+\d+",
                            r"\d+\s+N\.W\.\s+\d+",
                            r"\d+\s+S\.W\.2d\s+\d+",
                            r"\d+\s+S\.W\.3d\s+\d+",
                            r"\d+\s+S\.W\.\s+\d+",
                            r"\d+\s+A\.2d\s+\d+",
                            r"\d+\s+A\.3d\s+\d+",
                            r"\d+\s+A\.\s+\d+",
                            r"\d+\s+So\.2d\s+\d+",
                            r"\d+\s+So\.3d\s+\d+",
                            # Illinois
                            r"\d+\s+Ill\.\s*App\.\s*3d\s+\d+",
                            r"\d+\s+Ill\.\s*App\.\s*2d\s+\d+",
                            r"\d+\s+Ill\.\s*2d\s+\d+",
                            r"\d+\s+Ill\.\s+\d+",
                            # Virginia, California, New York, Ohio, Missouri, etc.
                            r"\d+\s+Va\.\s+\d+",
                            r"\d+\s+Va\.\s+App\.\s+\d+",
                            r"\d+\s+Cal\.\s*App\.\s*4th\s+\d+",
                            r"\d+\s+Cal\.\s*App\.\s*3d\s+\d+",
                            r"\d+\s+Cal\.\s*4th\s+\d+",
                            r"\d+\s+Cal\.\s*3d\s+\d+",
                            r"\d+\s+Cal\.\s*2d\s+\d+",
                            r"\d+\s+Cal\.\s+\d+",
                            r"\d+\s+N\.Y\.2d\s+\d+",
                            r"\d+\s+N\.Y\.3d\s+\d+",
                            r"\d+\s+N\.Y\.\s+\d+",
                            r"\d+\s+Ohio\s+St\.\s*3d\s+\d+",
                            r"\d+\s+Ohio\s+St\.\s*2d\s+\d+",
                            r"\d+\s+Ohio\s+App\.\s+\d+",
                            r"\d+\s+Mo\.\s+App\.\s+\d+",
                            r"\d+\s+Mo\.\s+\d+",
                            r"\d+\s+Tenn\.\s+\d+",
                            r"\d+\s+Tex\.\s+App\.\s+\d+",
                            r"\d+\s+Fla\.\s+\d+",
                            r"\d+\s+N\.J\.\s+\d+",
                            r"\d+\s+N\.J\.\s*Super\.\s+\d+",
                            r"\d+\s+Mass\.\s+App\.\s+[Cc]t\.\s+\d+",
                            r"\d+\s+Mass\.\s+\d+",
                            r"\d+\s+Ga\.\s+\d+",
                            r"\d+\s+N\.C\.\s+App\.\s+\d+",
                            r"\d+\s+N\.C\.\s+\d+",
                            r"\d+\s+Colo\.\s+App\.\s+\d+",
                            r"\d+\s+Colo\.\s+\d+",
                            r"\d+\s+Mich\.\s+App\.\s+\d+",
                            r"\d+\s+Mich\.\s+\d+",
                            r"\d+\s+Minn\.\s+\d+",
                            r"\d+\s+Wis\.\s*2d\s+\d+",
                            r"\d+\s+Wyo\.\s+\d+",
                            r"\d+\s+Idaho\s+\d+",
                            r"\d+\s+Or\.\s+App\.\s+\d+",
                            r"\d+\s+Or\.\s+\d+",
                            r"\d+\s+Mont\.\s+\d+",
                            r"\d+\s+Ala\.\s+\d+",
                            r"\d+\s+Conn\.\s+App\.\s+\d+",
                            r"\d+\s+Conn\.\s+\d+",
                            r"\d+\s+Md\.\s+App\.\s+\d+",
                            r"\d+\s+Md\.\s+\d+",
                            r"\d+\s+Pa\.\s+Super\.\s+\d+",
                            r"\d+\s+Pa\.\s+\d+",
                            r"\d+\s+Ind\.\s+App\.\s+\d+",
                            r"\d+\s+Ind\.\s+\d+",
                            r"\d+\s+Ariz\.\s+App\.\s+\d+",
                            r"\d+\s+Ariz\.\s+\d+",
                            r"\d+\s+N\.M\.\s+App\.\s+\d+",
                            r"\d+\s+N\.M\.\s+\d+",
                            r"\d+\s+Utah\s+App\.\s+\d+",
                            r"\d+\s+Utah\s+\d+",
                            r"\d+\s+Nev\.\s+\d+",
                            r"\d+\s+Haw\.\s+App\.\s+\d+",
                            r"\d+\s+Haw\.\s+\d+",
                            r"\d+\s+Alaska\s+\d+",
                            r"\d+\s+Kan\.\s+App\.\s*2d\s+\d+",
                            r"\d+\s+Kan\.\s+\d+",
                            r"\d+\s+Neb\.\s+App\.\s+\d+",
                            r"\d+\s+Neb\.\s+\d+",
                            r"\d+\s+Iowa\s+App\.\s+\d+",
                            r"\d+\s+Iowa\s+\d+",
                            r"\d+\s+S\.D\.\s+\d+",
                            r"\d+\s+N\.D\.\s+\d+",
                            r"\d+\s+La\.\s+App\.\s+\d+",
                            r"\d+\s+La\.\s+\d+",
                            r"\d+\s+Miss\.\s+App\.\s+\d+",
                            r"\d+\s+Miss\.\s+\d+",
                            r"\d+\s+Okla\.\s+Civ\.\s+App\.\s+\d+",
                            r"\d+\s+Okla\.\s+\d+",
                            r"\d+\s+Ark\.\s+App\.\s+\d+",
                            r"\d+\s+Ark\.\s+\d+",
                            r"\d+\s+Ky\.\s+App\.\s+\d+",
                            r"\d+\s+Ky\.\s+\d+",
                            r"\d+\s+S\.C\.\s+\d+",
                            r"\d+\s+Me\.\s+\d+",
                            r"\d+\s+Vt\.\s+\d+",
                            r"\d+\s+N\.H\.\s+\d+",
                            r"\d+\s+R\.I\.\s+\d+",
                            r"\d+\s+Del\.\s+\d+",
                            r"\d+\s+D\.C\.\s+\d+",
                            r"\d+\s+W\.\s*Va\.\s+\d+",
                            # WL/LEXIS (optional - often need docket context)
                            r"\d+\s+WL\s+\d+",
                        ]

                        seen = set()
                        citations_found = []
                        for pattern in citation_patterns:
                            for match in re.findall(pattern, text, re.IGNORECASE):
                                if match not in seen:
                                    seen.add(match)
                                    citations_found.append(
                                        {
                                            "citation": match,
                                            "case_name": "N/A",
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
                except Exception as progress_err:
                    logger.debug(f"[TASK:{task_id}] Final progress/complete update skipped: {progress_err}")
            else:
                result = {"status": "failed", "task_id": task_id, "error": result.get("error", "Processing failed")}

        else:
            # File inputs: extract text then run full pipeline with verification+clustering
            logger.info(f"[TASK:{task_id}] Using FULL PIPELINE for file input")
            try:
                vm.update_progress(task_id, processed=1, total=4, message="Extracting text from file")
            except Exception as progress_err:
                logger.debug(f"[TASK:{task_id}] File-path initial progress update skipped: {progress_err}")

            text = ""
            try:
                file_path = input_data.get("file_path")
                if not file_path:
                    raise ValueError("Missing file_path in input_data")
                # Use same extractor as sync path so citation counts match (sync uses unified_text_extractor)
                from src.unified_text_extractor import extract_text_from_file_unified
                text, _method = extract_text_from_file_unified(file_path, verbose=True)
                if text and len(text.strip()) > 0:
                    from src.utils.text_normalizer import normalize_text
                    text = normalize_text(text)
                logger.info(f"[TASK:{task_id}] Extracted {len(text)} characters from file (unified extractor)")

                # Update progress after text extraction
                logger.info(f"[TASK:{task_id}] About to extract and cluster citations...")
                vm.update_progress(task_id, processed=2, total=4, message="Extracting and clustering citations")

            except Exception as e:
                logger.error(f"[TASK:{task_id}] File text extraction failed: {e}")
                result = {"status": "failed", "task_id": task_id, "error": f"File text extraction failed: {str(e)}"}
                return result

            try:

                # Extract enable_verification flag from input_data (same normalization as text path)
                raw_ev = input_data.get("enable_verification", True)
                if isinstance(raw_ev, str):
                    enable_verification = raw_ev.strip().lower() in ("true", "1", "yes", "on")
                else:
                    enable_verification = bool(raw_ev)
                logger.info(f"[TASK:{task_id}] enable_verification flag (file): {enable_verification} (raw: {raw_ev!r})")

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

                # Call pipeline directly with asyncio; use same timeout as text path to avoid runaway runs
                import asyncio

                pipeline_timeout = int(os.environ.get("PIPELINE_TIMEOUT_SECONDS", "600"))
                try:
                    pipeline_result = asyncio.run(
                        asyncio.wait_for(
                            process_citations_unified(
                                text,
                                processing_mode="enhanced_sync",
                                enable_parallel_verification=enable_verification,
                                enable_verification=enable_verification,
                                progress_callback=file_progress_callback,
                            ),
                            timeout=float(pipeline_timeout),
                        )
                    )
                except asyncio.TimeoutError:
                    logger.error(f"[TASK:{task_id}] File pipeline timed out after {pipeline_timeout}s")
                    try:
                        vm.update_progress(
                            task_id, processed=0, total=1, message="Pipeline timed out; document may be too large"
                        )
                    except Exception:
                        pass
                    result = {
                        "status": "failed",
                        "task_id": task_id,
                        "error": f"Processing timed out after {pipeline_timeout} seconds. The document may be too large.",
                        "citations": [],
                        "clusters": [],
                        "success": False,
                    }
                    return result
                logger.info(f"[TASK:{task_id}] Unified pipeline processing completed (file path)")
            except Exception as e:
                logger.error(f"[TASK:{task_id}] Full pipeline failed: {e}")
                result = {"status": "failed", "task_id": task_id, "error": f"Pipeline failed: {str(e)}"}
                return result

            citations_raw = pipeline_result.get("citations", [])
            clusters = pipeline_result.get("clusters", [])
            # Normalize citations to dicts and ensure extracted_case_name/extracted_date are always set (for "from document" display)
            citations = []
            for c in citations_raw:
                if isinstance(c, dict):
                    cit = dict(c)
                else:
                    cit = (c.to_dict() if hasattr(c, "to_dict") and callable(getattr(c, "to_dict")) else {})
                cit.setdefault("extracted_case_name", cit.get("extracted_case_name") or "N/A")
                cit.setdefault("extracted_date", cit.get("extracted_date") or "N/A")
                citations.append(cit)
            names_from_doc = sum(1 for c in citations if (c.get("extracted_case_name") or "").strip() not in ("", "N/A"))
            if len(citations) > 0 and names_from_doc == 0:
                logger.warning(
                    f"[TASK:{task_id}] No case names from document (all N/A). "
                    "Check pipeline extraction: _extract_citations_unified may be failing (regex fallback has no names) or enhancement loop not finding names."
                )
            # Diagnostic: compare sync vs async pipeline output (see docs/PIPELINE_ENTRY_POINTS.md)
            logger.info(
                f"[SYNC-ASYNC-DIAG] ASYNC (file) pipeline out: len(text)={len(text)}, "
                f"len(citations)={len(citations)}, len(clusters)={len(clusters)}"
            )
            # Safety net: pipeline sometimes returns citations but 0 clusters (e.g. clustering filter removes all).
            # Build one cluster per citation so the frontend shows "X Cases Found" and cards instead of empty sections.
            if citations and not clusters:
                logger.warning(
                    f"[TASK:{task_id}] Pipeline returned {len(citations)} citations but 0 clusters - building one cluster per citation"
                )
                clusters = []
                for i, c in enumerate(citations, 1):
                    if isinstance(c, dict):
                        cit = c
                    else:
                        cit = (c.to_dict() if hasattr(c, "to_dict") and callable(getattr(c, "to_dict")) else {})
                    ct = cit.get("citation", "") or getattr(c, "citation", "")
                    ecn = cit.get("extracted_case_name") or cit.get("canonical_name") or "N/A"
                    clusters.append({
                        "cluster_id": f"cluster_file_{i}",
                        "cluster_key": ct[:200] if ct else f"c_{i}",
                        "citations": [cit],
                        "cluster_members": [ct] if ct else [],
                        "cluster_size": 1,
                        "size": 1,
                        "cluster_case_name": ecn,
                        "submitted_display_name": ecn,
                        "extracted_case_name": ecn,
                        "canonical_name": cit.get("canonical_name"),
                        "canonical_url": cit.get("canonical_url"),
                        "verified": bool(cit.get("verified", False)),
                        "verification_status": "verified" if cit.get("verified") else "unverified",
                        "metadata": {},
                    })

            # NOTE: Fallback verification already runs inside verify_citations_batch()
            # (Phase 4.75 enhanced_batch_fallback). No need for a second fallback here.

            try:
                total = max(4, len(citations) or 4)
                vm.update_progress(task_id, processed=3, total=total, message="Verifying citations and finalizing")
            except Exception as progress_err:
                logger.debug(f"[TASK:{task_id}] File-path finalizing progress update skipped: {progress_err}")

            # FIX 2026-02-09: Re-annotate mismatch flags after pipeline post-processing
            try:
                from src.utils.mismatch_utils import annotate_mismatch_flags
                annotate_mismatch_flags(citations, clusters, name_threshold=0.4, year_tolerance=0)
                logger.info(f"[TASK:{task_id}] Re-annotated mismatch flags (file path)")
            except Exception as mismatch_err:
                logger.warning(f"[TASK:{task_id}] Mismatch re-annotation failed: {mismatch_err}")

            # FIX 2026-02-24: Add cluster_sections for frontend display categorization
            from src.utils.response_enrichment import compute_cluster_sections
            
            verified_count_file = sum(
                1 for c in citations
                if isinstance(c, dict) and c.get("verified", False)
            )
            pipeline_meta = pipeline_result.get("metadata") or {}
            clustering_ver = pipeline_meta.get("clustering_version") or "unknown"
            meta_file = {
                "processing_strategy": "full_async_with_verification",
                "text_length": len(text),
                "citation_count": len(citations),
                "verified_count": verified_count_file,
                "cluster_count": len(clusters),
                "verification_completed": enable_verification,
                "clustering_version": clustering_ver,
            }
            if enable_verification and len(citations) > 0 and verified_count_file == 0:
                meta_file["verification_requested_but_none_matched"] = True
                meta_file["verification_hint"] = (
                    "No citations were matched. Ensure COURTLISTENER_API_KEY is set in the worker environment (see worker logs)."
                )
            result = {
                "status": "completed",
                "task_id": task_id,
                "citations": citations,
                "clusters": clusters,
                "cluster_sections": compute_cluster_sections(clusters),
                "metadata": meta_file,
            }

            try:
                vm.complete(task_id, result)
            except Exception as complete_err:
                logger.debug(f"[TASK:{task_id}] File-path complete update skipped: {complete_err}")

            # Diagnostic: log clustering version and sample clusters (Kustura/Perry) for debugging
            logger.info(
                f"[TASK:{task_id}] CLUSTER-DIAG clustering_version={clustering_ver} clusters={len(clusters)}"
            )
            for i, cl in enumerate(clusters or []):
                if not isinstance(cl, dict):
                    continue
                name = (
                    (cl.get("cluster_case_name") or cl.get("submitted_display_name") or cl.get("verifying_display_name") or "")
                ).strip()
                cits = cl.get("citations") or cl.get("citation_objects") or []
                if not name:
                    continue
                name_lower = name.lower()
                if "kustura" in name_lower or ("perry" in name_lower and "beverage" in name_lower):
                    cite_texts = [
                        (c.get("citation") or c.get("text") or "")[:50]
                        for c in cits
                        if isinstance(c, dict)
                    ]
                    logger.info(
                        f"[TASK:{task_id}] CLUSTER-DIAG cluster_id={cl.get('cluster_id')} name={name[:50]} "
                        f"citations={len(cits)} refs={cite_texts}"
                    )

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

                from src.config import REDIS_URL
                redis_client = Redis.from_url(REDIS_URL)

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
        except Exception as fail_err:
            logger.debug(f"[TASK:{task_id}] Timeout fail update skipped: {fail_err}")
        out = {
            "status": "failed",
            "error": error_msg,
            "task_id": task_id,
            "processing_time": time.time() - start_time if "start_time" in locals() else None,
            "error_type": "timeout",
        }
        try:
            from src.config import IS_PRODUCTION
            if not IS_PRODUCTION:
                out["stack_trace"] = traceback.format_exc()
        except Exception as stack_err:
            logger.debug(f"[TASK:{task_id}] Timeout stack-trace attachment skipped: {stack_err}")
        return out
    except Exception as e:
        error_msg = f"Task {task_id} failed: {str(e)}"
        logger.error(f"[TASK:{task_id}] {error_msg}", exc_info=True)
        try:
            vm.fail(task_id, error_msg)
        except Exception as fail_err:
            logger.debug(f"[TASK:{task_id}] Error fail update skipped: {fail_err}")
        out = {
            "status": "failed",
            "error": error_msg,
            "task_id": task_id,
            "processing_time": time.time() - start_time if "start_time" in locals() else None,
            "error_type": type(e).__name__,
            "exception_type": type(e).__name__,
        }
        try:
            from src.config import IS_PRODUCTION
            if not IS_PRODUCTION:
                out["stack_trace"] = traceback.format_exc()
        except Exception as stack_err:
            logger.debug(f"[TASK:{task_id}] Error stack-trace attachment skipped: {stack_err}")
        return out
    finally:
        if platform.system() != "Windows" and timeout_set:
            try:
                signal.alarm(0)  # type: ignore[attr-defined]
            except (AttributeError, OSError):
                logger.debug(f"[TASK:{task_id}] Unable to clear alarm in finally block")



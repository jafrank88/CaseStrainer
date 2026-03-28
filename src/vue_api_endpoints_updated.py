"""
Vue API Endpoints Blueprint
Main API routes for the CaseStrainer application
"""

import os
from src.config import (
    WEBSEARCH_TIMEOUT,
    FILE_PROCESSING_TIMEOUT_MINUTES,
    REDIS_URL,
    SYNC_REQUESTS_AS_ASYNC,
    ANALYZE_ASYNC_ONLY,
    ANALYZE_ALLOW_SYNC_OVERRIDE,
)

import sys
import uuid
import logging
import traceback
import time
import json
import copy
from datetime import datetime
import re
import html
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify, current_app, Response
from werkzeug.utils import secure_filename
from src.api.services.citation_service import CitationService
from src.database_manager import get_database_manager
from src.extraction import extract_case_name_from_strict_context
from src.utils.strict_context_isolator import (
    find_all_citation_positions,
    get_strict_context_for_citation,
)
import threading
from src.schemas import normalize_citation_dict, normalize_cluster_dict
from src.utils.response_enrichment import (
    extract_display_base_citation,
    compute_citation_score_and_similarity,
    build_fallback_clusters,
    deduplicate_cluster_citations,
    enrich_citations_with_cluster_members,
    deduplicate_clusters_for_response,
    merge_clusters_by_shared_real_canonical_url,
    apply_proprietary_display_fallback,
    compute_cluster_sections,
)
from src.utils.verification_display_utils import is_effectively_verified_citation
from src.utils.cluster_display_utils import finalize_cluster_for_response
from src.utils.cluster_postprocess_pipeline import apply_post_verify_cluster_splits
from src.metrics import (
    record_document,
    record_citations,
    get_daily_counts,
    get_totals,
    get_counts_last_n_days,
)

from src.rq_worker import process_citation_task_direct

# UnifiedInputProcessor is imported locally where needed to avoid startup issues

logger = logging.getLogger(__name__)

vue_api = Blueprint("vue_api", __name__)

citation_service = CitationService()

from src.api.routes import register_all_routes

register_all_routes(vue_api)


from src.rate_limiter import rate_limit


def _enforce_async_only_mode(force_mode, request_id: str, source: str):
    """
    Enforce async-only analyze mode when configured.
    Keeps an optional sync override for controlled debugging.
    """
    requested = (str(force_mode).strip().lower() if force_mode is not None else None) or None
    if not ANALYZE_ASYNC_ONLY:
        return requested
    if requested == "sync":
        if ANALYZE_ALLOW_SYNC_OVERRIDE:
            logger.warning(
                f"[Request {request_id}] Async-only enabled but allowing sync override for {source} (debug mode)"
            )
            return "sync"
        logger.info(f"[Request {request_id}] Async-only mode: overriding sync request to async for {source}")
        return "async"
    if requested in (None, "", "auto"):
        return "async"
    # Keep explicit async; normalize unknown values to async for safety.
    return "async" if requested not in ("async",) else requested


def _analyze_impl(request):
    """
    Main analysis implementation: file, JSON, form, URL. Called by api.routes.analyze via analyze_service.
    """
    # Generate initial request_id (will be replaced if client provides one)
    request_id = str(uuid.uuid4())

    if _is_test_environment_request(request):
        error_msg = "Test environment detected. Please use the production interface."
        logger.warning(f"[Request {request_id}] Test environment request detected and rejected")
        return (
            jsonify(
                {
                    "error": error_msg,
                    "citations": [],
                    "clusters": [],
                    "request_id": request_id,
                    "success": False,
                    "metadata": {
                        "rejected_reason": "test_environment_detected",
                        "user_agent": request.headers.get("User-Agent", "unknown"),
                        "referer": request.headers.get("Referer", "unknown"),
                    },
                }
            ),
            403,
        )

    logger.info(f"=== ANALYZE ENDPOINT CALLED [Request ID: {request_id}] ===")
    logger.info(f"[Request {request_id}] Method: {request.method}")
    logger.info(f"[Request {request_id}] URL: {request.url}")
    logger.info(f"[Request {request_id}] Content-Type: {request.content_type}")

    start_time = time.time()
    metadata = {
        "request_id": request_id,
        "endpoint": "/analyze",
        "timestamp": datetime.utcnow().isoformat(),
        "processing_mode": "unknown",
        "input_type": "unknown",
        "input_size": len(request.data) if request.data else 0,
        "content_type": request.content_type or "not_specified",
    }

    # Initialize force_mode parameter
    force_mode = None
    # Initialize enable_verification parameter (default to True for end users - can be disabled for testing)
    enable_verification = True
    # Precomputed result (used to harmonize early-return paths)
    precomputed_result = None

    try:
        if True:
            # Keep placeholder branch for historical diff stability.
            # Intentionally no-op.
            logger.debug(f"[Request {request_id}] Placeholder bootstrap branch executed")

        # Best-effort: record one document submission for this request
        try:
            record_document()
        except Exception as record_err:
            logger.debug(f"[Request {request_id}] record_document skipped: {record_err}")

        if request.files:
            logger.info(f"[Request {request_id}] Files received: {[f.filename for f in request.files.values()]}")

        service = CitationService()

        progress_steps = [
            {"name": "Initializing...", "progress": 5, "message": "Starting document analysis..."},
            {"name": "Extract", "progress": 15, "message": "Extracting citations from document..."},
            {"name": "Enhance", "progress": 35, "message": "Enhancing citation data with case names..."},
            {"name": "Parallel", "progress": 50, "message": "Detecting parallel citations..."},
            {"name": "Filter", "progress": 65, "message": "Removing false positive citations..."},
            {"name": "Verify", "progress": 75, "message": "Verifying citations with external sources..."},
            {"name": "Cluster", "progress": 85, "message": "Creating citation clusters..."},
            {"name": "Finalize", "progress": 95, "message": "Finalizing results..."},
        ]
        # Initialize progress manager (SSEProgressManager) and start progress for this request
        try:
            from src.unified_input_processor import get_progress_manager

            progress_tracker = get_progress_manager()
            # Use the correct method name and store the task ID for later use
            # For sync processing, create tracker directly with request_id to avoid mapping issues
            # Use 100 steps for percentage-based tracking (0-100%)
            if progress_tracker is not None:
                task_id = progress_tracker.start_task(100, task_id_override=request_id)
        except Exception as _e:
            logger.warning(f"[Request {request_id}] Progress manager initialization failed: {_e}")
            progress_tracker = None

        json_data = None
        if request.data and request.is_json:
            try:
                json_data = request.get_json(silent=True)
                if json_data:
                    # Check if client provided a request_id for progress tracking
                    if "client_request_id" in json_data:
                        request_id = json_data["client_request_id"]
                        logger.info(f"[Request {request_id}] Using client-provided request_id for progress tracking")
                        # EARLY: Start progress and register verification so polling by client_request_id returns 200
                        try:
                            # Start progress under the client-provided ID (in addition to any earlier default)
                            try:
                                # Ensure progress is started for the client-provided ID
                                if progress_tracker is not None and request_id not in progress_tracker.active_tasks:
                                    task_id = progress_tracker.start_task(100, task_id_override=request_id)
                            except Exception as __e:
                                logger.warning(f"[Request {request_id}] Progress start failed: {__e}")
                            from src.verification_manager import VerificationManager

                            vm = VerificationManager()
                            total_cites = 0
                            vm.register_verification(request_id, request_id, total_cites)
                            logger.info(
                                f"[Request {request_id}] Early progress + verification registered for JSON input"
                            )
                        except Exception as _e:
                            logger.warning(f"[Request {request_id}] Early JSON verification registration failed: {_e}")

                    sanitized_data = {}
                    for k, v in json_data.items():
                        if isinstance(v, str) and len(v) > 100:
                            sanitized_data[k] = f"[content of length {len(v)}]"
                        else:
                            sanitized_data[k] = v
            except Exception as e:
                logger.warning(f"[Request {request_id}] Failed to parse JSON data: {str(e)}")

        input_data = None
        input_type = None

        if "file" in request.files and request.files["file"].filename:
            logger.info(f"[Request {request_id}] Processing file upload")
            logger.info(
                f"[Request {request_id}] File details: name={request.files['file'].filename}, size={request.files['file'].content_length}, type={request.files['file'].content_type}"
            )

            # Extract force_mode parameter for file uploads
            force_mode = request.form.get("force_mode")
            if force_mode == "sync" and SYNC_REQUESTS_AS_ASYNC:
                force_mode = "async"
                logger.info(f"[Request {request_id}] SYNC_REQUESTS_AS_ASYNC: treating sync as async (enqueue, return task_id)")
            force_mode = _enforce_async_only_mode(force_mode, request_id, "file_upload")
            logger.info(f"[Request {request_id}] DEBUG: force_mode from file form: '{force_mode}'")
            logger.info(f"[Request {request_id}] DEBUG: form keys: {list(request.form.keys())}")
            if force_mode:
                logger.info(f"[Request {request_id}] User requested force_mode='{force_mode}' for file upload")

            # EARLY: Register verification so client_request_id polling returns 200 immediately
            try:
                from src.verification_manager import VerificationManager

                vm = VerificationManager()
                client_request_id = request.form.get("client_request_id")
                total_cites = 0
                if client_request_id:
                    vm.register_verification(client_request_id, request_id, total_cites)
                vm.register_verification(request_id, request_id, total_cites)
                logger.info(f"[Request {request_id}] Early verification registered (client_id={client_request_id})")
            except Exception as _e:
                logger.warning(f"[Request {request_id}] Early verification registration failed: {_e}")

            file_obj = request.files["file"]
            input_data = {
                "type": "file",
                "file": file_obj,
                "filename": file_obj.filename,
                "content_type": file_obj.content_type or "application/octet-stream",
                "file_size": getattr(file_obj, "content_length", 0) or 0,
            }
            input_type = "file"
            metadata.update(
                {
                    "input_type": "file",
                    "filename": file_obj.filename,
                    "content_type": file_obj.content_type or "application/octet-stream",
                    "file_size": getattr(file_obj, "content_length", 0) or 0,
                }
            )

            # Check if file should be processed immediately (sync mode)
            if force_mode == "sync" or (
                force_mode != "async" and service.should_process_immediately(input_data, force_mode=force_mode)
            ):
                logger.info(f"[Request {request_id}] Processing file immediately via UnifiedInputProcessor")
                try:
                    from src.unified_input_processor import UnifiedInputProcessor

                    uip = UnifiedInputProcessor()

                    # Pass file object and filename so processor can validate extension and extract (do not pass raw bytes)
                    file_input = {"file": file_obj, "filename": file_obj.filename or "unknown"}
                    result = uip.process_any_input(
                        file_input,
                        "file",
                        request_id,
                        source_name="file_upload",
                        enable_verification=enable_verification,
                        force_mode=force_mode,
                    )
                    result["request_id"] = request_id
                    if "metadata" not in result:
                        result["metadata"] = {}
                    result["metadata"].update(
                        {
                            "processing_mode": "immediate",
                            "input_type": "file",
                            "filename": file_obj.filename,
                            "file_size": getattr(file_obj, "content_length", 0) or 0,
                        }
                    )
                    precomputed_result = result
                    logger.info(f"[Request {request_id}] File processed immediately in sync mode")
                except Exception as e:
                    logger.error(f"[Request {request_id}] Error in immediate file processing: {str(e)}", exc_info=True)
                    # Fall back to async processing if immediate fails

        elif request.is_json or json_data:
            logger.info(f"[Request {request_id}] Processing JSON input")
            logger.info(
                f"[Request {request_id}] request.is_json: {request.is_json}, json_data exists: {json_data is not None}"
            )
            # Be tolerant to malformed JSON - don't raise BadRequest here
            data = json_data or request.get_json(silent=True)
            logger.info(
                f"[Request {request_id}] Initial data from get_json: {type(data)}, keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}"
            )
            if data is None:
                logger.info(f"[Request {request_id}] JSON data is None, trying fallback parsing...")
                # Fallback: try to decode raw body as JSON or URL string
                try:
                    raw_body = request.data.decode("utf-8") if request.data else ""
                    logger.info(f"[Request {request_id}] Raw body length: {len(raw_body)}")
                    if raw_body:
                        import json as _json

                        try:
                            data = _json.loads(raw_body)
                            logger.info(f"[Request {request_id}] Successfully parsed JSON from raw body")
                        except Exception as parse_error:
                            logger.warning(
                                f"[Request {request_id}] JSON parse failed: {parse_error}, trying as URL string..."
                            )
                            # If body is a plain URL string, accept it
                            raw_trim = raw_body.strip().strip('"')
                            if raw_trim.startswith(("http://", "https://")):
                                data = {"type": "url", "url": raw_trim}
                                logger.info(f"[Request {request_id}] Detected URL string: {raw_trim[:100]}")
                            else:
                                data = {}
                                logger.warning(
                                    f"[Request {request_id}] Raw body doesn't look like URL: {raw_trim[:100]}"
                                )
                    else:
                        data = {}
                        logger.warning(f"[Request {request_id}] Raw body is empty")
                except Exception as fallback_error:
                    logger.error(f"[Request {request_id}] Fallback parsing failed: {fallback_error}")
                    data = {}

            if data and isinstance(data, dict):
                logger.info(f"[Request {request_id}] JSON data keys: {list(data.keys())}")
                logger.info(
                    f"[Request {request_id}] JSON data type: {data.get('type')}, has url: {bool(data.get('url'))}, has text: {bool(data.get('text'))}"
                )

                # Accept explicit type=url, or infer URL when only 'url' provided
                # Check for URL: explicit type='url' OR url field present without text field
                is_url_type = str(data.get("type", "")).lower() == "url"
                has_url = bool(data.get("url"))
                has_text = bool(data.get("text"))

                logger.info(
                    f"[Request {request_id}] URL detection: is_url_type={is_url_type}, has_url={has_url}, has_text={has_text}"
                )

                if (is_url_type and has_url) or (has_url and not has_text):
                    input_data = data["url"]
                    input_type = "url"
                    logger.info(
                        f"[Request {request_id}] URL request detected: {input_data[:100] if len(input_data) > 100 else input_data}"
                    )
                    metadata.update({"input_type": "url", "url": data["url"]})

                    # Extract enable_verification parameter for URL inputs
                    enable_verification = data.get("enable_verification")
                    if enable_verification is not None:
                        # Convert to boolean if needed
                        if isinstance(enable_verification, str):
                            enable_verification = enable_verification.lower() in ("true", "1", "yes", "on")
                        logger.info(
                            f"[Request {request_id}] User requested enable_verification={enable_verification} for URL"
                        )
                    else:
                        enable_verification = True  # Default to True for end users - can be disabled for testing
                        logger.info(
                            f"[Request {request_id}] Using default enable_verification={enable_verification} for URL"
                        )

                    # Extract force_mode/processing_mode parameter for URL inputs
                    # Check both 'force_mode' and 'processing_mode' for compatibility
                    requested_mode = data.get("force_mode") or data.get("processing_mode")
                    logger.info(
                        f"[Request {request_id}] URL detected, checking processing_mode. force_mode={data.get('force_mode')}, processing_mode={data.get('processing_mode')}, requested_mode={requested_mode}"
                    )
                    if requested_mode:
                        # Map 'sync' to force_mode='sync', 'async' to force_mode='async'
                        if requested_mode.lower() == "sync":
                            force_mode = "async" if SYNC_REQUESTS_AS_ASYNC else "sync"
                            if SYNC_REQUESTS_AS_ASYNC:
                                logger.info(f"[Request {request_id}] SYNC_REQUESTS_AS_ASYNC: treating URL sync as async")
                            else:
                                logger.info(f"[Request {request_id}] User requested sync mode for URL")
                        elif requested_mode.lower() == "async":
                            force_mode = "async"
                            logger.info(f"[Request {request_id}] User requested async mode for URL")
                        else:
                            logger.info(
                                f"[Request {request_id}] User requested processing_mode='{requested_mode}' for URL (will use auto-routing)"
                            )
                    force_mode = _enforce_async_only_mode(force_mode, request_id, "json_url")
                elif data.get("type") == "text" and data.get("text"):
                    text_data = data["text"]
                    input_dict = {"type": "text", "text": text_data}

                    # Extract enable_verification parameter
                    enable_verification = data.get("enable_verification")
                    if enable_verification is not None:
                        # Convert to boolean if needed
                        if isinstance(enable_verification, str):
                            enable_verification = enable_verification.lower() in ("true", "1", "yes", "on")
                        logger.info(f"[Request {request_id}] User requested enable_verification={enable_verification}")
                    else:
                        enable_verification = True  # Default to True for end users - can be disabled for testing
                        logger.info(f"[Request {request_id}] Using default enable_verification={enable_verification}")

                    # Extract force_mode parameter
                    force_mode = data.get("force_mode")
                    if force_mode == "sync" and SYNC_REQUESTS_AS_ASYNC:
                        force_mode = "async"
                        logger.info(f"[Request {request_id}] SYNC_REQUESTS_AS_ASYNC: treating JSON text sync as async")
                    force_mode = _enforce_async_only_mode(force_mode, request_id, "json_text")
                    if force_mode:
                        logger.info(f"[Request {request_id}] User requested force_mode='{force_mode}' for JSON text")

                    if force_mode != "async" and service.should_process_immediately(input_dict, force_mode=force_mode):
                        logger.info(
                            f"[Request {request_id}] Processing JSON text immediately via UnifiedInputProcessor"
                        )
                        try:
                            from src.unified_input_processor import UnifiedInputProcessor

                            uip = UnifiedInputProcessor()
                            result = uip.process_any_input(
                                text_data,
                                "text",
                                request_id,
                                source_name="json_text",
                                enable_verification=enable_verification,
                                force_mode=force_mode,
                            )
                            result["request_id"] = request_id
                            if "metadata" not in result:
                                result["metadata"] = {}
                            result["metadata"].update(
                                {"processing_mode": "immediate", "input_type": "text", "text_length": len(text_data)}
                            )
                            precomputed_result = result
                        except Exception as e:
                            logger.error(
                                f"[Request {request_id}] Error in immediate processing: {str(e)}", exc_info=True
                            )

                    input_data = text_data
                    input_type = "text"
                    metadata.update({"input_type": "text", "text_length": len(text_data)})
                elif data.get("text"):  # Legacy format
                    text_data = data["text"]
                    input_dict = {"type": "text", "text": text_data}

                    # Extract enable_verification parameter
                    enable_verification = data.get("enable_verification")
                    if enable_verification is not None:
                        # Convert to boolean if needed
                        if isinstance(enable_verification, str):
                            enable_verification = enable_verification.lower() in ("true", "1", "yes", "on")
                        logger.info(f"[Request {request_id}] User requested enable_verification={enable_verification}")
                    else:
                        enable_verification = True  # Default to True for end users - can be disabled for testing
                        logger.info(f"[Request {request_id}] Using default enable_verification={enable_verification}")

                    # Extract force_mode parameter
                    force_mode = data.get("force_mode")
                    if force_mode == "sync" and SYNC_REQUESTS_AS_ASYNC:
                        force_mode = "async"
                        logger.info(f"[Request {request_id}] SYNC_REQUESTS_AS_ASYNC: treating legacy JSON sync as async")
                    force_mode = _enforce_async_only_mode(force_mode, request_id, "json_text_legacy")
                    if force_mode:
                        logger.info(
                            f"[Request {request_id}] User requested force_mode='{force_mode}' for legacy JSON text"
                        )

                    if force_mode != "async" and service.should_process_immediately(input_dict, force_mode=force_mode):
                        logger.info(
                            f"[Request {request_id}] Processing legacy JSON text immediately via UnifiedInputProcessor"
                        )
                        try:
                            from src.unified_input_processor import UnifiedInputProcessor

                            uip = UnifiedInputProcessor()
                            result = uip.process_any_input(
                                text_data,
                                "text",
                                request_id,
                                source_name="json_text_legacy",
                                enable_verification=enable_verification,
                                force_mode=force_mode,
                            )
                            result["request_id"] = request_id
                            if "metadata" not in result:
                                result["metadata"] = {}
                            result["metadata"].update(
                                {"processing_mode": "immediate", "input_type": "text", "text_length": len(text_data)}
                            )
                            precomputed_result = result
                        except Exception as e:
                            logger.error(
                                f"[Request {request_id}] Error in immediate processing: {str(e)}", exc_info=True
                            )

                    input_data = text_data
                    input_type = "text"
                    metadata.update({"input_type": "text", "text_length": len(text_data)})
                else:
                    # Defensive: if payload has neither text nor url
                    logger.warning(
                        f"[Request {request_id}] JSON payload missing 'text' or 'url' fields: {list(data.keys())}"
                    )
                    return (
                        jsonify(
                            {
                                "error": 'Invalid JSON payload. Provide either {"type":"text","text":"..."} or {"type":"url","url":"https://..."}.',
                                "request_id": request_id,
                                "success": False,
                            }
                        ),
                        400,
                    )

        elif request.form:
            logger.info(f"[Request {request_id}] Processing form input")

            # Extract force_mode parameter for sync/async override
            force_mode = request.form.get("force_mode")
            if force_mode == "sync" and SYNC_REQUESTS_AS_ASYNC:
                force_mode = "async"
                logger.info(f"[Request {request_id}] SYNC_REQUESTS_AS_ASYNC: treating sync as async")
            force_mode = _enforce_async_only_mode(force_mode, request_id, "form")
            logger.info(f"[Request {request_id}] DEBUG: force_mode from form: '{force_mode}'")
            logger.info(f"[Request {request_id}] DEBUG: form keys: {list(request.form.keys())}")
            if force_mode:
                logger.info(f"[Request {request_id}] User requested force_mode='{force_mode}'")

            # Extract enable_verification parameter
            enable_verification = request.form.get("enable_verification")
            if enable_verification is not None:
                # Convert string to boolean if needed
                if isinstance(enable_verification, str):
                    enable_verification = enable_verification.lower() in ("true", "1", "yes", "on")
                logger.info(f"[Request {request_id}] User requested enable_verification={enable_verification}")
            else:
                enable_verification = True  # Default to True for end users - can be disabled for testing
                logger.info(f"[Request {request_id}] Using default enable_verification={enable_verification}")

            if "url" in request.form:
                input_data = request.form["url"]
                input_type = "url"
                metadata.update({"input_type": "url", "url": request.form["url"]})
            elif "text" in request.form:
                input_data = request.form["text"]
                input_type = "text"
                metadata.update({"input_type": "text", "text_length": len(request.form["text"])})

        elif request.data and isinstance(request.data, (str, bytes)):
            try:
                url = request.data.decode("utf-8").strip() if isinstance(request.data, bytes) else request.data.strip()
                if url.startswith(("http://", "https://")):
                    logger.info(f"[Request {request_id}] Processing raw URL input")
                    input_data = url
                    input_type = "url"
                    metadata.update({"input_type": "url", "url": url})
            except Exception as e:
                logger.warning(f"[Request {request_id}] Failed to process raw data as URL: {str(e)}")

        # Unified handling for all three input types:
        # - File: async → _handle_file_upload (save to UPLOADS_SAVE_DIR, enqueue file path for worker); sync → process_any_input with file object.
        # - URL: fetch and normalize to text, then process as text (same pipeline as text box).
        # - Text: process_any_input(text, "text") for sync or enqueue text job.
        if input_data is not None and input_type is not None:
            logger.info(f"[Request {request_id}] Processing {input_type} input")
            force_mode = _enforce_async_only_mode(force_mode, request_id, "final_routing")

            # Async file: save to uploads (config), enqueue file job (worker path from config).
            # URL and text continue below; URL is normalized to text first.
            if input_type == "file" and precomputed_result is None:
                file_result = _handle_file_upload(service, request_id)
                if isinstance(file_result, dict) and file_result.get("error"):
                    return jsonify(file_result), 400
                return jsonify(file_result), 200

            # Normalize URL input to text before processing to avoid URL-stage stalls
            if input_type == "url":
                try:
                    normalized_text = service.extract_text_from_input({"type": "url", "url": input_data})
                    if not normalized_text or len(normalized_text.strip()) < 10:
                        logger.warning(f"[Request {request_id}] URL returned insufficient content; aborting")
                        return (
                            jsonify(
                                {
                                    "error": "URL returned empty or insufficient content for analysis",
                                    "request_id": request_id,
                                    "success": False,
                                }
                            ),
                            400,
                        )
                    # Convert to text pipeline
                    input_data = normalized_text
                    input_type = "text"
                    metadata.update({"input_type": "text", "text_length": len(normalized_text)})
                    logger.info(
                        f"[Request {request_id}] Converted URL to text ({len(normalized_text)} chars); proceeding as text"
                    )

                    # Respect user's force_mode preference if explicitly set
                    # Only use auto-routing if user didn't specify sync/async mode
                    if force_mode is None:
                        # Let the routing logic decide sync vs async based on text size
                        # Don't force sync mode - allow async processing for large PDFs
                        logger.info(
                            f"[Request {request_id}] Using automatic routing for URL input (text size: {len(normalized_text)} chars)"
                        )
                    else:
                        logger.info(
                            f"[Request {request_id}] Using user-requested mode: {force_mode} for URL input (text size: {len(normalized_text)} chars)"
                        )

                except Exception as _e:
                    logger.error(f"[Request {request_id}] URL fetch failed: {_e}")
                    return (
                        jsonify(
                            {
                                "error": f"Failed to fetch URL content: {str(_e)}",
                                "request_id": request_id,
                                "success": False,
                            }
                        ),
                        400,
                    )

            try:
                from src.unified_input_processor import UnifiedInputProcessor

                progress_data = {
                    "current_step": 0,
                    "total_steps": 5,
                    "current_message": "Initializing...",
                    "start_time": time.time(),
                    "steps": [
                        {"name": "Initializing...", "progress": 0, "status": "pending"},
                        {"name": "Extract", "progress": 0, "status": "pending"},
                        {"name": "Analyze", "progress": 0, "status": "pending"},
                        {"name": "Extract Names", "progress": 0, "status": "pending"},
                        {"name": "Cluster", "progress": 0, "status": "pending"},
                        {"name": "Verify", "progress": 0, "status": "pending"},
                    ],
                }

                def progress_callback(progress: int, step: str, message: str):
                    """Progress callback to update frontend progress."""
                    try:
                        for i, step_info in enumerate(progress_data["steps"]):
                            if step_info["name"] == step:
                                step_info["progress"] = progress
                                step_info["status"] = "completed" if progress == 100 else "in-progress"
                                step_info["message"] = message
                                break

                        progress_data["current_step"] = progress
                        progress_data["current_message"] = message

                        logger.info(f"[Request {request_id}] Progress: {progress}% - {step}: {message}")

                    except Exception as e:
                        logger.warning(f"[Request {request_id}] Progress callback error: {e}")

                # Use unified pipeline for all input types for consistent async behavior
                if precomputed_result is not None:
                    # Use precomputed results for immediate processing (text or files)
                    result = precomputed_result
                    logger.info(f"[Request {request_id}] Using precomputed result from immediate processing")
                else:
                    # Use UnifiedInputProcessor for async processing
                    # This ensures consistent async processing behavior
                    processor = UnifiedInputProcessor()
                    logger.info(f"[Request {request_id}] Using UnifiedInputProcessor for {input_type} input")
                    logger.info(
                        f"[Request {request_id}] Input data length: {len(str(input_data)) if input_data else 0}"
                    )
                    logger.info(f"[Request {request_id}] Force mode: {force_mode}")
                    logger.info(
                        f"[Request {request_id}] About to call process_any_input with force_mode='{force_mode}'"
                    )

                    # Log before processing to track async behavior
                    logger.info(f"[Request {request_id}] About to call process_any_input...")
                    result = processor.process_any_input(
                        input_data,
                        input_type,
                        request_id,
                        force_mode=force_mode,
                        enable_verification=enable_verification,  # Pass enable_verification parameter
                    )
                    logger.info(
                        f"[Request {request_id}] process_any_input returned, processing_mode={result.get('metadata', {}).get('processing_mode', 'unknown') if result else 'None'}"
                    )
                    logger.info(f"[Request {request_id}] process_any_input completed")
                    logger.info(f"[Request {request_id}] Result keys: {list(result.keys()) if result else 'None'}")

                    # Log processing mode from result
                    if result and "metadata" in result:
                        processing_mode = result["metadata"].get("processing_mode", "unknown")
                        logger.info(f"[Request {request_id}] Processing mode: {processing_mode}")
                    else:
                        logger.warning(f"[Request {request_id}] No metadata or result found")

                try:
                    if progress_tracker is not None:
                        progress_tracker.update_progress(
                            request_id, 40, "running", "Citations extracted successfully"
                        )
                    logger.info(f"[Request {request_id}] Progress update 1: Citations extracted")
                except Exception as progress_error:
                    logger.warning(f"[Request {request_id}] Progress update 1 failed: {progress_error}")

                try:
                    if progress_tracker is not None:
                        progress_tracker.update_progress(
                            request_id, 60, "running", "Citations normalized locally"
                        )
                    logger.info(f"[Request {request_id}] Progress update 2: Citations normalized")
                except Exception as progress_error:
                    logger.warning(f"[Request {request_id}] Progress update 2 failed: {progress_error}")

                try:
                    if progress_tracker is not None:
                        progress_tracker.update_progress(
                            request_id, 80, "running", "Case names and years extracted"
                        )
                    logger.info(f"[Request {request_id}] Progress update 3: Case names extracted")
                except Exception as progress_error:
                    logger.warning(f"[Request {request_id}] Progress update 3 failed: {progress_error}")
                time.sleep(0.1)  # Small delay for frontend to see progress

                try:
                    if progress_tracker is not None:
                        progress_tracker.update_progress(
                            request_id, 90, "running", "Citations clustered successfully"
                        )
                    logger.info(f"[Request {request_id}] Progress update 4: Citations clustered")
                except Exception as progress_error:
                    logger.warning(f"[Request {request_id}] Progress update 4 failed: {progress_error}")
                time.sleep(0.1)  # Small delay for frontend to see progress

                try:
                    if progress_tracker is not None:
                        progress_tracker.update_progress(
                            request_id, 100, "completed", "Processing complete"
                        )
                except Exception as progress_error:
                    logger.debug(f"[Request {request_id}] Progress completion update skipped: {progress_error}")

                # === Strict context repair (Vue path) ===
                # For text inputs, ensure extracted_case_name appears in the strict pre-citation context; otherwise re-extract.
                try:
                    if isinstance(input_data, str):
                        all_positions = find_all_citation_positions(input_data)
                        debug_flag = str(request.args.get("debug", "")).lower() in ("1", "true", "yes")
                        for _ci in result.get("citations") or []:
                            # Get citation text and current name
                            if isinstance(_ci, dict):
                                cit_text = _ci.get("citation") or _ci.get("text")
                                cur_name = _ci.get("extracted_case_name") or ""
                            else:
                                cit_text = getattr(_ci, "citation", None)
                                cur_name = getattr(_ci, "extracted_case_name", "") or ""
                            if not cit_text:
                                continue
                            # Resolve citation position
                            pos = None
                            for s, e, t in all_positions:
                                if t == cit_text:
                                    pos = (s, e)
                                    break
                            if pos is None:
                                m = input_data.find(cit_text)
                                if m != -1:
                                    pos = (m, m + len(cit_text))
                            # Robust fallback: regex search allowing flexible spaces/dots
                            if pos is None and cit_text:
                                try:

                                    def _build_citation_regex(s: str) -> str:
                                        # Escape everything then relax spaces and dots
                                        pat = re.escape(str(s))
                                        # Allow flexible whitespace between tokens
                                        pat = pat.replace(r"\ ", r"\\s+")
                                        # Make dots optional and allow optional following space
                                        pat = pat.replace(r"\.", r"\\.?")
                                        return pat

                                    rx = _build_citation_regex(cit_text)
                                    mx = re.search(rx, input_data, flags=re.IGNORECASE)
                                    if mx:
                                        pos = (mx.start(), mx.end())
                                except Exception as regex_error:
                                    logger.debug(
                                        f"[STRICT-REPAIR] Regex position fallback skipped for '{cit_text}': {regex_error}"
                                    )
                            if pos is None:
                                continue
                            s_idx, e_idx = pos
                            strict_ctx = get_strict_context_for_citation(
                                input_data, s_idx, e_idx, all_positions, max_lookback=200
                            )
                            # Normalize for containment check (use only the tail near the citation to avoid earlier-name bleed)
                            tail_for_check = (strict_ctx or "")[-160:]

                            def _norm(x: str) -> str:
                                return (x or "").lower().replace("\u2019", "'").replace("\u2018", "'").replace("`", "'")

                            if (
                                (not cur_name)
                                or (str(cur_name).strip().upper() == "N/A")
                                or (_norm(cur_name) not in _norm(tail_for_check))
                            ):
                                re_name = extract_case_name_from_strict_context(strict_ctx, cit_text)
                                if re_name and re_name != "N/A":
                                    if isinstance(_ci, dict):
                                        _ci["extracted_case_name"] = re_name
                                        _ci["method"] = "clean_pipeline_v1_strict_repair"
                                    else:
                                        try:
                                            setattr(_ci, "extracted_case_name", re_name)
                                            setattr(_ci, "method", "clean_pipeline_v1_strict_repair")
                                        except Exception as set_err:
                                            logger.debug(
                                                f"[STRICT-REPAIR] Object update skipped for '{cit_text}': {set_err}"
                                            )
                                    logger.info(
                                        f"[STRICT-REPAIR] Overwrote extracted name for {cit_text}: '{cur_name}' -> '{re_name}'"
                                    )
                            if debug_flag:
                                tail = (strict_ctx or "")[-120:]
                                if isinstance(_ci, dict):
                                    _ci["strict_context_tail"] = tail
                                else:
                                    try:
                                        setattr(_ci, "strict_context_tail", tail)
                                    except Exception as tail_err:
                                        logger.debug(
                                            f"[STRICT-REPAIR] strict_context_tail attach skipped for '{cit_text}': {tail_err}"
                                        )
                except Exception as _e:
                    logger.warning(f"[STRICT-REPAIR] Skipped due to error: {_e}")

                if result.get("success") is False or result.get("error"):
                    return _format_error(
                        result.get("error", "Unknown error"),
                        status_code=400,
                        request_id=request_id,
                        metadata={**metadata, **result.get("metadata", {})},
                    )

                result["request_id"] = request_id
                if "metadata" not in result:
                    result["metadata"] = {}

                # CRITICAL FIX: Only add progress_data with completed steps if processing was synchronous
                # For async/queued tasks, progress_data should only be added when task completes
                processing_mode = result.get("metadata", {}).get(
                    "processing_mode", result.get("processing_mode", "enhanced_sync")
                )
                is_async_or_queued = processing_mode in ("queued", "async", "async_progress")

                if not is_async_or_queued:
                    # Only add completed progress_data for synchronous processing
                    result["metadata"].update(
                        {
                            "processing_mode": processing_mode,
                            "input_type": input_type,
                            "text_length": len(str(input_data)) if hasattr(input_data, "__len__") else 0,
                            "async_verification_queued": result.get("async_verification_queued", False),
                            "progress_data": {
                                "current_step": 100,
                                "total_steps": 5,
                                "current_message": "Processing completed successfully",
                                "start_time": start_time,
                                "steps": [
                                    {
                                        "name": "Initializing...",
                                        "progress": 100,
                                        "status": "completed",
                                        "message": "Started enhanced sync processing",
                                    },
                                    {
                                        "name": "Extract",
                                        "progress": 100,
                                        "status": "completed",
                                        "message": "Citations extracted successfully",
                                    },
                                    {
                                        "name": "Analyze",
                                        "progress": 100,
                                        "status": "completed",
                                        "message": "Citations normalized locally",
                                    },
                                    {
                                        "name": "Extract Names",
                                        "progress": 100,
                                        "status": "completed",
                                        "message": "Case names and years extracted",
                                    },
                                    {
                                        "name": "Cluster",
                                        "progress": 100,
                                        "status": "completed",
                                        "message": "Citations clustered successfully",
                                    },
                                    {
                                        "name": "Verify",
                                        "progress": 100,
                                        "status": "completed",
                                        "message": "Results prepared successfully",
                                    },
                                ],
                            },
                        }
                    )
                else:
                    # For async/queued tasks, only add basic metadata without completed progress_data
                    result["metadata"].update(
                        {
                            "processing_mode": processing_mode,
                            "input_type": input_type,
                            "text_length": len(str(input_data)) if hasattr(input_data, "__len__") else 0,
                            "async_verification_queued": result.get("async_verification_queued", False),
                            "progress_data": {
                                "current_step": 0,
                                "total_steps": 5,
                                "current_message": "Processing started",
                                "start_time": start_time,
                                "steps": [
                                    {"name": "Initializing...", "progress": 0, "status": "pending"},
                                    {"name": "Extract", "progress": 0, "status": "pending"},
                                    {"name": "Analyze", "progress": 0, "status": "pending"},
                                    {"name": "Extract Names", "progress": 0, "status": "pending"},
                                    {"name": "Cluster", "progress": 0, "status": "pending"},
                                    {"name": "Verify", "progress": 0, "status": "pending"},
                                ],
                            },
                        }
                    )
                # If we have a task identifier, register verification so polling has a source
                try:
                    from src.verification_manager import VerificationManager

                    vm = VerificationManager()
                    job_id_candidate = None
                    if "task_id" in result:
                        job_id_candidate = result["task_id"]
                    elif result.get("verification_status", {}).get("verification_job_id"):
                        job_id_candidate = result["verification_status"].get("verification_job_id")
                    if job_id_candidate:
                        total_cites = (
                            len(result.get("citations", [])) if isinstance(result.get("citations"), list) else 0
                        )
                        vm.register_verification(request_id, job_id_candidate, total_cites)
                except Exception as _e:
                    logger.warning(f"[Request {request_id}] Could not register verification: {_e}")

                if result.get("async_verification_queued") and result.get("verification_status", {}).get(
                    "verification_queued"
                ):
                    verification_job_id = result["verification_status"].get("verification_job_id", request_id)
                    # Explicit registration for verification queue
                    try:
                        from src.verification_manager import VerificationManager

                        vm = VerificationManager()
                        total_cites = (
                            len(result.get("citations", [])) if isinstance(result.get("citations"), list) else 0
                        )
                        vm.register_verification(request_id, verification_job_id, total_cites)
                    except Exception as _e:
                        logger.warning(f"[Request {request_id}] Could not register async verification: {_e}")
                    return jsonify(
                        {
                            "status": "processing",
                            "task_id": verification_job_id,
                            "message": "Analysis completed, verification in progress",
                            "citations": result.get("citations", []),
                            "clusters": result.get("clusters", []),
                            "request_id": request_id,
                            "processing_mode": "enhanced_sync_with_async_verification",
                            "async_verification_queued": True,
                            "verification_job_id": verification_job_id,
                            "progress_data": {
                                "current_step": 90,
                                "total_steps": 6,
                                "current_message": "Verification in progress",
                                "start_time": start_time,
                                "steps": [
                                    {
                                        "name": "Initializing...",
                                        "progress": 100,
                                        "status": "completed",
                                        "message": "Started enhanced sync processing",
                                    },
                                    {
                                        "name": "Extract",
                                        "progress": 100,
                                        "status": "completed",
                                        "message": "Citations extracted successfully",
                                    },
                                    {
                                        "name": "Analyze",
                                        "progress": 100,
                                        "status": "completed",
                                        "message": "Citations normalized locally",
                                    },
                                    {
                                        "name": "Extract Names",
                                        "progress": 100,
                                        "status": "completed",
                                        "message": "Case names and years extracted",
                                    },
                                    {
                                        "name": "Cluster",
                                        "progress": 100,
                                        "status": "completed",
                                        "message": "Citations clustered successfully",
                                    },
                                    {
                                        "name": "Verify",
                                        "progress": 90,
                                        "status": "in-progress",
                                        "message": "Verification queued for background processing",
                                    },
                                ],
                            },
                        }
                    )

                return _format_response(result, request_id, metadata, start_time)

            except Exception as e:
                error_msg = f"Error in unified processor: {str(e)}"
                logger.error(f"[Request {request_id}] {error_msg}", exc_info=True)
                return _format_error(
                    error_msg,
                    status_code=500,
                    request_id=request_id,
                    metadata={**metadata, "error_type": "unified_processor_error", "error_details": str(e)},
                )

        content_type = request.content_type or "not specified"
        error_msg = (
            f"Invalid or missing input. No file, JSON, or form data found. "
            f"Content-Type: {content_type}, Data length: {len(request.data) if request.data else 0}"
        )
        logger.error(f"[Request {request_id}] {error_msg}")

        return _format_error(
            "Invalid or missing input. Please check the Content-Type header and request format.",
            details=error_msg,
            status_code=400,
            request_id=request_id,
            metadata={**metadata, "error_type": "invalid_input", "error_details": error_msg},
        )

    except Exception as e:
        error_msg = f"Unexpected error in analyze endpoint: {str(e)}"
        logger.error(f"[Request {request_id}] {error_msg}", exc_info=True)

        return _format_error(
            "An unexpected error occurred during analysis",
            details=str(e),
            status_code=500,
            request_id=request_id,
            metadata={**metadata, "error_type": "unexpected_error", "error_details": str(e)},
        )


def _validate_api_response_data(response_data):
    """Validate API response structure; return list of error strings or empty list."""
    errors = []
    if not isinstance(response_data, dict):
        errors.append("response_data must be a dict")
        return errors
    if "citations" in response_data and not isinstance(response_data["citations"], list):
        errors.append("citations must be a list")
    if "clusters" in response_data and not isinstance(response_data["clusters"], list):
        errors.append("clusters must be a list")
    return errors


def _format_response(result, request_id, metadata, start_time):
    """Format a successful response with consistent structure"""
    processing_time_ms = int((time.time() - start_time) * 1000)

    # NEW: Apply parallel verification to citations before returning response
    print(f"_format_response: Applying parallel verification to {len(result.get('citations', []))} citations")
    try:
        citations = result.get("citations", [])
        if citations and len(citations) > 1:
            # Import the parallel verification function
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

            processor = UnifiedCitationProcessorV2()

            # Convert dict citations to CitationResult objects if needed
            from src.models import CitationResult

            citation_objects = []

            for cit in citations:
                if isinstance(cit, dict):
                    # Convert dict to CitationResult object
                    cit_obj = CitationResult(
                        citation=cit.get("citation", ""),
                        extracted_case_name=cit.get("extracted_case_name", ""),
                        extracted_date=cit.get("extracted_date", ""),
                        canonical_name=cit.get("canonical_name", ""),
                        canonical_date=cit.get("canonical_date", ""),
                        canonical_url=cit.get("canonical_url", ""),
                        verified=cit.get("verified", False),
                        true_by_parallel=cit.get("true_by_parallel", False),
                        possible_match=cit.get("possible_match", False),
                        error=cit.get("error"),
                        source=cit.get("source", "Unknown"),
                        start_index=cit.get("start_index"),
                        end_index=cit.get("end_index"),
                        method=cit.get("method", ""),
                        confidence=cit.get("confidence", 0.0),
                        metadata=cit.get("metadata", {}),
                    )
                    citation_objects.append(cit_obj)
                else:
                    citation_objects.append(cit)

            # Apply parallel verification
            processor.propagate_canonical_to_cluster(citation_objects)
            print(f"_format_response: Parallel verification completed")

            # Update the result with parallel verification data
            updated_citations = []
            for i, cit_obj in enumerate(citation_objects):
                if isinstance(citations[i], dict):
                    # Convert back to dict, preserving existing metadata
                    citations[i]["true_by_parallel"] = getattr(cit_obj, "true_by_parallel", False)
                    citations[i]["verified"] = getattr(cit_obj, "verified", False)
                    citations[i]["canonical_name"] = getattr(cit_obj, "canonical_name", "")
                    citations[i]["canonical_date"] = getattr(cit_obj, "canonical_date", "")
                    citations[i]["canonical_url"] = getattr(cit_obj, "canonical_url", "")
                    citations[i]["possible_match"] = getattr(cit_obj, "possible_match", False)

                    # Preserve existing metadata and merge with verification metadata
                    existing_metadata = citations[i].get("metadata", {})
                    verification_metadata = getattr(cit_obj, "metadata", {})

                    # Merge metadata, with verification metadata taking precedence
                    merged_metadata = {**existing_metadata, **verification_metadata}

                    # Ensure verification status is consistent
                    if citations[i].get("verified", False):
                        merged_metadata["verification_status"] = "verified"
                    elif not merged_metadata.get("verification_status"):
                        merged_metadata["verification_status"] = "unverified"

                    citations[i]["metadata"] = merged_metadata
                    updated_citations.append(citations[i])
                else:
                    updated_citations.append(cit_obj)

            result["citations"] = updated_citations

            # Log if parallel verification was applied
            parallel_count = 0
            for c in updated_citations:
                if isinstance(c, dict):
                    if c.get("true_by_parallel", False):
                        parallel_count += 1
                else:
                    if getattr(c, "true_by_parallel", False):
                        parallel_count += 1
            if parallel_count > 0:
                print(f"_format_response: Applied parallel verification to {parallel_count} citations")
                logger.info(f"[_format_response] Applied parallel verification to {parallel_count} citations")

    except Exception as parallel_error:
        print(f"_format_response: Parallel verification failed: {parallel_error}")
        logger.warning(f"[_format_response] Parallel verification failed (non-critical): {parallel_error}")
        import traceback

        logger.warning(f"[_format_response] Parallel verification error details: {traceback.format_exc()}")

    if not isinstance(result, dict):
        result = {}

    metadata.update(
        {
            "processing_time_ms": processing_time_ms,
            "processing_mode": result.get("metadata", {}).get(
                "processing_mode", metadata.get("processing_mode", "unknown")
            ),
            "status": result.get("status", "completed"),
            "success": result.get("success", True),
        }
    )

    def _normalize_legal_name(s):
        try:
            import re, html

            if not s:
                return ""
            x = html.unescape(str(s)).lower()
            x = x.replace("" ', "' ").replace('`', " '").replace(' " ", "'")
            patterns = [
                (r"\bdep[''.\']?t\b", "department"),
                (r"\bcomm[''.\']?n\b", "commission"),
                (r"\binfo\.?\b", "information"),  # FIX DEC 2025: Info. -> Information
                (r"\bpub\.?\b", "public"),
                (r"\butil\.?\b", "utility"),
                (r"\bins\.?\b", "insurance"),
                (r"\bfed[''.\']?n\b", "federation"),
                (r"\bass[''.\']?n\b", "association"),
                (r"\bpa\.?\b", "pennsylvania"),
                (r"\bu\.?s\.?\b", "united states"),
                (r"\bsec\.?\b", "securities"),
                (r"\bexch\.?\b", "exchange"),
                (r"\bmfrs?\.?\b", "manufacturers"),
                (r"\bindus\.?\b", "industries"),
                (r"\bnat[''.\']?l\b", "national"),
                (r"\bcommw\.?\b", "commonwealth"),
                # FIX DEC 2025: Additional legal abbreviations
                (r"\bhous\.?\b", "housing"),
                (r"\bauth\.?\b", "authority"),
                (r"\bcmtys?\.?\b", "communities"),
                (r"\bwash\.?\b", "washington"),
                (r"\bcty\.?\b", "county"),
                (r"\brsrv\.?\b", "reservation"),
                (r"\bbd\.?\b", "board"),
                (r"\btrs\.?\b", "trustees"),
                (r"\bcommc\.?\b", "communications"),
                (r"\bsoc[''.\']?y\b", "society"),
                (r"\bdef\.?\b", "defense"),
                (r"\bcent\.?\b", "central"),
                (r"\bdev\.?\b", "development"),
                (r"\bserv\.?\b", "services"),
                (r"\bsrvs\.?\b", "services"),
            ]
            for pat, repl in patterns:
                x = re.sub(pat, repl, x)
            x = re.sub(r"[\.,\-_/&()]+", " ", x)
            x = re.sub(r"\s+", " ", x).strip()
            stop = {
                "inc",
                "llc",
                "ltd",
                "corp",
                "co",
                "company",
                "limited",
                "plc",
                "s.a.",
                "sa",
                "gmbh",
                "ag",
                # permissive: ignore common agency qualifiers to reduce false negatives
                "department",
                "dept",
                "division",
                "bureau",
                "office",
                "ministry",
                "agency",
                "administration",
            }
            tokens = [t for t in x.split() if t not in stop]
            return " ".join(tokens)
        except Exception:
            return str(s or "").strip().lower()

    def _jaccard(a, b):
        sa = set((a or "").split())
        sb = set((b or "").split())
        if not sa or not sb:
            return 0.0
        inter = len(sa & sb)
        uni = len(sa | sb)
        return inter / max(1, uni)

    def _names_equivalent(a, b):
        """Lenient: prefer false positives over false negatives."""
        try:
            if not a or not b:
                return False
            if a == b:
                return True
            # Accept substring containment after normalization
            if a in b or b in a:
                return True
            # Lower Jaccard threshold to be lenient
            return _jaccard(a, b) >= 0.5
        except Exception:
            return False

    # USER FIX 2024-10-21: Convert CitationResult objects to dicts BEFORE building response
    citations_raw = result.get("citations", [])
    logger.info(f"[DEBUG] Processor returned {len(citations_raw)} citations")
    if citations_raw:
        logger.info(f"[DEBUG] First citation: {citations_raw[0]}")

    citations_serialized = []
    for cit in citations_raw:
        # Serialize citation object/dict first
        if hasattr(cit, "to_dict"):
            d = cit.to_dict()
        elif isinstance(cit, dict):
            d = dict(cit)
        else:
            d = cit.__dict__ if hasattr(cit, "__dict__") else {"raw": str(cit)}

        # Enforce strict data separation: extracted_* must come from document
        try:
            # Prefer original_case_name/date captured pre-verification
            original_case = None
            original_date = None
            if isinstance(cit, dict):
                original_case = cit.get("original_case_name")
                original_date = cit.get("original_date")
            else:
                original_case = getattr(cit, "original_case_name", None)
                original_date = getattr(cit, "original_date", None)

            if original_case:
                if not d.get("extracted_case_name") or d.get("extracted_case_name") == "N/A":
                    d["extracted_case_name"] = original_case
                d["extracted_source"] = "document"
            # Do not overwrite extracted_date with canonical; restore original when present
            if original_date:
                if not d.get("extracted_date") or d.get("extracted_date") == "N/A":
                    d["extracted_date"] = original_date

            # Ensure canonical fields remain separate
            # (no action needed if d already has 'canonical_name'/'canonical_date')
        except Exception as _e:
            logger.warning(f"[RESPONSE] Data separation enforcement skipped for a citation: {_e}")

        citations_serialized.append(d)

    # Filter out court-year-only items (e.g., "N.J. 1997") from citations and clusters
    try:
        import re

        def _is_court_year_only(cit_text: str) -> bool:
            """Filter only short court-year-only strings (e.g. 'N.J. 1997'), not full citations that contain a year."""
            if not cit_text:
                return False
            t = str(cit_text).strip()
            # Reporter citation starts with volume (e.g. "123 F.3d 456") - keep those
            looks_like_reporter = re.match(r"^\d+\s+[A-Za-z\.]", t) is not None
            if looks_like_reporter:
                return False
            has_year = re.search(r"(17|18|19|20)\d{2}\b", t) is not None
            if not has_year:
                return False
            # Only treat as court-year-only if string is short (no full case name + citation)
            # so we don't drop e.g. "Milkovich v. Lorain Journal Co., 497 U.S. 1 (1990)"
            if len(t) > 40:
                return False
            return True

        # Filter individual citations (sync-only; async task_status returns pipeline output unfiltered)
        before_c = len(citations_serialized)
        removed = [c for c in citations_serialized if _is_court_year_only(c.get("citation"))]
        citations_serialized = [c for c in citations_serialized if not _is_court_year_only(c.get("citation"))]
        after_c = len(citations_serialized)
        if removed:
            logger.info(
                f"[FILTER] Removed {len(removed)} court-year-only items from citations (sync); "
                f"remaining {after_c} (async may have {before_c} before this filter)"
            )
            for i, c in enumerate(removed[:10]):
                cit_text = (c.get("citation") or c.get("text") or "")[:80]
                logger.debug(f"[FILTER] court-year-only removed [{i+1}]: {repr(cit_text)}")
            if len(removed) > 10:
                logger.debug(f"[FILTER] ... and {len(removed) - 10} more court-year-only citations")
    except Exception as _e:
        logger.warning(f"[FILTER] Failed filtering court-year-only citations: {_e}")

    # Normalize citations to stable DTO shape
    try:
        citations_serialized = [normalize_citation_dict(c) for c in citations_serialized]
    except Exception as _e:
        logger.warning(f"[SCHEMAS] Citation normalization failed, using raw dicts: {_e}")

    try:
        import re

        def _year_from(s):
            if not s:
                return ""
            m = re.search(r"(17|18|19|20)\d{2}", str(s))
            return m.group(0) if m else ""

        for c in citations_serialized:
            exn = c.get("extracted_case_name") or ""
            can = c.get("canonical_name") or c.get("canonical_case_name") or ""
            nex = _normalize_legal_name(exn)
            ncan = _normalize_legal_name(can)
            c["normalized_extracted_name"] = nex
            c["normalized_canonical_name"] = ncan
            eq = _names_equivalent(nex, ncan) if (nex and ncan) else False
            c["names_equivalent"] = eq
            # Only flag mismatch on strong disagreement (very low similarity and no substring)
            if nex and ncan:
                j = _jaccard(nex, ncan)
                c["name_mismatch"] = (nex not in ncan) and (ncan not in nex) and (j < 0.3)
            else:
                c["name_mismatch"] = False
            c["submitted_display_name"] = html.unescape(exn or c.get("citation") or "")
            c["submitted_display_date"] = c.get("extracted_date") or _year_from(c.get("extracted_date")) or ""
            
            # USER FIX 2026-01-09: Map 'verified' to 'found' for UI compatibility
            # The UI checks citation.found to determine verification status
            if "verified" in c and "found" not in c:
                c["found"] = c["verified"]
            # CAPTCHA masking: if canonical appears to be 'capcha/captcha', treat as unverified with no verifying display
            if ncan and ("captcha" in ncan or ncan == "capcha"):
                try:
                    c["verified"] = False
                except Exception as captcha_err:
                    logger.debug(f"[RESPONSE] CAPTCHA masking verify reset skipped: {captcha_err}")
                # Clear canonical fields so UI won't display placeholder
                if "canonical_name" in c:
                    c["canonical_name"] = None
                if "canonical_case_name" in c:
                    c["canonical_case_name"] = None
                if "canonical_date" in c and not c.get("canonical_date"):
                    c["canonical_date"] = None
                c["verifying_display_name"] = ""
                c["error"] = c.get("error") or "captcha_blocked"
            else:
                # Clean canonical fields for API consumers
                if c.get("canonical_name"):
                    c["canonical_name"] = html.unescape(c["canonical_name"])
                if c.get("canonical_case_name"):
                    c["canonical_case_name"] = html.unescape(c["canonical_case_name"])
                c["verifying_display_name"] = html.unescape(can)
            # Normalize to year for display consistency with submitted_display_date (avoids false "Different date" when years match)
            c["verifying_display_date"] = _year_from(c.get("canonical_date")) or c.get("canonical_date") or ""
    except Exception as _e:
        logger.warning(f"[RESPONSE] Failed to add name normalization fields: {_e}")

    # Add display_base_citation, citation_score, name_similarity (backend single source of truth)
    try:
        for c in citations_serialized:
            raw = c.get("citation") or c.get("text") or ""
            c["display_base_citation"] = extract_display_base_citation(raw)
            score, name_sim = compute_citation_score_and_similarity(c)
            c["citation_score"] = score
            c["name_similarity"] = name_sim
            c["score_color"] = "text-success" if score >= 4 else ("text-warning" if score >= 2 else "text-danger")
    except Exception as _e:
        logger.warning(f"[RESPONSE] Failed to add citation display/score fields: {_e}")

    # Add progress endpoints for UI polling/streaming
    result["progress_endpoint"] = f"/casestrainer/api/analyze/progress/{request_id}"
    result["progress_stream"] = f"/casestrainer/api/analyze/progress-stream/{request_id}"

    # Prepare clusters with filtered inner citations if present (preserve objects and verified flags)
    clusters_data = result.get("clusters", [])
    # When pipeline returns citations but no clusters, build fallback clusters on backend (single source of truth)
    if not clusters_data and citations_serialized:
        try:
            clusters_data = build_fallback_clusters(citations_serialized)
            logger.info(f"[RESPONSE] Built {len(clusters_data)} fallback clusters from {len(citations_serialized)} citations")
        except Exception as _e:
            logger.warning(f"[RESPONSE] Fallback cluster build failed: {_e}")

    try:

        def _filter_cluster_citations(citations_list):
            cleaned = []
            for it in citations_list or []:
                if isinstance(it, dict):
                    text = it.get("citation") or it.get("text") or ""
                    if _is_court_year_only(text):
                        continue
                    # ensure 'citation' field exists for matching
                    if not it.get("citation") and it.get("text"):
                        it["citation"] = it["text"]
                    cleaned.append(it)
                else:
                    text = str(it)
                    if _is_court_year_only(text):
                        continue
                    cleaned.append(text)
            return cleaned

        def _norm_cit(v):
            return (str(v or "")).strip()

        def _extract_cit_key(v: str) -> str:
            s = _norm_cit(v)
            try:
                m = re.search(r"\b\d+\s+[A-Za-z][A-Za-z\.\d]*\s+\d+\b", s)
                if m:
                    return m.group(0).strip()
            except Exception as key_err:
                logger.debug(f"[RESPONSE] Citation key extraction fallback used: {key_err}")
            # as-is fallback
            return s

        # build lookup from individual citations for enrichment (full and short key so cluster enrichment finds)
        _cit_lut = {}
        for c in citations_serialized:
            key = _norm_cit(c.get("citation"))
            if key:
                _cit_lut[key] = c
            short = _extract_cit_key((c.get("citation") or c.get("text")) or "")
            if short and short not in _cit_lut:
                _cit_lut[short] = c

        for cl in clusters_data:
            if isinstance(cl, dict) and "citations" in cl:
                items = _filter_cluster_citations(cl.get("citations"))
                enriched = []
                for it in items:
                    if isinstance(it, dict):
                        key = _extract_cit_key((it.get("citation") or it.get("text")) or "")
                        match = _cit_lut.get(key)
                        if match:
                            merged = dict(match)
                            # overlay original minimal fields cautiously (don't overwrite protected fields)
                            protected = {
                                "extracted_case_name",
                                "extracted_date",
                                "canonical_name",
                                "canonical_case_name",
                                "canonical_date",
                                "verified",
                                "verification_source",
                                "verification_url",
                            }
                            for k, v in it.items():
                                if v in [None, ""]:
                                    continue
                                if k in protected:
                                    # do not overwrite protected keys
                                    if not merged.get(k):
                                        merged[k] = v
                                else:
                                    merged[k] = v
                            enriched.append(merged)
                        else:
                            # ensure 'verified' key present for UI logic
                            if "verified" not in it:
                                it["verified"] = False
                            enriched.append(it)
                    else:
                        key = _extract_cit_key(it)
                        match = _cit_lut.get(key)
                        if match:
                            enriched.append(match)
                        else:
                            enriched.append({"text": key, "citation": key, "verified": False})
                cl["citations"] = enriched

                # CRITICAL FIX: Calculate cluster verified status from child citations
                # Cluster is verified if any citation is verified and has canonical_url
                any_verified = False
                best_canonical_name = None
                best_canonical_date = None
                best_canonical_url = None
                for cit in enriched:
                    if isinstance(cit, dict):
                        if is_effectively_verified_citation(cit):
                            any_verified = True
                            if cit.get("canonical_name"):
                                best_canonical_name = cit.get("canonical_name")
                                best_canonical_date = cit.get("canonical_date")
                                best_canonical_url = cit.get("canonical_url")
                # Set cluster verified flag based on child citations
                cl["verified"] = any_verified
                if best_canonical_url:
                    cl["canonical_url"] = best_canonical_url
                if best_canonical_name:
                    cl["canonical_name"] = best_canonical_name
                    cl["verifying_display_name"] = best_canonical_name
                if best_canonical_date:
                    cl["canonical_date"] = best_canonical_date

                # Do NOT propagate cluster canonical fields onto child citations.
                # That can contaminate mixed-tier clusters (e.g., F. Supp. inheriting U.S. canonical URL/name).
                # Only set citation-local display alias when the citation itself is verified with its own canonical name.
                for cit in cl["citations"]:
                    if not isinstance(cit, dict):
                        continue
                    if cit.get("verified") and cit.get("canonical_name") and cit.get("canonical_name") != "N/A":
                        cit["cluster_case_name"] = cit["canonical_name"]

        # Safety pass: enforce canonical post-cluster split rules here too, so fallback
        # clusters or response-enriched clusters cannot ship mixed court tiers.
        clusters_data = apply_post_verify_cluster_splits(
            clusters_data,
            run_id=request_id,
        )

        # Annotate mismatch flags using centralized mismatch_utils (single source of truth)
        try:
            from src.utils.mismatch_utils import annotate_mismatch_flags
            citations_flat = [c for cl in clusters_data for c in (cl.get("citations") or []) if isinstance(c, dict)]
            annotate_mismatch_flags(citations_flat, clusters_data, name_threshold=0.4, year_tolerance=0)
        except Exception as _ann:
            logger.warning(f"[FILTER] annotate_mismatch_flags failed: {_ann}")
    except Exception as _e:
        logger.warning(f"[FILTER] Failed filtering/annotating clusters: {_e}")

    # Normalize clusters to stable DTO shape (preserve enriched data)
    try:
        clusters_data = [normalize_cluster_dict(cl) if isinstance(cl, dict) else cl for cl in clusters_data]
    except Exception as _e:
        logger.warning(f"[SCHEMAS] Cluster normalization failed, using raw dicts: {_e}")

    # Last-mile response hygiene: normalize proprietary messages (dedupe runs after display finalization).
    try:
        apply_proprietary_display_fallback(citations_serialized)
        for _cl in clusters_data:
            if not isinstance(_cl, dict):
                continue
            apply_proprietary_display_fallback(_cl.get("citations") or [])
    except Exception as _e:
        logger.warning(f"[RESPONSE] Final response hygiene failed: {_e}")

    # Add cluster-level display fields and lenient equivalence for UI
    try:
        import re

        def _year_only(s):
            if not s:
                return ""
            m = re.search(r"(17|18|19|20)\d{2}", str(s))
            return m.group(0) if m else ""

        for cl in clusters_data:
            if not isinstance(cl, dict):
                continue
            cits = cl.get("citations") or []
            rep = None
            for it in cits:
                if isinstance(it, dict) and (
                    it.get("extracted_case_name") or it.get("canonical_name") or it.get("canonical_case_name")
                ):
                    rep = it
                    if it.get("verified"):
                        break
            if rep is None and cits:
                rep = cits[0] if isinstance(cits[0], dict) else None
            exn = _normalize_legal_name(rep.get("extracted_case_name") if rep else "")
            can = _normalize_legal_name((rep.get("canonical_name") or rep.get("canonical_case_name")) if rep else "")
            j = _jaccard(exn, can) if (exn and can) else 0.0
            names_eq = _names_equivalent(exn, can) if (exn and can) else False
            name_mm = False if names_eq else (exn not in can and can not in exn and j < 0.4) if (exn and can) else False
            
            # Use shared backend finalizer as single source of truth for
            # submitted/verifying display fields and unverified canonical clearing.
            finalize_cluster_for_response(
                cl,
                clean_names=False,
                clear_unverified_canonical=True,
                clear_unverified_citations=True,
            )
            # Lenient flags for UI
            cl["names_equivalent"] = names_eq
            cl["name_mismatch"] = name_mm
            cl["name_similarity"] = j

            # Backend-provided deduplicated list for display (by display_base_citation, prefer verified)
            # Enrich truncated citations (e.g. "31 Wn. App. 2") with fuller text from cluster_members
            try:
                cits = enrich_citations_with_cluster_members(
                    cl.get("citations") or [],
                    cl.get("cluster_members") or [],
                )
                cl["display_citations"] = deduplicate_cluster_citations(cits)
            except Exception:
                cl["display_citations"] = cl.get("citations") or []

        try:
            clusters_data = merge_clusters_by_shared_real_canonical_url(clusters_data)
            for _cl in clusters_data:
                if isinstance(_cl, dict):
                    finalize_cluster_for_response(
                        _cl,
                        clean_names=False,
                        clear_unverified_canonical=True,
                        clear_unverified_citations=True,
                    )
            clusters_data = deduplicate_clusters_for_response(clusters_data)
            for _cl in clusters_data:
                if not isinstance(_cl, dict):
                    continue
                try:
                    cits = enrich_citations_with_cluster_members(
                        _cl.get("citations") or [],
                        _cl.get("cluster_members") or [],
                    )
                    _cl["display_citations"] = deduplicate_cluster_citations(cits)
                except Exception:
                    _cl["display_citations"] = _cl.get("citations") or []
        except Exception as _dedupe_err:
            logger.warning(f"[RESPONSE] Cluster merge/dedupe after finalize failed: {_dedupe_err}")
    except Exception as _e:
        logger.warning(f"[RESPONSE] Failed to add cluster display fields: {_e}")

    # Pre-categorized cluster sections for frontend (optional: frontend can use cluster_sections or compute locally)
    cluster_sections = {}
    try:
        cluster_sections = compute_cluster_sections(clusters_data)
    except Exception as _e:
        logger.warning(f"[RESPONSE] Failed to compute cluster_sections: {_e}")

    # Best-effort: record citations count when returning a completed, successful response
    try:
        if isinstance(citations_serialized, list):
            status_flag = result.get("status", "completed")
            success_flag = bool(result.get("success", True))
            if success_flag and status_flag == "completed" and len(citations_serialized) > 0:
                record_citations(len(citations_serialized))
    except Exception as record_err:
        logger.debug(f"[RESPONSE] record_citations skipped: {record_err}")

    response_data = {
        "citations": citations_serialized,  # Move to top level
        "clusters": clusters_data,  # Move to top level
        "cluster_sections": cluster_sections,  # Pre-categorized: unverified, case_mismatch, date_mismatch, etc.
        "result": {
            "statistics": result.get("statistics", {}),
        },
        "request_id": request_id,
        "success": result.get("success", True),
        "status": result.get("status", "completed"),  # Always include status
        "metadata": {**result.get("metadata", {}), **metadata},
    }

    if "progress_data" in result:
        response_data["metadata"]["progress_data"] = result["progress_data"]

    if "task_id" in result:
        # Add task_id to both top level AND inside result for frontend compatibility
        response_data.update(
            {
                "task_id": result["task_id"],
                "status": result.get("status", "processing"),
                "message": result.get("message", "Request is being processed"),
            }
        )
        response_data["result"]["task_id"] = result["task_id"]  # Also add inside result

    for key in ["message", "warnings", "debug", "verification_status", "async_verification_queued"]:
        if key in result and key not in response_data:
            response_data[key] = result[key]

    # Perform data integrity validation before returning response
    validation_errors = _validate_api_response_data(response_data)
    if validation_errors:
        logger.error(f"[Request {request_id}] Data integrity validation failed: {validation_errors}")
        # Log the validation errors but don't fail the request - let frontend handle it
        response_data["metadata"]["validation_warnings"] = validation_errors

    log_data = copy.deepcopy(response_data)

    def safe_serialize(obj):
        """Safely serialize objects to JSON, handling custom objects"""
        # USER FIX 2024-10-21: Check to_dict() FIRST before __dict__
        # CitationResult has both, but to_dict() includes proper serialization logic
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        elif isinstance(obj, (list, tuple)):
            return [safe_serialize(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: safe_serialize(v) for k, v in obj.items()}
        return str(obj)  # Fallback to string representation

    if "result" in log_data:
        result_data = log_data["result"]
        if "citations" in result_data:
            if len(result_data["citations"]) > 5:
                result_data["citations"] = f"[list of {len(result_data['citations'])} citations]"
            else:
                result_data["citations"] = safe_serialize(result_data["citations"])

        if "clusters" in result_data:
            if len(result_data["clusters"]) > 3:
                result_data["clusters"] = f"[list of {len(result_data['clusters'])} clusters]"
            else:
                result_data["clusters"] = safe_serialize(result_data["clusters"])

    logger.info(f"[Request {request_id}] Request completed successfully in {processing_time_ms}ms")

    try:
        os.makedirs("/app/logs", exist_ok=True)

        serializable_data = safe_serialize(response_data)

        with open("/app/logs/frontend_api_results.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(serializable_data, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to write API response to log file: {e}")

    try:
        json.dumps(response_data)
    except (TypeError, ValueError) as e:
        logger.error(f"Response contains non-serializable data: {e}")
        try:
            if "result" in response_data and response_data["result"]:
                if "citations" in response_data["result"]:
                    response_data["result"]["citations"] = [
                        cit.to_dict() if hasattr(cit, "to_dict") else safe_serialize(cit)
                        for cit in response_data["result"]["citations"]
                    ]
                if "clusters" in response_data["result"]:
                    response_data["result"]["clusters"] = [
                        {k: (v.to_dict() if hasattr(v, "to_dict") else safe_serialize(v)) for k, v in cluster.items()}
                        for cluster in response_data["result"]["clusters"]
                    ]

            json.dumps(response_data)
        except (TypeError, ValueError) as e2:
            logger.error(f"Failed to fix non-serializable data: {e2}")
            response_data = safe_serialize(response_data)

    return jsonify(response_data)


def _format_error(message, details=None, status_code=400, request_id=None, metadata=None):
    """Format an error response with consistent structure"""
    error_data = {
        "error": message,
        "details": details or message,
        "request_id": request_id or str(uuid.uuid4()),
        "success": False,
        "citations": [],
        "clusters": [],
        "metadata": metadata or {},
    }

    if "request_id" not in error_data["metadata"] and request_id:
        error_data["metadata"]["request_id"] = request_id

    if "status" not in error_data["metadata"]:
        error_data["metadata"]["status"] = "error"

    logger.error(f"[Request {request_id or 'unknown'}] Error: {message}")
    if details and details != message:
        logger.error(f"[Request {request_id or 'unknown'}] Details: {details}")

    return jsonify(error_data), status_code



def _handle_file_upload(service, request_id):
    """
    Handle file upload with proper async processing and CitationService integration

    Args:
        service: Instance of CitationService
        request_id: Unique ID for request tracking

    Returns:
        Response with analysis results or task status
    """
    logger.info(f"[File Upload {request_id}] Starting file upload handler")

    try:
        if "file" not in request.files:
            error_msg = "No file provided in request.files"
            logger.error(f"[File Upload {request_id}] {error_msg}")
            return {
                "error": error_msg,
                "citations": [],
                "clusters": [],
                "request_id": request_id,
                "success": False,
                "metadata": {},
            }

        file = request.files["file"]
        if not file or file.filename == "":
            error_msg = "No file selected or empty file"
            logger.error(f"[File Upload {request_id}] {error_msg}")
            return {
                "error": error_msg,
                "citations": [],
                "clusters": [],
                "request_id": request_id,
                "success": False,
                "metadata": {},
            }

        filename = secure_filename(file.filename) if file.filename else "unknown_file"
        logger.info(f"[File Upload {request_id}] Processing file: {filename}")
        logger.info(f"[File Upload {request_id}] Content type: {file.content_type}")

        # EARLY verification registration so frontend polling gets 200 immediately
        try:
            from src.verification_manager import VerificationManager

            vm = VerificationManager()
            client_request_id = request.form.get("client_request_id")
            total_cites = 0
            if client_request_id:
                vm.register_verification(client_request_id, request_id, total_cites)
            vm.register_verification(request_id, request_id, total_cites)
            logger.info(f"[File Upload {request_id}] Early verification registered (client_id={client_request_id})")
        except Exception as _e:
            logger.warning(f"[File Upload {request_id}] Early verification registration failed: {_e}")

        allowed_extensions = {"pdf", "txt", "doc", "docx", "rtf", "md", "html", "htm", "xml", "xhtml"}
        file_ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""

        if file_ext not in allowed_extensions:
            error_msg = f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}. Got: {file_ext}'
            logger.error(f"[File Upload {request_id}] {error_msg}")
            return {
                "error": error_msg,
                "citations": [],
                "clusters": [],
                "request_id": request_id,
                "success": False,
                "metadata": {},
            }

        unique_filename = f"{uuid.uuid4()}_{filename}"
        logger.info(f"[File Upload {request_id}] Generated secure filename: {unique_filename}")

        from src.config import UPLOADS_SAVE_DIR, UPLOADS_WORKER_PATH

        uploads_dir = os.path.normpath(os.path.abspath(UPLOADS_SAVE_DIR))
        os.makedirs(uploads_dir, exist_ok=True)
        logger.info(f"[File Upload {request_id}] Upload directory: {uploads_dir}")

        file_path_local = os.path.join(uploads_dir, unique_filename)
        logger.info(f"[File Upload {request_id}] Saving file to: {file_path_local}")

        # Path for job payload: worker opens this path (e.g. /app/uploads/... in Docker).
        file_path_for_worker = os.path.join(UPLOADS_WORKER_PATH, unique_filename)

        try:
            file.save(file_path_local)

            if not os.path.exists(file_path_local):
                raise IOError("File was not saved successfully")

            logger.info(f"[File Upload {request_id}] File saved successfully")

            file_size = os.path.getsize(file_path_local)

            options = {}
            if "options" in request.form:
                try:
                    options = json.loads(request.form["options"])
                    logger.info(f"[File Upload {request_id}] Parsed options: {options}")
                except json.JSONDecodeError as e:
                    logger.warning(f"[File Upload {request_id}] Failed to parse options JSON: {e}")

            logger.info(f"[File Upload {request_id}] Starting file processing with CitationService")

            # Extract text from file and determine processing mode based on content size
            # The input format (file, URL, text) should be irrelevant - only text size matters
            from src.api.services.citation_service import CitationService

            citation_service = CitationService()

            # Create input data for the service
            input_data = {"type": "file", "file_path": file_path_local, "filename": filename, "file_size": file_size}
            force_mode = request.form.get("force_mode")
            if force_mode == "sync" and SYNC_REQUESTS_AS_ASYNC:
                force_mode = "async"
                logger.info(f"[File Upload {request_id}] SYNC_REQUESTS_AS_ASYNC: treating sync as async")
            if force_mode:
                logger.info(f"[File Upload {request_id}] Force mode requested: {force_mode}")

            logger.info(f"[File Upload {request_id}] File size: {file_size} bytes")
            logger.info(f"[File Upload {request_id}] Input data: {input_data}")

            # Extract text from file and determine processing mode
            text = citation_service.extract_text_from_input(input_data)
            if text is None:
                logger.error(f"[File Upload {request_id}] Failed to extract text from file")
                return {
                    "error": "Failed to extract text from file",
                    "details": "The file could not be processed. Please ensure it contains readable text.",
                    "citations": [],
                    "clusters": [],
                    "request_id": request_id,
                    "success": False,
                    "metadata": {},
                }

            # Use the service to determine processing mode based on extracted text size
            should_process_immediately = False  # Force async for all files to test progress updates
            logger.info(f"[File Upload {request_id}] Extracted {len(text)} chars of text")
            logger.info(
                f"[File Upload {request_id}] should_process_immediately returned: {should_process_immediately} (True=sync, False=async)"
            )

            if not should_process_immediately:
                from rq import Queue
                from redis import Redis
                from src.rq_worker import process_citation_task_direct

                redis_conn = Redis.from_url(REDIS_URL)
                queue = Queue("casestrainer", connection=redis_conn)

                job = queue.enqueue(
                    process_citation_task_direct,
                    args=(request_id, "file", {"file_path": file_path_for_worker, "filename": filename, "options": options}),
                    job_id=request_id,  # FIX: Use request_id as job_id to prevent caching duplicate requests
                    job_timeout=FILE_PROCESSING_TIMEOUT_MINUTES * 60,  # 6 minutes timeout (optimized)
                    result_ttl=86400,  # Keep results for 24 hours
                    failure_ttl=86400,  # Keep failed jobs for 24 hours
                )

                logger.info(f"[File Upload {request_id}] File processing task enqueued with job_id: {job.id}")

                # Heartbeat for file async path: reflect queued/verification progress via SSEProgressManager
                try:
                    from src.unified_input_processor import get_progress_manager
                    from src.progress_manager import ProgressTracker as SSETracker

                    sse_mgr = get_progress_manager()
                    sse_mgr.active_tasks[request_id] = SSETracker(request_id, total_steps=100)
                    sse_mgr.update_progress(request_id, 10, "queued", "Queued for background processing")

                    def _file_async_hb_and_watch():
                        try:
                            hb = 12
                            from src.verification_manager import VerificationManager

                            vm = VerificationManager()
                            while True:
                                time.sleep(1.0)
                                task = sse_mgr.active_tasks.get(request_id)
                                if not task:
                                    break
                                status = getattr(task, "status", "")
                                vstat = None
                                try:
                                    vstat = vm.get_verification_status(request_id) or vm.get_verification_status(job.id)
                                except Exception:
                                    vstat = None
                                if isinstance(vstat, dict):
                                    pct = int(vstat.get("progress_percent", 0))
                                    msg = vstat.get("current_message", "Verifying...")
                                    if pct > hb:
                                        hb = pct
                                    if pct >= 100 or str(vstat.get("state", "")).lower() in (
                                        "completed",
                                        "complete",
                                        "done",
                                        "success",
                                    ):
                                        sse_mgr.update_progress(request_id, 100, "completed", "Verification completed")
                                        break
                                    sse_mgr.update_progress(request_id, max(hb, min(95, pct)), "processing", msg)
                                    continue
                                if status in ("completed", "failed"):
                                    break
                                if hb < 60:
                                    hb = min(60, hb + 2)
                                    sse_mgr.update_progress(request_id, hb, "processing", "Processing in background...")
                        except Exception as hb_err:
                            logger.debug(f"[ASYNC-HB] Heartbeat update skipped: {hb_err}")

                    threading.Thread(target=_file_async_hb_and_watch, daemon=True).start()
                except Exception as hb_thread_err:
                    logger.debug(f"[ASYNC-HB] Failed to start heartbeat watcher thread: {hb_thread_err}")

                # Register verification immediately so polling endpoints return 200
                try:
                    from src.verification_manager import VerificationManager

                    vm = VerificationManager()
                    client_request_id = request.form.get("client_request_id")
                    total_cites = 0
                    # Register under client_request_id (early polling) -> maps to job_id=request_id
                    if client_request_id:
                        vm.register_verification(client_request_id, request_id, total_cites)
                    # Also register under backend request_id for later polling consistency
                    vm.register_verification(request_id, request_id, total_cites)
                except Exception as _e:
                    logger.warning(f"[File Upload {request_id}] Could not register verification immediately: {_e}")

                return {
                    "task_id": request_id,
                    "status": "processing",
                    "message": "File processing started",
                    "request_id": request_id,
                    "success": True,
                    "citations": [],
                    "clusters": [],
                    "cluster_sections": {"verified_strict": [], "verified_by_parallel": [], "unverified": [], "case_mismatch": [], "date_mismatch": [], "other": []},
                    "progress_endpoint": f"/casestrainer/api/analyze/progress/{request_id}",
                    "progress_stream": f"/casestrainer/api/analyze/progress-stream/{request_id}",
                    "metadata": {
                        "filename": filename,
                        "file_size": os.path.getsize(file_path_local),
                        "content_type": file.content_type,
                        "processing_mode": "queued",
                        "input_type": "file",
                    },
                }
            else:
                logger.info(f"[File Upload {request_id}] Processing file synchronously")

                if file_ext == "pdf":
                    # UNIFIED: Use same extractor as RQ worker and async paths (PyMuPDF via UnifiedTextExtractor)
                    # Ensures file upload and URL/async produce identical citation results
                    text = ""
                    logger.info(f"[File Upload {request_id}] Starting PDF text extraction from: {file_path_local}")
                    try:
                        from src.unified_text_extractor import extract_text_from_file_unified

                        text, method = extract_text_from_file_unified(file_path_local, verbose=True)
                        logger.info(f"[File Upload {request_id}] Extracted {len(text)} characters using {method}")
                        if text:
                            logger.info(f"[File Upload {request_id}] First 200 chars: {text[:200]}")
                        if not text or len(text.strip()) < 10:
                            text = f"[Error extracting PDF content: insufficient text from {method}]"
                    except Exception as e:
                        logger.error(f"[File Upload {request_id}] PDF extraction failed: {e}")
                        text = f"[Error extracting PDF content: {str(e)}]"
                elif file_ext == "docx":
                    try:
                        from docx import Document

                        doc = Document(file_path_local)
                        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
                    except ImportError:
                        text = f"[DOCX file content could not be extracted - {filename}]"
                        logger.warning(f"[File Upload {request_id}] python-docx not available for DOCX processing")
                    except Exception as e:
                        text = f"[Error extracting DOCX content: {str(e)}]"
                        logger.error(f"[File Upload {request_id}] DOCX processing error: {e}")
                elif file_ext == "doc":
                    text = f"[DOC files are not supported - {filename}. Please convert to DOCX or PDF.]"
                    logger.warning(f"[File Upload {request_id}] DOC file not supported: {filename}")
                elif file_ext in ["html", "htm", "xhtml"]:
                    try:
                        from bs4 import BeautifulSoup

                        with open(file_path_local, "r", encoding="utf-8", errors="ignore") as f:
                            html_content = f.read()
                        soup = BeautifulSoup(html_content, "html.parser")
                        for script in soup(["script", "style"]):
                            script.decompose()
                        text = soup.get_text(separator="\n", strip=True)
                        logger.info(
                            f"[File Upload {request_id}] Successfully extracted {len(text)} characters from HTML"
                        )
                    except ImportError:
                        text = f"[HTML file content could not be extracted - {filename}]"
                        logger.warning(f"[File Upload {request_id}] BeautifulSoup not available for HTML processing")
                    except Exception as e:
                        text = f"[Error extracting HTML content: {str(e)}]"
                        logger.error(f"[File Upload {request_id}] HTML processing error: {e}")
                elif file_ext == "xml":
                    try:
                        from bs4 import BeautifulSoup

                        with open(file_path_local, "r", encoding="utf-8", errors="ignore") as f:
                            xml_content = f.read()
                        soup = BeautifulSoup(xml_content, "xml")
                        for script in soup(["script", "style"]):
                            script.decompose()
                        text = soup.get_text(separator="\n", strip=True)
                        logger.info(
                            f"[File Upload {request_id}] Successfully extracted {len(text)} characters from XML"
                        )
                    except ImportError:
                        text = f"[XML file content could not be extracted - {filename}]"
                        logger.warning(f"[File Upload {request_id}] BeautifulSoup not available for XML processing")
                    except Exception as e:
                        text = f"[Error extracting XML content: {str(e)}]"
                        logger.error(f"[File Upload {request_id}] XML processing error: {e}")
                else:
                    with open(file_path_local, "r", encoding="utf-8", errors="replace") as f:
                        text = f.read()

                logger.info(f"[File Upload {request_id}] Processing extracted text synchronously")
                logger.info(f"[File Upload {request_id}] Text to process length: {len(text)} characters")
                logger.info(f"[File Upload {request_id}] Text preview: {text[:300]}...")
                # Progress heartbeat handled centrally in UnifiedInputProcessor where applicable

                # Use unified pipeline (same as async worker and main analyze sync path)
                import asyncio

                from src.unified_processing_pipeline import process_citations_unified

                clean_result = asyncio.run(
                    process_citations_unified(
                        text,
                        enable_verification=True,
                        enable_parallel_verification=True,
                    )
                )
                citations_list = list(clean_result.get("citations", []))
                clusters_list = list(clean_result.get("clusters", []))

                result = {
                    "citations": citations_list,
                    "clusters": clusters_list,
                    "statistics": {"total_citations": len(citations_list)},
                }

                logger.info(f"[File Upload {request_id}] Citation processing completed")
                logger.info(f"[File Upload {request_id}] Found {len(result.get('citations', []))} citations")
                logger.info(f"[File Upload {request_id}] Found {len(result.get('clusters', []))} clusters")

                formatted_result = {
                    "citations": result.get("citations", []),
                    "clusters": result.get("clusters", []),
                    "cluster_sections": compute_cluster_sections(result.get("clusters", [])),
                    "statistics": result.get("statistics", {}),
                    "request_id": request_id,
                    "success": True,
                    "metadata": {
                        "source": filename,
                        "text_length": len(text),
                        "processing_time": time.time(),
                        "processing_mode": "sync",
                    },
                }

                formatted_result["metadata"].update(
                    {
                        "filename": filename,
                        "file_size": os.path.getsize(file_path_local),
                        "content_type": file.content_type,
                        "processing_mode": "sync",
                    }
                )
                try:
                    # Mark completion
                    from src.unified_input_processor import get_progress_manager

                    sse_mgr = get_progress_manager()
                    sse_mgr.update_progress(request_id, 100, "completed", "Processing completed successfully")
                except Exception as completion_err:
                    logger.debug(f"[Request {request_id}] Completion progress update skipped: {completion_err}")

                return formatted_result

        except IOError as e:
            error_msg = f"Failed to process file: {str(e)}"
            logger.error(f"[File Upload {request_id}] {error_msg}", exc_info=True)
            return {
                "error": error_msg,
                "citations": [],
                "clusters": [],
                "request_id": request_id,
                "success": False,
                "metadata": {},
            }

        except Exception as e:
            error_msg = f"Failed to enqueue task: {str(e)}"
            logger.error(f"[File Upload {request_id}] {error_msg}", exc_info=True)

            try:
                if os.path.exists(file_path_local):
                    os.remove(file_path_local)
                    logger.info(f"[File Upload {request_id}] Cleaned up file after task enqueue failure")
            except Exception as cleanup_error:
                logger.error(f"[File Upload {request_id}] Failed to clean up file: {str(cleanup_error)}")

            return {
                "error": error_msg,
                "citations": [],
                "clusters": [],
                "request_id": request_id,
                "success": False,
                "metadata": {},
            }

    except Exception as e:
        logger.error(f"File upload error: {e}", exc_info=True)
        return {
            "error": f"Failed to process file: {str(e)}",
            "citations": [],
            "clusters": [],
            "request_id": request_id,
            "success": False,
            "metadata": {},
        }


def _handle_json_input(service, request_id, data=None):
    """
    Handle JSON input processing with CitationService integration

    Args:
        service: Instance of CitationService
        request_id: Unique ID for request tracking
        data: Optional pre-parsed JSON data (for testing or direct call)

    Returns:
        Dictionary with analysis results or error information
    """
    logger.warning(
        f"[JSON Input {request_id}] Deprecated legacy handler invoked; routing to canonical _analyze_impl"
    )
    return _analyze_impl(request)


async def _handle_form_input(service, request_id):
    """
    Handle form input processing with CitationService integration

    Args:
        service: Instance of CitationService
        request_id: Unique ID for request tracking
    """
    logger.warning(
        f"[Form Input {request_id}] Deprecated legacy handler invoked; routing to canonical _analyze_impl"
    )
    return _analyze_impl(request)


def _is_test_citation_text(text: str) -> bool:
    """Check if text contains known test citations that should be rejected."""
    return False


def _extract_test_pattern(text: str) -> str:
    """Extract the test pattern that was detected."""
    if not text:
        return "no_text"

    text_norm = text.strip().lower()

    if "smith v. jones" in text_norm and "123 f.3d 456" in text_norm:
        return "smith_v_jones_123_f3d_456"
    elif "123 f.3d 456" in text_norm:
        return "123_f3d_456_pattern"
    elif "999 u.s. 999" in text_norm:
        return "999_us_999_pattern"
    elif "test citation" in text_norm:
        return "test_citation_string"
    elif "sample citation" in text_norm:
        return "sample_citation_string"

    return "unknown_test_pattern"


def _is_test_environment_request(request) -> bool:
    """Check if the request appears to be from a test environment."""
    return False


def _is_test_url(url: str) -> bool:
    """Check if a URL is a test URL that should be rejected."""
    if not url:
        return False

    url_lower = url.lower()

    test_url_patterns = [
        "example.com",
        "test.com",
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "test.local",
        "dev.local",
        "staging.local",
        "mock.com",
        "fake.com",
        "dummy.com",
        "sample.com",
    ]

    for pattern in test_url_patterns:
        if pattern in url_lower:
            logger.warning(f"Test URL detected: {url} (pattern: {pattern})")
            return True

    problematic_protocols = [
        "file://",
        "ftp://",
        "mailto:",
        "tel:",
        "javascript:",
        "data:",
        "chrome://",
        "about:",
        "moz-extension://",
    ]

    for protocol in problematic_protocols:
        if url_lower.startswith(protocol):
            logger.warning(f"Problematic URL protocol detected: {url} (protocol: {protocol})")
            return True

    return False


def _validate_url(url: str) -> bool:
    """Validate that a URL is safe and properly formatted."""
    if not url or not isinstance(url, str):
        return False

    if len(url) > 2048:
        logger.warning(f"URL too long: {len(url)} characters")
        return False

    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)

        if parsed.scheme not in ["http", "https"]:
            logger.warning(f"Unsupported protocol: {parsed.scheme}")
            return False

        if _is_test_url(url):
            return False

        return True
    except Exception as e:
        logger.warning(f"URL validation error: {str(e)}")
        return False



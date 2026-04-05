"""
POST /analyze pipeline: request parsing, sync/async routing, response formatting.

Public entry: analyze_request(request) — behavior matches the former
vue_api_endpoints_updated._analyze_impl.
"""

import os
import uuid
import logging
import time
import json
from datetime import datetime
import re
import threading

from flask import jsonify, request
from werkzeug.utils import secure_filename

from src.config import (
    REDIS_URL,
    SYNC_REQUESTS_AS_ASYNC,
    ANALYZE_ASYNC_ONLY,
    ANALYZE_ALLOW_SYNC_OVERRIDE,
    FILE_PROCESSING_TIMEOUT_MINUTES,
    DATA_RETENTION_ASYNC_SECONDS,
)
from src.api.services.citation_service import CitationService
from src.extraction import extract_case_name_from_strict_context
from src.utils.strict_context_isolator import (
    find_all_citation_positions,
    get_strict_context_for_citation,
)
from src.metrics import record_document
from src.utils.response_enrichment import compute_cluster_sections

from src.api.services.response_format import (
    format_analyze_error_response,
    format_analyze_success_response,
)

logger = logging.getLogger(__name__)


def _is_test_environment_request(request) -> bool:
    """Check if the request appears to be from a test environment."""
    return False


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


def analyze_request(request):
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

                try:
                    if progress_tracker is not None:
                        progress_tracker.update_progress(
                            request_id, 90, "running", "Citations clustered successfully"
                        )
                    logger.info(f"[Request {request_id}] Progress update 4: Citations clustered")
                except Exception as progress_error:
                    logger.warning(f"[Request {request_id}] Progress update 4 failed: {progress_error}")

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
                    return format_analyze_error_response(
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

                return format_analyze_success_response(result, request_id, metadata, start_time)

            except Exception as e:
                error_msg = f"Error in unified processor: {str(e)}"
                logger.error(f"[Request {request_id}] {error_msg}", exc_info=True)
                return format_analyze_error_response(
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

        return format_analyze_error_response(
            "Invalid or missing input. Please check the Content-Type header and request format.",
            details=error_msg,
            status_code=400,
            request_id=request_id,
            metadata={**metadata, "error_type": "invalid_input", "error_details": error_msg},
        )

    except Exception as e:
        error_msg = f"Unexpected error in analyze endpoint: {str(e)}"
        logger.error(f"[Request {request_id}] {error_msg}", exc_info=True)

        return format_analyze_error_response(
            "An unexpected error occurred during analysis",
            details=str(e),
            status_code=500,
            request_id=request_id,
            metadata={**metadata, "error_type": "unexpected_error", "error_details": str(e)},
        )





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

            # IMPORTANT: When force_mode=async, do NOT synchronously extract text here.
            # OCR-based PDF extraction can take tens of seconds and would block the initial /analyze response,
            # defeating the purpose of async mode. The worker will perform extraction/verification.
            text = ""
            if str(force_mode or "").strip().lower() != "async":
                text = citation_service.extract_text_from_input(input_data)
                if text is None:
                    logger.error(f"[File Upload {request_id}] Failed to extract text from file")
                    return {
                        "error": "Failed to extract text from file",
                        "details": (
                            "The file could not be processed. If this is a PDF, it may require OCR (scanned PDF or "
                            "broken text encoding). Enable OCR or upload a text-searchable PDF."
                        ),
                        "citations": [],
                        "clusters": [],
                        "request_id": request_id,
                        "success": False,
                        "metadata": {},
                    }

            # Use the service to determine processing mode based on extracted text size
            should_process_immediately = False  # Force async for all files to test progress updates
            if text:
                logger.info(f"[File Upload {request_id}] Extracted {len(text)} chars of text")
            else:
                logger.info(f"[File Upload {request_id}] Skipping synchronous extraction (force_mode=async)")
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
                    result_ttl=DATA_RETENTION_ASYNC_SECONDS,
                    failure_ttl=DATA_RETENTION_ASYNC_SECONDS,
                )

                logger.info(f"[File Upload {request_id}] File processing task enqueued with job_id: {job.id}")

                # Heartbeat for file async path: reflect queued/verification progress via SSEProgressManager
                try:
                    from src.unified_input_processor import get_progress_manager
                    from src.progress_manager import ProgressTracker as SSETracker

                    sse_mgr = get_progress_manager()
                    sse_mgr.active_tasks[request_id] = SSETracker(request_id, total_steps=100)
                    queued_msg = "Queued for background processing"
                    if str(filename or "").lower().endswith(".pdf"):
                        queued_msg = (
                            "Queued for background processing (scanned/broken-text PDFs may require OCR and can take a few minutes)"
                        )
                    sse_mgr.update_progress(request_id, 10, "queued", queued_msg)

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

                response_msg = "File processing started"
                if str(filename or "").lower().endswith(".pdf"):
                    response_msg = (
                        "File processing started. If this PDF is scanned or has broken text encoding, OCR may be needed and can take a few minutes."
                    )

                return {
                    "task_id": request_id,
                    "status": "processing",
                    "message": response_msg,
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


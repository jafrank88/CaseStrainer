"""
Progress and SSE progress-stream routes for the Vue API.
"""

import json
import logging
import time

from flask import request, jsonify, Response

logger = logging.getLogger(__name__)


def register_progress_routes(bp):
    @bp.route("/analyze/progress/<request_id>", methods=["GET"])
    def analyze_progress(request_id):
        try:
            from src.unified_input_processor import get_progress_manager

            pm = get_progress_manager()
            data = pm.get_progress(request_id) if hasattr(pm, "get_progress") else pm.progress_store.get(request_id, {})
            return jsonify({"request_id": request_id, "status": "ok", "progress_data": data or {}})
        except Exception as e:
            return jsonify({"request_id": request_id, "status": "error", "error": str(e)}), 500

    @bp.route("/analyze/progress-stream/<request_id>", methods=["GET"])
    def analyze_progress_stream(request_id):
        def _stream():
            try:
                from time import sleep
                from src.unified_input_processor import get_progress_manager

                pm = get_progress_manager()
                for _ in range(60):
                    data = (
                        pm.get_progress(request_id)
                        if hasattr(pm, "get_progress")
                        else pm.progress_store.get(request_id, {})
                    )
                    payload = json.dumps({"request_id": request_id, "progress_data": data or {}})
                    yield f"data: {payload}\n\n"
                    sleep(1)
            except Exception:
                yield f"data: {json.dumps({'request_id': request_id, 'progress_data': {}})}\n\n"

        return Response(_stream(), mimetype="text/event-stream")

    @bp.route("/processing_progress", methods=["GET"])
    def processing_progress():
        """Get current processing progress from ProgressTracker or global progress manager."""
        request_id = request.args.get("request_id") or request.args.get("task_id")

        if not request_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Missing request_id or task_id parameter",
                        "processed_citations": 0,
                        "total_citations": 0,
                        "is_complete": False,
                    }
                ),
                400,
            )

        try:
            from src.unified_input_processor import get_progress_manager

            global_progress_mgr = get_progress_manager()

            if request_id in global_progress_mgr.active_tasks:
                progress_data = global_progress_mgr.get_progress(request_id)
                logger.debug(f"[Progress API] Found progress in global manager: {progress_data}")

                if progress_data and "error" not in progress_data:
                    pct = progress_data.get("progress", 0)
                    status_str = str(progress_data.get("status", "processing"))
                    is_complete = status_str.lower() in ("complete", "completed", "done", "success") or pct >= 100
                    return jsonify(
                        {
                            "status": "success",
                            "request_id": request_id,
                            "progress_percent": pct,
                            "current_step": int(pct),
                            "total_steps": 100,
                            "current_message": progress_data.get("message", "Processing..."),
                            "status_detail": status_str,
                            "is_complete": is_complete,
                            "processed_citations": int(pct),
                            "total_citations": 100,
                        }
                    )
            return jsonify(
                {
                    "status": "pending",
                    "request_id": request_id,
                    "progress_percent": 0,
                    "current_step": 0,
                    "total_steps": 100,
                    "current_message": "Waiting for processing to start...",
                    "status_detail": "pending",
                    "is_complete": False,
                    "processed_citations": 0,
                    "total_citations": 100,
                }
            )

        except Exception as e:
            logger.error(f"Error getting progress for {request_id}: {e}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": f"Failed to get progress: {str(e)}",
                        "request_id": request_id,
                        "processed_citations": 0,
                        "total_citations": 0,
                        "is_complete": False,
                    }
                ),
                500,
            )

    @bp.route("/analyze/progress-stream/<request_id>", methods=["GET"])
    def progress_stream(request_id):
        """SSE endpoint for real-time progress updates."""

        def generate_progress_stream():
            try:
                yield 'data: {"type": "connected", "message": "Progress stream connected"}\n\n'
                from src.unified_input_processor import get_progress_manager

                sse_mgr = get_progress_manager()
                start_time = time.time()
                last_pct = -1
                while True:
                    time.sleep(0.5)
                    pdata = sse_mgr.get_progress(request_id)
                    if not pdata or "error" in pdata:
                        if time.time() - start_time > 30:
                            yield 'data: {"type": "timeout", "message": "No progress available"}\n\n'
                            break
                        continue
                    pct = int(pdata.get("progress", 0))
                    if pct != last_pct:
                        last_pct = pct
                        progress_event = {
                            "type": "progress",
                            "data": {
                                "step": pdata.get("status", "processing"),
                                "progress": pct,
                                "message": pdata.get("message", "Processing..."),
                                "total_steps": 100,
                                "current_step": pct,
                            },
                        }
                        yield f"data: {json.dumps(progress_event)}\n\n"
                    if pct >= 100 or str(pdata.get("status", "")).lower() in ("complete", "completed", "done", "success"):
                        yield 'data: {"type": "complete", "message": "Processing completed successfully!"}\n\n'
                        break
                    try:
                        sse_mgr.cleanup_task(request_id)
                    except Exception:
                        logger.debug("Suppressed exception", exc_info=True)
            except Exception as e:
                logger.error(f"Error in progress stream for {request_id}: {e}")
                yield f'data: {{"type": "error", "message": "Progress stream error: {str(e)}"}}\n\n'

        return Response(
            generate_progress_stream(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Headers": "Cache-Control",
            },
        )

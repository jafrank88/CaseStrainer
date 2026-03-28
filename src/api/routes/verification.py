"""
Verification stream and status routes for the Vue API.
"""

import json
import logging
import time
from datetime import datetime

from flask import jsonify, Response

logger = logging.getLogger(__name__)


def register_verification_routes(bp):
    @bp.route("/analyze/verification-stream/<request_id>")
    def verification_stream(request_id):
        """Stream verification progress and results via SSE."""
        try:
            from src.verification_manager import VerificationManager

            verification_manager = VerificationManager()

            def generate():
                try:
                    connection_data = {
                        "type": "connection_established",
                        "request_id": request_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    yield f"data: {json.dumps(connection_data)}\n\n"

                    last_status = None
                    last_progress = 0

                    while True:
                        try:
                            status = verification_manager.get_verification_status(request_id)

                            if not status:
                                error_data = {
                                    "type": "error",
                                    "message": "Verification not found or not started",
                                    "request_id": request_id,
                                    "timestamp": datetime.utcnow().isoformat(),
                                }
                                yield f"data: {json.dumps(error_data)}\n\n"
                                break

                            status_changed = last_status != status.get("status") or last_progress != status.get("progress", 0)

                            if status_changed:
                                event_data = {
                                    "type": "verification_status",
                                    "request_id": request_id,
                                    "status": status.get("status"),
                                    "progress": status.get("progress", 0),
                                    "citations_processed": status.get("citations_processed", 0),
                                    "citations_count": status.get("citations_count", 0),
                                    "current_method": status.get("current_method"),
                                    "timestamp": datetime.utcnow().isoformat(),
                                }
                                yield f"data: {json.dumps(event_data)}\n\n"
                                last_status = status.get("status")
                                last_progress = status.get("progress", 0)

                            if status.get("status") in ["completed", "failed"]:
                                if status.get("status") == "completed":
                                    results = verification_manager.get_verification_results(request_id)
                                    event_data = {
                                        "type": "verification_complete",
                                        "request_id": request_id,
                                        "results": results or {},
                                        "timestamp": datetime.utcnow().isoformat(),
                                    }
                                    if not results:
                                        event_data["message"] = "Verification completed but results not available"
                                else:
                                    event_data = {
                                        "type": "verification_failed",
                                        "request_id": request_id,
                                        "error_message": status.get("error_message", "Unknown error"),
                                        "timestamp": datetime.utcnow().isoformat(),
                                    }
                                yield f"data: {json.dumps(event_data)}\n\n"
                                break

                            time.sleep(1)

                        except Exception as e:
                            logger.error(f"Error in verification stream for {request_id}: {e}")
                            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'request_id': request_id})}\n\n"
                            break

                    yield f"data: {json.dumps({'type': 'stream_end', 'request_id': request_id, 'timestamp': datetime.utcnow().isoformat()})}\n\n"

                except Exception as e:
                    logger.error(f"Fatal error in verification stream for {request_id}: {e}")
                    yield f"data: {json.dumps({'type': 'fatal_error', 'message': str(e), 'request_id': request_id})}\n\n"

            return Response(
                generate(),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Headers": "Cache-Control",
                },
            )

        except Exception as e:
            logger.error(f"Failed to start verification stream for {request_id}: {e}")
            return jsonify({"error": str(e), "request_id": request_id}), 500

    @bp.route("/analyze/verification-status/<request_id>")
    def verification_status(request_id):
        """Get current verification status for a request."""
        try:
            from src.verification_manager import VerificationManager

            verification_manager = VerificationManager()
            status = verification_manager.get_verification_status(request_id)

            if not status:
                return jsonify({"error": "Verification not found", "request_id": request_id}), 404

            return jsonify({"request_id": request_id, "status": status, "timestamp": datetime.utcnow().isoformat()})

        except Exception as e:
            logger.error(f"Failed to get verification status for {request_id}: {e}")
            return jsonify({"error": str(e), "request_id": request_id}), 500

    @bp.route("/analyze/verification-results/<request_id>")
    def verification_results(request_id):
        """Get verification results for a completed request."""
        try:
            from src.verification_manager import VerificationManager

            verification_manager = VerificationManager()
            results = verification_manager.get_verification_results(request_id)

            if not results:
                return jsonify({"error": "Verification results not available", "request_id": request_id}), 404

            return jsonify({"request_id": request_id, "results": results, "timestamp": datetime.utcnow().isoformat()})

        except Exception as e:
            logger.error(f"Failed to get verification results for {request_id}: {e}")
            return jsonify({"error": str(e), "request_id": request_id}), 500

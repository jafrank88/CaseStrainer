"""
Example integration of SimplifiedCitationProcessor into existing API endpoints.

This file demonstrates how to replace the complex current implementation
with the simplified unified processor.
"""

from flask import request, jsonify
import logging
import os
from typing import Dict, Any

# Import the simplified processor
from src.simplified_citation_processor import create_processor, ProcessingConfig, ProcessingMode
from src.config import REDIS_URL

logger = logging.getLogger(__name__)


class SimplifiedAPIHandler:
    """
    Handler class that demonstrates integration of SimplifiedCitationProcessor
    with the existing Flask API structure.
    """

    def __init__(self):
        # Default configuration
        self.default_config = ProcessingConfig(
            enable_verification=True,
            enable_clustering=True,
            max_citations=1000,
            timeout_seconds=300,
            cache_results=True,
            async_threshold_kb=5,
        )

    def analyze_text(self) -> Dict[str, Any]:
        """
        Simplified analyze endpoint - replaces the complex current implementation.

        This single method replaces:
        - Multiple processing paths in vue_api_endpoints.py
        - Complex routing through UnifiedInputProcessor
        - Duplicate sync/async logic
        """
        try:
            # Extract request data
            data = request.get_json() or {}
            text = data.get("text", "")
            enable_verification = data.get("enable_verification", True)

            if not text:
                return jsonify({"error": "No text provided", "message": "Please provide text to analyze"}), 400

            # Create processor with request-specific configuration
            processor = create_processor(
                enable_verification=enable_verification,
                enable_clustering=data.get("enable_clustering", True),
                max_citations=data.get("max_citations", 1000),
                timeout_seconds=data.get("timeout_seconds", 300),
                cache_results=data.get("cache_results", True),
            )

            # Prepare input data
            input_data = {"type": "text", "text": text}

            # Generate request ID
            import uuid

            request_id = f"api_{uuid.uuid4().hex[:12]}"

            # Process the request
            logger.info(f"[{request_id}] Starting analysis with simplified processor")
            result = processor.process(input_data, request_id)

            # Format response based on processing mode
            if result.mode == ProcessingMode.ASYNCHRONOUS:
                return (
                    jsonify(
                        {
                            "status": "processing",
                            "task_id": result.task_id,
                            "message": "Large document detected - processing asynchronously",
                            "processing_mode": "async",
                            "request_id": request_id,
                        }
                    ),
                    202,
                )
            else:
                # Synchronous result
                return (
                    jsonify(
                        {
                            "status": "completed",
                            "processing_mode": "sync",
                            "request_id": request_id,
                            "results": {
                                "citations": result.citations,
                                "clusters": result.clusters,
                                "verification_results": result.verification_results,
                            },
                            "metadata": {
                                "processing_time": result.processing_time,
                                "citation_count": len(result.citations),
                                "cluster_count": len(result.clusters),
                                "verification_enabled": enable_verification,
                            },
                        }
                    ),
                    200,
                )

        except Exception as e:
            logger.error(f"Error in analyze_text: {str(e)}", exc_info=True)
            return jsonify({"error": "Processing failed", "message": str(e)}), 500

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Simplified task status endpoint.

        This replaces the complex status checking logic spread across
        multiple files and provides a unified interface.
        """
        try:
            from rq import Queue
            from redis import Redis
            from rq.job import Job

            # Connect to Redis
            redis_conn = Redis.from_url(REDIS_URL)
            queue = Queue("casestrainer", connection=redis_conn)

            # Get job
            job = Job.fetch(task_id, connection=redis_conn)

            # Prepare response
            response = {
                "task_id": task_id,
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "is_finished": job.is_finished,
                "is_failed": job.is_failed,
                "is_started": job.is_started,
                "is_queued": job.is_queued,
            }

            # Add progress information if available
            if job.is_finished and not job.is_failed:
                result = job.result
                if isinstance(result, dict):
                    response.update(
                        {
                            "result": {
                                "citations": result.get("citations", []),
                                "clusters": result.get("clusters", []),
                                "verification_results": result.get("verification_results"),
                                "metadata": result.get("metadata", {}),
                            }
                        }
                    )

            # Add error information if failed
            if job.is_failed:
                response["error"] = str(job.exc_info)

            return jsonify(response), 200

        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {str(e)}")
            return jsonify({"error": "Task not found", "message": f"Could not find task with ID: {task_id}"}), 404

    def process_file(self) -> Dict[str, Any]:
        """
        Simplified file processing endpoint.

        This demonstrates how the unified processor handles file inputs
        without the complex routing logic.
        """
        try:
            # Check if file was uploaded
            if "file" not in request.files:
                return jsonify({"error": "No file provided", "message": "Please upload a file to process"}), 400

            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "No file selected", "message": "Please select a file to upload"}), 400

            # Create processor for file processing
            processor = create_processor(
                enable_verification=request.form.get("enable_verification", True),
                timeout_seconds=600,  # Longer timeout for files
            )

            # Save file temporarily
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
                file.save(tmp_file.name)
                tmp_path = tmp_file.name

            try:
                # Prepare input data
                input_data = {"type": "file", "file_path": tmp_path}

                # Generate request ID
                import uuid

                request_id = f"file_{uuid.uuid4().hex[:12]}"

                # Process the file
                logger.info(f"[{request_id}] Processing file: {file.filename}")
                result = processor.process(input_data, request_id)

                # Clean up temporary file
                os.unlink(tmp_path)

                # Return response
                if result.mode == ProcessingMode.ASYNCHRONOUS:
                    return (
                        jsonify(
                            {
                                "status": "processing",
                                "task_id": result.task_id,
                                "message": "File is being processed asynchronously",
                                "filename": file.filename,
                                "request_id": request_id,
                            }
                        ),
                        202,
                    )
                else:
                    return (
                        jsonify(
                            {
                                "status": "completed",
                                "filename": file.filename,
                                "results": {
                                    "citations": result.citations,
                                    "clusters": result.clusters,
                                    "verification_results": result.verification_results,
                                },
                                "metadata": {
                                    "processing_time": result.processing_time,
                                    "citation_count": len(result.citations),
                                    "request_id": request_id,
                                },
                            }
                        ),
                        200,
                    )

            except Exception as e:
                # Clean up on error
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise e

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}", exc_info=True)
            return jsonify({"error": "File processing failed", "message": str(e)}), 500


# Example Flask blueprint using the simplified handler
def create_simplified_blueprint():
    """
    Create a Flask blueprint that uses the simplified processor.

    This replaces the complex vue_api.py and citation_api.py blueprints
    with a single, unified blueprint.
    """
    from flask import Blueprint

    simplified_api = Blueprint("simplified_api", __name__)
    handler = SimplifiedAPIHandler()

    @simplified_api.route("/analyze", methods=["POST"])
    def analyze():
        return handler.analyze_text()

    @simplified_api.route("/analyze/file", methods=["POST"])
    def analyze_file():
        return handler.process_file()

    @simplified_api.route("/task/<task_id>", methods=["GET"])
    def get_task_status(task_id):
        return handler.get_task_status(task_id)

    @simplified_api.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "healthy", "processor": "simplified", "version": "1.0.0"}), 200

    return simplified_api


# Migration helper functions
def migrate_to_simplified_processor():
    """
    Helper function to gradually migrate from legacy to simplified processor.

    This can be used in the main application to switch between processors
    based on configuration or percentage-based rollout.
    """
    use_simplified = os.getenv("USE_SIMPLIFIED_PROCESSOR", "false").lower() == "true"
    percentage = float(os.getenv("SIMPLIFIED_PROCESSOR_PERCENTAGE", "0"))

    if use_simplified:
        return True, 1.0  # 100% simplified

    if percentage > 0:
        import random

        if random.random() < percentage / 100:
            return True, percentage / 100

    return False, 0


# Example usage in main application
def register_api_routes(app):
    """
    Register API routes with gradual migration support.
    """

    should_use_simplified, rollout_percentage = migrate_to_simplified_processor()

    if should_use_simplified:
        # Use simplified processor
        simplified_bp = create_simplified_blueprint()
        app.register_blueprint(simplified_bp, url_prefix="/api/v2")
        logger.info(f"Registered simplified API (rollout: {rollout_percentage:.0%})")

        # Optionally register legacy API alongside
        if rollout_percentage < 1.0:
            from src.vue_api_endpoints import vue_api

            app.register_blueprint(vue_api, url_prefix="/api/v1")
            logger.info("Registered legacy API for fallback")
    else:
        # Use legacy processor
        from src.vue_api_endpoints import vue_api

        app.register_blueprint(vue_api, url_prefix="/api")
        logger.info("Using legacy API processor")


# Performance comparison utility
def compare_processors(text: str, enable_verification: bool = True) -> Dict[str, Any]:
    """
    Compare performance between legacy and simplified processors.

    This utility can be used during migration to ensure the simplified
    processor produces equivalent results with better performance.
    """
    import time

    results = {}

    # Test simplified processor
    start_time = time.time()
    simplified_processor = create_processor(
        enable_verification=enable_verification, cache_results=False  # Disable cache for fair comparison
    )

    simplified_result = simplified_processor.process({"type": "text", "text": text}, "comparison_test")
    simplified_time = time.time() - start_time

    results["simplified"] = {
        "processing_time": simplified_time,
        "citation_count": len(simplified_result.citations),
        "cluster_count": len(simplified_result.clusters),
        "mode": simplified_result.mode.value,
    }

    # Test legacy processor (if available)
    try:
        from src.unified_input_processor import UnifiedInputProcessor

        start_time = time.time()
        legacy_processor = UnifiedInputProcessor()

        # Simulate the legacy processing path
        legacy_result = legacy_processor.process_any_input(text, "text", "comparison_test", "test")
        legacy_time = time.time() - start_time

        results["legacy"] = {
            "processing_time": legacy_time,
            "citation_count": len(legacy_result.get("citations", [])),
            "has_verification": "verification_results" in legacy_result,
        }

        # Calculate improvement
        if legacy_time > 0:
            results["improvement"] = {
                "time_reduction_percent": ((legacy_time - simplified_time) / legacy_time) * 100,
                "faster_by": legacy_time - simplified_time,
            }

    except Exception as e:
        results["legacy_error"] = str(e)

    return results


if __name__ == "__main__":
    # Example usage
    sample_text = """
    In Smith v. Jones, 123 U.S. 456 (2020), the Supreme Court ruled that...
    The case of Johnson v. Smith, 456 F.2d 789 (9th Cir. 2021) further established...
    According to Brown v. Board of Education, 347 U.S. 483 (1954)...
    """

    comparison = compare_processors(sample_text)
    print("Performance Comparison:")
    print(f"Simplified: {comparison['simplified']['processing_time']:.2f}s")
    if "legacy" in comparison:
        print(f"Legacy: {comparison['legacy']['processing_time']:.2f}s")
        print(f"Improvement: {comparison['improvement']['time_reduction_percent']:.1f}% faster")

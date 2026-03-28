"""
Task status (RQ job polling) route for the Vue API.
"""

import json
import logging
import re
from datetime import datetime

from flask import jsonify

from src.config import WEBSEARCH_TIMEOUT, REDIS_URL
from src.utils.response_enrichment import compute_cluster_sections, extract_display_base_citation

logger = logging.getLogger(__name__)


def register_task_status_routes(bp):
    @bp.route("/task_status/<task_id>", methods=["GET"])
    def task_status(task_id):
        """Check the status of a queued task"""
        logger.info(f"Checking status for task_id: {task_id}")

        try:
            from rq import Queue
            from redis import Redis

            if not REDIS_URL:
                logger.error("REDIS_URL environment variable not set")
                return (
                    jsonify(
                        {
                            "error": "Server configuration error",
                            "details": "Redis URL not configured",
                            "task_id": task_id,
                            "citations": [],
                            "clusters": [],
                        }
                    ),
                    500,
                )

            redis_conn = Redis.from_url(
                REDIS_URL, socket_connect_timeout=WEBSEARCH_TIMEOUT, socket_timeout=WEBSEARCH_TIMEOUT
            )

            try:
                redis_conn.ping()
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                return (
                    jsonify(
                        {
                            "error": "Failed to connect to task queue",
                            "details": str(e),
                            "task_id": task_id,
                            "citations": [],
                            "clusters": [],
                        }
                    ),
                    500,
                )

            queue = Queue("casestrainer", connection=redis_conn)
            job = queue.fetch_job(task_id)

            if not job:
                try:
                    from rq.job import Job

                    job = Job.fetch(task_id, connection=redis_conn)
                except Exception as fetch_error:
                    logger.warning(f"Job {task_id} not found in queue or Redis: {fetch_error}")
                    try:
                        result_key = f"verification:result:{task_id}"
                        result_data = redis_conn.get(result_key)
                        if result_data:
                            payload = result_data.decode("utf-8") if isinstance(result_data, bytes) else str(result_data)
                            result = json.loads(payload)
                            return jsonify(
                                {
                                    "status": "completed",
                                    "task_id": task_id,
                                    "is_finished": True,
                                    "citations": result.get("citations", []),
                                    "clusters": result.get("clusters", []),
                                    "cluster_sections": compute_cluster_sections(result.get("clusters", [])),
                                    "statistics": result.get("statistics", {}),
                                    "metadata": result.get("metadata", {}),
                                    "success": True,
                                }
                            )
                    except Exception as redis_error:
                        logger.error(f"Could not retrieve verification result from Redis: {redis_error}")
                    return jsonify({"error": "Task not found", "task_id": task_id, "citations": [], "clusters": []}), 404

            result = None
            if job.is_finished:
                try:
                    result = job.result
                except Exception as e:
                    logger.error(f"Error getting job result: {e}")

            def _load_best_stored_result():
                verification_result = None
                try:
                    result_key = f"verification:result:{task_id}"
                    result_data = redis_conn.get(result_key)
                    if result_data:
                        payload = result_data.decode("utf-8") if isinstance(result_data, bytes) else str(result_data)
                        verification_result = json.loads(payload)
                except Exception as redis_fallback_err:
                    logger.warning(f"[TASK_STATUS] Failed to retrieve verification result: {redis_fallback_err}")

                task_result = None
                try:
                    task_result_key = f"task_result:{task_id}"
                    task_result_data = redis_conn.get(task_result_key)
                    if task_result_data:
                        payload = task_result_data.decode("utf-8") if isinstance(task_result_data, bytes) else str(task_result_data)
                        task_result = json.loads(payload)
                except Exception as task_result_err:
                    logger.warning(f"[TASK_STATUS] Failed to retrieve task result: {task_result_err}")

                rq_result = None
                try:
                    rq_result_key = f"rq:job:{task_id}:result"
                    rq_result_data = redis_conn.get(rq_result_key)
                    if rq_result_data:
                        payload = rq_result_data.decode("utf-8") if isinstance(rq_result_data, bytes) else str(rq_result_data)
                        rq_result = json.loads(payload)
                except Exception as rq_result_err:
                    logger.warning(f"[TASK_STATUS] Failed to retrieve rq job result: {rq_result_err}")

                rq_hash_result = None
                try:
                    job_key = f"rq:job:{task_id}"
                    job_hash_result = redis_conn.hget(job_key, "result")
                    if job_hash_result:
                        payload = job_hash_result.decode("utf-8") if isinstance(job_hash_result, bytes) else str(job_hash_result)
                        rq_hash_result = json.loads(payload)
                except Exception as rq_hash_result_err:
                    logger.warning(f"[TASK_STATUS] Failed to retrieve rq job hash result: {rq_hash_result_err}")

                def _unwrap_result_payload(payload):
                    if not isinstance(payload, dict):
                        return {}
                    inner = payload.get("result")
                    return inner if isinstance(inner, dict) else payload

                def _extract_array_counts(payload):
                    data = _unwrap_result_payload(payload)
                    if not isinstance(data, dict):
                        return (0, 0)
                    citations = data.get("citations", []) if isinstance(data.get("citations", []), list) else []
                    clusters = data.get("clusters", []) if isinstance(data.get("clusters", []), list) else []
                    return (len(citations), len(clusters))

                def _extract_expected_counts(payload):
                    data = _unwrap_result_payload(payload)
                    if not isinstance(data, dict):
                        return (0, 0)
                    metadata = data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {}
                    statistics = data.get("statistics", {}) if isinstance(data.get("statistics", {}), dict) else {}
                    citation_count = (
                        metadata.get("citation_count")
                        or metadata.get("citations_count")
                        or statistics.get("total_citations")
                        or 0
                    )
                    cluster_count = (
                        metadata.get("cluster_count")
                        or metadata.get("clusters_count")
                        or statistics.get("total_clusters")
                        or 0
                    )
                    try:
                        citation_count = int(citation_count or 0)
                    except Exception:
                        citation_count = 0
                    try:
                        cluster_count = int(cluster_count or 0)
                    except Exception:
                        cluster_count = 0
                    return (citation_count, cluster_count)

                def _result_score(payload):
                    data = _unwrap_result_payload(payload)
                    citations = data.get("citations", []) if isinstance(data.get("citations", []), list) else []
                    clusters = data.get("clusters", []) if isinstance(data.get("clusters", []), list) else []
                    expected_citations, expected_clusters = _extract_expected_counts(payload)
                    has_success_flag = 1 if isinstance(payload, dict) and (payload.get("status") in ["success", "completed"] or payload.get("success") is True) else 0
                    return (
                        len(citations) + len(clusters),
                        len(citations),
                        len(clusters),
                        expected_citations + expected_clusters,
                        expected_citations,
                        expected_clusters,
                        has_success_flag,
                    )

                candidates = [task_result, rq_result, rq_hash_result, verification_result, result]
                best_result = None
                best_score = (-1, -1, -1, -1, -1, -1, -1)
                for candidate in candidates:
                    score = _result_score(candidate)
                    if score > best_score:
                        best_result = candidate
                        best_score = score

                actual_result = _unwrap_result_payload(best_result)
                citations = actual_result.get("citations", []) or []
                clusters = actual_result.get("clusters", []) or []

                if (not citations and not clusters) and isinstance(result, dict):
                    result_unwrapped = _unwrap_result_payload(result)
                    result_citations = result_unwrapped.get("citations", []) or []
                    result_clusters = result_unwrapped.get("clusters", []) or []
                    if result_citations or result_clusters:
                        actual_result = result_unwrapped
                        citations = result_citations
                        clusters = result_clusters
                        best_result = result

                if (not citations and not clusters):
                    for fallback in (task_result, rq_result, verification_result):
                        fallback_result = _unwrap_result_payload(fallback)
                        fallback_citations = fallback_result.get("citations", []) or []
                        fallback_clusters = fallback_result.get("clusters", []) or []
                        if fallback_citations or fallback_clusters:
                            actual_result = fallback_result
                            citations = fallback_citations
                            clusters = fallback_clusters
                            best_result = fallback
                            break

                is_success = (
                    (best_result and isinstance(best_result, dict) and (best_result.get("status") in ["success", "completed"] or best_result.get("success") is True))
                    or (verification_result and isinstance(verification_result, dict) and (verification_result.get("status") in ["success", "completed"] or verification_result.get("success") is True))
                    or (citations or clusters)
                )

                return {
                    "result": best_result,
                    "actual_result": actual_result,
                    "citations": citations,
                    "clusters": clusters,
                    "verification_result": verification_result,
                    "task_result": task_result,
                    "rq_result": rq_result,
                    "rq_hash_result": rq_hash_result,
                    "is_success": is_success,
                }

            stored_result_info = _load_best_stored_result()

            completed_progress_payload = None
            try:
                progress_key = f"progress:{task_id}"
                raw = redis_conn.get(progress_key)
                if raw:
                    payload = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
                    parsed_progress = json.loads(payload)
                    if isinstance(parsed_progress, dict) and parsed_progress.get("status") == "completed":
                        completed_progress_payload = parsed_progress
            except Exception:
                completed_progress_payload = None

            completed_progress_citation_count = 0
            completed_progress_cluster_count = 0
            if isinstance(completed_progress_payload, dict):
                progress_citation_count = completed_progress_payload.get("citations_count")
                progress_cluster_count = completed_progress_payload.get("clusters_count")
                if progress_citation_count is None:
                    progress_citation_count = completed_progress_payload.get("total_citations")
                try:
                    completed_progress_citation_count = int(progress_citation_count or 0)
                except Exception:
                    completed_progress_citation_count = 0
                try:
                    completed_progress_cluster_count = int(progress_cluster_count or 0)
                except Exception:
                    completed_progress_cluster_count = 0

            if (
                (completed_progress_citation_count > 0 or completed_progress_cluster_count > 0)
                and not (stored_result_info["citations"] or stored_result_info["clusters"])
            ):
                for preferred_key in ("task_result", "rq_result", "rq_hash_result", "verification_result"):
                    candidate_payload = stored_result_info.get(preferred_key)
                    candidate_citations, candidate_clusters = _extract_array_counts(candidate_payload)
                    expected_citations, expected_clusters = _extract_expected_counts(candidate_payload)
                    if candidate_citations or candidate_clusters:
                        stored_result_info["result"] = candidate_payload
                        stored_result_info["actual_result"] = _unwrap_result_payload(candidate_payload)
                        stored_result_info["citations"] = stored_result_info["actual_result"].get("citations", []) or []
                        stored_result_info["clusters"] = stored_result_info["actual_result"].get("clusters", []) or []
                        stored_result_info["is_success"] = True
                        break
                    if (
                        expected_citations == completed_progress_citation_count
                        and expected_clusters == completed_progress_cluster_count
                        and (expected_citations > 0 or expected_clusters > 0)
                    ):
                        logger.warning(
                            f"[TASK_STATUS] Completed progress shows non-empty result for {task_id}, but {preferred_key} payload arrays are empty despite matching counts"
                        )

            if job.is_finished:
                result = stored_result_info["result"] or result
                actual_result = stored_result_info["actual_result"]
                citations = stored_result_info["citations"]
                clusters = stored_result_info["clusters"]
                verification_result = stored_result_info["verification_result"]
                is_success = stored_result_info["is_success"]

                has_materialized_results = bool(citations or clusters)

                if is_success and not has_materialized_results:
                    explicit_empty_result = False
                    authoritative_counts = []
                    if isinstance(actual_result, dict):
                        metadata = actual_result.get("metadata", {})
                        statistics = actual_result.get("statistics", {})
                        total_from_stats = statistics.get("total_citations")
                        total_from_meta = metadata.get("citation_count")
                        for count_value in (total_from_stats, total_from_meta):
                            if count_value is None:
                                continue
                            try:
                                authoritative_counts.append(int(count_value))
                            except Exception:
                                pass

                    if isinstance(completed_progress_payload, dict):
                        progress_citation_count = completed_progress_citation_count
                        progress_cluster_count = completed_progress_cluster_count
                        if progress_citation_count > 0 or progress_cluster_count > 0:
                            explicit_empty_result = False
                        authoritative_counts.extend([progress_citation_count, progress_cluster_count])

                    normalized_authoritative_counts = [count for count in authoritative_counts if isinstance(count, int) and count >= 0]
                    if normalized_authoritative_counts:
                        explicit_empty_result = all(count == 0 for count in normalized_authoritative_counts)

                    if not explicit_empty_result:
                        progress = 0
                        message = "Finalizing results..."
                        current_message = "Finalizing results..."
                        try:
                            progress_key = f"progress:{task_id}"
                            raw = redis_conn.get(progress_key)
                            if raw:
                                payload = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
                                prog_data = json.loads(payload)
                                progress = int(prog_data.get("progress") or prog_data.get("progress_percent") or 0)
                                message = prog_data.get("message") or message
                                current_message = prog_data.get("current_step") or message
                        except Exception:
                            pass

                        return jsonify(
                            {
                                "status": "processing",
                                "task_id": task_id,
                                "message": message,
                                "current_message": current_message,
                                "progress": progress,
                                "progress_percent": progress,
                                "success": True,
                                "citations": [],
                                "clusters": [],
                            }
                        )

                if is_success:
                    metadata = actual_result.get("metadata", {})
                    if verification_result and "metadata" in verification_result:
                        metadata = {**metadata, **verification_result.get("metadata", {})}
                    for c in (citations or []):
                        if isinstance(c, dict) and not c.get("display_base_citation"):
                            raw = c.get("citation") or c.get("text") or ""
                            c["display_base_citation"] = extract_display_base_citation(raw)
                    return jsonify(
                        {
                            "status": "completed",
                            "task_id": task_id,
                            "is_finished": True,
                            "citations": citations,
                            "clusters": clusters,
                            "cluster_sections": compute_cluster_sections(clusters),
                            "statistics": actual_result.get("statistics", {}),
                            "metadata": metadata,
                            "success": True,
                        }
                    )
                else:
                    error_msg = (result.get("error", "Processing failed") if result and isinstance(result, dict) else None) or (f"Job failed with exception: {job.exc_info}" if job.exc_info else "Unknown error")
                    return jsonify(
                        {"status": "failed", "task_id": task_id, "error": error_msg, "success": False, "citations": [], "clusters": []}
                    )

            elif job.is_failed:
                error_msg = str(job.exc_info) if job.exc_info else "Job failed without exception info"
                return jsonify({"status": "failed", "task_id": task_id, "error": error_msg, "success": False, "citations": [], "clusters": []})

            elif job.is_started:
                if stored_result_info["is_success"] and (stored_result_info["citations"] or stored_result_info["clusters"]):
                    actual_result = stored_result_info["actual_result"]
                    citations = stored_result_info["citations"]
                    clusters = stored_result_info["clusters"]
                    verification_result = stored_result_info["verification_result"]
                    metadata = actual_result.get("metadata", {})
                    if verification_result and "metadata" in verification_result:
                        metadata = {**metadata, **verification_result.get("metadata", {})}
                    return jsonify(
                        {
                            "status": "completed",
                            "task_id": task_id,
                            "is_finished": True,
                            "citations": citations,
                            "clusters": clusters,
                            "cluster_sections": compute_cluster_sections(clusters),
                            "statistics": actual_result.get("statistics", {}),
                            "metadata": metadata,
                            "success": True,
                        }
                    )

                try:
                    from src.verification_manager import VerificationManager
                    vm = VerificationManager()
                    vstatus = vm.get_verification_status(task_id)
                except Exception:
                    vstatus = None

                started_at = job.started_at
                elapsed_time = None
                elapsed_seconds = None
                if started_at:
                    if isinstance(started_at, str):
                        started_at = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
                    elapsed_seconds = (datetime.now(started_at.tzinfo) - started_at).total_seconds() if started_at.tzinfo else (datetime.now() - started_at.replace(tzinfo=None)).total_seconds()
                    elapsed_time = f"{int(elapsed_seconds // 60)}m {int(elapsed_seconds % 60)}s"

                response = {"status": "processing", "task_id": task_id, "message": "Task is currently being processed", "success": True, "citations": [], "clusters": []}
                progress_payload = None
                try:
                    progress_key = f"progress:{task_id}"
                    raw = redis_conn.get(progress_key)
                    if raw:
                        payload = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
                        progress_payload = json.loads(payload)
                except Exception:
                    progress_payload = None

                if isinstance(vstatus, dict):
                    response["verification_status"] = vstatus
                    total_cites = vstatus.get("total_citations", 0)
                    processed_cites = vstatus.get("citations_processed", 0)
                    if total_cites and processed_cites > total_cites:
                        processed_cites = total_cites
                    current_message = vstatus.get("current_message", "Processing...")
                    pct = vstatus.get("progress_percent", 0)
                    response["progress_percent"] = pct
                    response["progress"] = pct  # Frontend expects "progress" for the progress bar
                    if total_cites > 0:
                        response["current_message"] = current_message if re.search(r"\(\d+/\d+\s+citations\)", current_message) else f"{current_message} ({processed_cites}/{total_cites} citations)"
                        response["message"] = f"Processing {total_cites} citations... ({processed_cites} processed)"
                        # If verification has not advanced yet, surface likely external API wait.
                        if (
                            elapsed_time
                            and processed_cites == 0
                            and re.search(r"verifying citations", response["current_message"], re.IGNORECASE)
                        ):
                            response["message"] = f"Waiting on external citation source... ({elapsed_time} elapsed)"
                        # If progress is partial and elapsed > ~90s, worker may be stuck (e.g. old worker without per-batch timeout). Hint to user.
                        if (
                            elapsed_time
                            and processed_cites > 0
                            and processed_cites < total_cites
                            and elapsed_seconds > 95
                        ):
                            response["message"] = f"Processing {total_cites} citations... ({processed_cites} processed) — next batch taking longer than expected; job will continue or time out"
                    elif elapsed_time:
                        response["current_message"] = f"Extracting citations... (processing for {elapsed_time})"
                        response["message"] = f"Processing document... (started {elapsed_time} ago)"
                    else:
                        response["current_message"] = current_message
                elif elapsed_time:
                    response["current_message"] = f"Processing document... (started {elapsed_time} ago)"
                    response["message"] = f"Task is processing... (elapsed: {elapsed_time})"
                    response["progress"] = 0
                    response["progress_percent"] = 0
                else:
                    response["progress"] = 0
                    response["progress_percent"] = 0

                if isinstance(progress_payload, dict):
                    payload_progress = progress_payload.get("progress")
                    payload_message = progress_payload.get("message")
                    payload_current = progress_payload.get("current_message") or progress_payload.get("current_step")
                    payload_total = progress_payload.get("total_citations")
                    payload_processed = progress_payload.get("citations_processed")

                    if payload_total is not None and payload_processed is not None:
                        try:
                            payload_total_int = int(payload_total)
                            payload_processed_int = int(payload_processed)
                            payload_processed = min(payload_processed_int, payload_total_int) if payload_total_int > 0 else payload_processed_int
                        except Exception:
                            pass

                    if payload_progress is not None:
                        try:
                            response["progress"] = int(payload_progress)
                            response["progress_percent"] = int(payload_progress)
                        except Exception:
                            pass

                    if payload_message:
                        response["message"] = payload_message
                    if payload_current:
                        response["current_message"] = payload_current

                    if payload_total is not None:
                        response["total_citations"] = payload_total
                    if payload_processed is not None:
                        response["citations_processed"] = payload_processed

                    if payload_total and payload_processed is not None:
                        if isinstance(response.get("message"), str) and re.search(r"\(\d+/\d+\s+citations\)", response["message"]):
                            response["message"] = re.sub(
                                r"\(\d+/\d+\s+citations\)",
                                f"({payload_processed}/{payload_total} citations)",
                                response["message"],
                            )
                        if isinstance(response.get("current_message"), str) and re.search(r"\(\d+/\d+\s+citations\)", response["current_message"]):
                            response["current_message"] = re.sub(
                                r"\(\d+/\d+\s+citations\)",
                                f"({payload_processed}/{payload_total} citations)",
                                response["current_message"],
                            )

                    if (
                        payload_total
                        and payload_processed is not None
                        and isinstance(response.get("message"), str)
                        and "100 citations" in response["message"]
                    ):
                        response["message"] = f"Processing {payload_total} citations... ({payload_processed} processed)"

                return jsonify(response)

            else:
                try:
                    position = queue.get_job_position(task_id)
                except Exception:
                    position = -1
                try:
                    from src.verification_manager import VerificationManager
                    vm = VerificationManager()
                    vstatus = vm.get_verification_status(task_id)
                except Exception:
                    vstatus = None
                response = {"status": "queued", "task_id": task_id, "message": f"Task is queued (position: {position})", "position": position, "success": True, "citations": [], "clusters": []}
                # If job has been at front of queue (position 0) for a long time, workers may not be running
                try:
                    import time
                    created_at = getattr(job, "created_at", None)
                    if created_at and position == 0:
                        if hasattr(created_at, "timestamp"):
                            created_ts = created_at.timestamp()
                        else:
                            created_ts = (created_at - datetime(1970, 1, 1)).total_seconds()
                        wait_seconds = time.time() - created_ts
                        if wait_seconds > 90:
                            hint = "Job has been waiting a long time. Ensure RQ workers are running (e.g. docker compose ps; check worker logs)."
                            response["worker_hint"] = hint
                            response["queued_seconds"] = int(wait_seconds)
                            response["message"] = f"Task is queued (position: {position}). {hint}"
                except Exception:
                    pass
                if isinstance(vstatus, dict):
                    response["verification_status"] = vstatus
                    if "progress_percent" in vstatus:
                        pct = vstatus.get("progress_percent", 0)
                        response["progress_percent"] = pct
                        response["progress"] = pct
                    if "current_message" in vstatus:
                        response["current_message"] = vstatus.get("current_message")
                return jsonify(response)

        except Exception as e:
            logger.error(f"Error checking task status for {task_id}: {e}", exc_info=True)
            return (
                jsonify(
                    {"error": "Failed to check task status", "details": str(e), "task_id": task_id, "citations": [], "clusters": []}
                ),
                500,
            )

"""
Task status (RQ job polling) route for the Vue API.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Callable, Dict, Tuple

from flask import jsonify

from src.config import WEBSEARCH_TIMEOUT, REDIS_URL
from src.utils.response_enrichment import compute_cluster_sections, extract_display_base_citation

logger = logging.getLogger(__name__)


def _repair_cluster_citation_sync(citations_list, clusters_list):
    """Best-effort reconciliation between top-level citations and nested cluster citations."""
    if not isinstance(citations_list, list) or not isinstance(clusters_list, list):
        return

    try:
        from src.utils.response_enrichment import per_citation_cluster_year, _four_digit_year_from_val
    except Exception:
        per_citation_cluster_year = None  # type: ignore[assignment]
        _four_digit_year_from_val = None  # type: ignore[assignment]

    def _base_key(val):
        raw = str(val or "").strip()
        if not raw:
            return ""
        base = extract_display_base_citation(raw) or raw
        return re.sub(r"\s+", " ", str(base).strip().lower())

    def _pick_best(rows):
        best: Dict[str, Any] | None = None
        best_score = -1
        for row in rows:
            if not isinstance(row, dict):
                continue
            md: Dict[str, Any] = {}
            md_raw = row.get("metadata")
            if isinstance(md_raw, dict):
                md = md_raw
            md_y = str(md.get("year") or "").strip()
            md_src = str(md.get("extracted_date_source") or "")
            has_local_year = md_y.isdigit() and 1700 <= int(md_y) <= 2030 and md_src.startswith("citation_")
            score = (
                (8 if bool(row.get("verified") or row.get("is_verified")) else 0)
                + (4 if has_local_year else 0)
                + (2 if bool(row.get("canonical_url")) else 0)
                + (1 if bool(str(row.get("extracted_case_name") or "").strip()) else 0)
            )
            if score > best_score:
                best = row
                best_score = score
        return best

    def _citation_local_year(c):
        if not isinstance(c, dict):
            return ""
        md: Dict[str, Any] = {}
        md_raw = c.get("metadata")
        if isinstance(md_raw, dict):
            md = md_raw
        md_y = str(md.get("year") or "").strip()
        md_src = str(md.get("extracted_date_source") or "")
        if md_y.isdigit() and 1700 <= int(md_y) <= 2030 and md_src.startswith("citation_"):
            return md_y
        for k in ("extracted_date", "extracted_year", "canonical_date", "date"):
            v = str(c.get(k) or "").strip()
            m = re.search(r"(19|20)\d{2}", v)
            if m:
                return m.group(0)
        ct = str(c.get("citation") or c.get("text") or "")
        m = re.search(r"\(([^)]*?)\)\s*$", ct)
        if m:
            y = re.search(r"(19|20)\d{2}", m.group(1))
            if y:
                return y.group(0)
        return ""

    by_start_base = {}
    by_base = {}
    for c in citations_list:
        if not isinstance(c, dict):
            continue
        b = _base_key(c.get("citation") or c.get("text"))
        if not b:
            continue
        si = c.get("start_index") if isinstance(c.get("start_index"), int) else None
        if si is not None:
            by_start_base[(si, b)] = c
        by_base.setdefault(b, []).append(c)

    for cl in clusters_list:
        if not isinstance(cl, dict):
            continue
        cl_cites = cl.get("citations")
        if not isinstance(cl_cites, list):
            continue

        for cc in cl_cites:
            if not isinstance(cc, dict):
                continue
            b = _base_key(cc.get("citation") or cc.get("text"))
            if not b:
                continue
            si = cc.get("start_index") if isinstance(cc.get("start_index"), int) else None
            match = by_start_base.get((si, b)) if si is not None else None
            if not isinstance(match, dict):
                match = _pick_best(by_base.get(b, []))
            if not isinstance(match, dict):
                continue

            for fld in (
                "verified",
                "is_verified",
                "verification_status",
                "verification_error",
                "possible_match",
                "true_by_parallel",
                "canonical_name",
                "canonical_date",
                "canonical_url",
                "source",
                "metadata",
                "extracted_case_name",
                "extracted_date",
                "display_base_citation",
            ):
                if fld in match:
                    cc[fld] = match.get(fld)

        if per_citation_cluster_year and _four_digit_year_from_val:
            for cc in cl_cites:
                if isinstance(cc, dict):
                    cc["cluster_year"] = per_citation_cluster_year(cc, cl)
            year_counts = {}
            for cc in cl_cites:
                if isinstance(cc, dict):
                    y = _four_digit_year_from_val(cc.get("cluster_year"))
                    if y:
                        year_counts[y] = year_counts.get(y, 0) + 1
            if year_counts:
                cy = sorted(year_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
                cl["cluster_year"] = cy
                cl["date"] = cy
        else:
            year_counts = {}
            for cc in cl_cites:
                y = _citation_local_year(cc)
                if y:
                    year_counts[y] = year_counts.get(y, 0) + 1
            if year_counts:
                cy = sorted(year_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
                cl["cluster_year"] = cy
                cl["date"] = cy
                for cc in cl_cites:
                    if isinstance(cc, dict):
                        cc["cluster_year"] = cy

        has_verified = any(
            isinstance(cc, dict) and bool(cc.get("verified") or cc.get("is_verified"))
            for cc in cl_cites
        )
        if has_verified:
            cl["verified"] = True
            cur_status = str(cl.get("verification_status") or "").strip().lower()
            if not cur_status or cur_status in {"unverified", "not_found"}:
                cl["verification_status"] = "verified"


def _strip_non_case_from_response_payload(citations_list, clusters_list):
    """Remove secondary non-case references (e.g. law reviews) from top-level and clusters."""
    _non_case_check: Callable[[str], bool]
    try:
        from src.utils.verification_display_utils import is_non_case_legal_reference
        _non_case_check = is_non_case_legal_reference
    except Exception:
        def is_non_case_legal_reference(_s: str) -> bool:
            return False
        _non_case_check = is_non_case_legal_reference

    def _is_non_case_row(row):
        if not isinstance(row, dict):
            return False
        if str(row.get("citation_type") or "") == "non_case_reference":
            return True
        txt = str(row.get("citation") or row.get("text") or "")
        return bool(_non_case_check(txt))

    filtered_citations = [c for c in (citations_list or []) if isinstance(c, dict) and not _is_non_case_row(c)]
    filtered_clusters = []
    for cl in (clusters_list or []):
        if not isinstance(cl, dict):
            continue
        cits = cl.get("citations")
        if isinstance(cits, list):
            cl["citations"] = [c for c in cits if isinstance(c, dict) and not _is_non_case_row(c)]
            cl["cluster_size"] = len(cl["citations"])
            cl["size"] = len(cl["citations"])
        objs = cl.get("citation_objects")
        if isinstance(objs, list):
            cl["citation_objects"] = [c for c in objs if isinstance(c, dict) and not _is_non_case_row(c)]
        if (cl.get("citations") or cl.get("citation_objects")):
            filtered_clusters.append(cl)
    return filtered_citations, filtered_clusters


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
                                logger.debug("Suppressed exception", exc_info=True)

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
                            logger.debug("Suppressed exception", exc_info=True)

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
                    _repair_cluster_citation_sync(citations, clusters)
                    # Re-apply post-verify split rules at response time so worker-path
                    # merge/relabel drift cannot leak mixed canonical clusters to UI.
                    try:
                        from src.utils.cluster_postprocess_pipeline import apply_post_verify_cluster_splits

                        clusters = apply_post_verify_cluster_splits(
                            clusters or [],
                            run_id=f"{task_id}:task_status",
                        )
                        _repair_cluster_citation_sync(citations, clusters)
                    except Exception:
                        logger.debug("Suppressed exception", exc_info=True)
                    # Re-run display finalization so stale cluster-level display fields
                    # (submitted_display_date/name, display_canonical_url) cannot force
                    # verified clusters into Google-search/unverified UI lanes.
                    try:
                        from src.utils.cluster_display_utils import finalize_cluster_for_response

                        for cl in (clusters or []):
                            if not isinstance(cl, dict):
                                continue
                            finalize_cluster_for_response(
                                cl,
                                clean_names=False,
                                clear_unverified_canonical=True,
                                clear_unverified_citations=True,
                            )
                    except Exception:
                        logger.debug("Suppressed exception", exc_info=True)
                    # Final sync for completed results: align citation cluster fields and prefer citation-derived years.
                    try:
                        cl_by_id = {
                            cl.get("cluster_id"): cl
                            for cl in (clusters or [])
                            if isinstance(cl, dict) and cl.get("cluster_id")
                        }
                        for c in (citations or []):
                            if not isinstance(c, dict):
                                continue
                            cid = c.get("cluster_id")
                            cl = cl_by_id.get(cid) if cid else None
                            if cl and cl.get("cluster_case_name"):
                                c["cluster_case_name"] = cl.get("cluster_case_name")
                            md = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
                            y = str(md.get("year") or "").strip()
                            src = str(md.get("extracted_date_source") or "")
                            if y.isdigit() and 1700 <= int(y) <= 2030 and src.startswith("citation_"):
                                c["extracted_date"] = y
                    except Exception:
                        logger.debug("Suppressed exception", exc_info=True)
                    citations, clusters = _strip_non_case_from_response_payload(citations, clusters)
                    stats = actual_result.get("statistics", {}) if isinstance(actual_result.get("statistics", {}), dict) else {}
                    stats["total_citations"] = len(citations or [])
                    stats["total_clusters"] = len(clusters or [])
                    stats["verified_citations"] = sum(
                        1 for c in (citations or []) if isinstance(c, dict) and bool(c.get("verified"))
                    )
                    return jsonify(
                        {
                            "status": "completed",
                            "task_id": task_id,
                            "is_finished": True,
                            "citations": citations,
                            "clusters": clusters,
                            "cluster_sections": compute_cluster_sections(clusters),
                            "statistics": stats,
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
                    _repair_cluster_citation_sync(citations, clusters)
                    try:
                        from src.utils.cluster_postprocess_pipeline import apply_post_verify_cluster_splits

                        clusters = apply_post_verify_cluster_splits(
                            clusters or [],
                            run_id=f"{task_id}:task_status_started",
                        )
                        _repair_cluster_citation_sync(citations, clusters)
                    except Exception:
                        logger.debug("Suppressed exception", exc_info=True)
                    try:
                        from src.utils.cluster_display_utils import finalize_cluster_for_response

                        for cl in (clusters or []):
                            if not isinstance(cl, dict):
                                continue
                            finalize_cluster_for_response(
                                cl,
                                clean_names=False,
                                clear_unverified_canonical=True,
                                clear_unverified_citations=True,
                            )
                    except Exception:
                        logger.debug("Suppressed exception", exc_info=True)
                    try:
                        cl_by_id = {
                            cl.get("cluster_id"): cl
                            for cl in (clusters or [])
                            if isinstance(cl, dict) and cl.get("cluster_id")
                        }
                        for c in (citations or []):
                            if not isinstance(c, dict):
                                continue
                            cid = c.get("cluster_id")
                            cl = cl_by_id.get(cid) if cid else None
                            if cl and cl.get("cluster_case_name"):
                                c["cluster_case_name"] = cl.get("cluster_case_name")
                            md = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
                            y = str(md.get("year") or "").strip()
                            src = str(md.get("extracted_date_source") or "")
                            if y.isdigit() and 1700 <= int(y) <= 2030 and src.startswith("citation_"):
                                c["extracted_date"] = y
                    except Exception:
                        logger.debug("Suppressed exception", exc_info=True)
                    citations, clusters = _strip_non_case_from_response_payload(citations, clusters)
                    stats = actual_result.get("statistics", {}) if isinstance(actual_result.get("statistics", {}), dict) else {}
                    stats["total_citations"] = len(citations or [])
                    stats["total_clusters"] = len(clusters or [])
                    stats["verified_citations"] = sum(
                        1 for c in (citations or []) if isinstance(c, dict) and bool(c.get("verified"))
                    )
                    return jsonify(
                        {
                            "status": "completed",
                            "task_id": task_id,
                            "is_finished": True,
                            "citations": citations,
                            "clusters": clusters,
                            "cluster_sections": compute_cluster_sections(clusters),
                            "statistics": stats,
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
                            logger.debug("Suppressed exception", exc_info=True)

                    if payload_progress is not None:
                        try:
                            response["progress"] = int(payload_progress)
                            response["progress_percent"] = int(payload_progress)
                        except Exception:
                            logger.debug("Suppressed exception", exc_info=True)

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

                # Final safety sync (always for completed jobs): ensure per-citation cluster fields
                # match the final clusters, and ensure citation-derived year metadata wins for extracted_date.
                try:
                    clusters_out = response.get("clusters") or []
                    from src.utils.same_case import has_case_name, names_are_same_case
                    from collections import Counter
                    cl_by_id = {
                        cl.get("cluster_id"): cl
                        for cl in clusters_out
                        if isinstance(cl, dict) and cl.get("cluster_id")
                    }

                    # Repair cluster_case_name from the authoritative flat citations list.
                    # (Cluster citations often omit extracted_case_name; response["citations"] has it.)
                    # Index citations by a normalized "core" key so "347 U.S. 521" and
                    # "347 U.S. 521 (scotus 1954)" match the same bucket.
                    from src.utils.response_enrichment import extract_display_base_citation as _extract_display_base_citation
                    from src.utils.verification_display_utils import citation_core_key
                    cit_by_core = {}
                    for c in response.get("citations") or []:
                        if not isinstance(c, dict):
                            continue
                        raw = (c.get("citation") or "").strip()
                        base = (c.get("display_base_citation") or _extract_display_base_citation(raw) or raw).strip()
                        core = citation_core_key(base) or citation_core_key(raw) or ""
                        if core:
                            cit_by_core.setdefault(core, []).append(c)

                    for cl in clusters_out:
                        if not isinstance(cl, dict):
                            continue
                        names = []
                        for item in (cl.get("cluster_members") or []):
                            ct = ""
                            if isinstance(item, dict):
                                ct = (item.get("citation") or "").strip()
                            else:
                                ct = str(item or "").strip()
                            if not ct:
                                continue
                            # Prefer exact citation row match when available.
                            exact = next(
                                (
                                    rr for rr in (response.get("citations") or [])
                                    if isinstance(rr, dict) and (rr.get("citation") or "").strip() == ct
                                ),
                                None,
                            )
                            if isinstance(exact, dict):
                                nm = (exact.get("extracted_case_name") or "").strip()
                                if nm and nm != "N/A" and has_case_name(nm):
                                    names.append(nm)
                                    continue
                            base = _extract_display_base_citation(ct) or ct
                            core = citation_core_key(base) or citation_core_key(ct) or ""
                            rows = cit_by_core.get(core) if core else None
                            if not rows:
                                continue
                            for row in rows:
                                nm = (row.get("extracted_case_name") or "").strip()
                                if nm and nm != "N/A" and has_case_name(nm):
                                    names.append(nm)
                        if not names:
                            continue
                        best, _cnt = Counter(names).most_common(1)[0]
                        cur = (cl.get("cluster_case_name") or "").strip()
                        if not cur or cur == "N/A" or not has_case_name(cur) or not names_are_same_case(best, cur):
                            cl["cluster_case_name"] = best

                    # Index clusters by case name for safe reassignment.
                    cl_name_index = []
                    for cl in clusters_out:
                        if not isinstance(cl, dict):
                            continue
                        nm = (cl.get("cluster_case_name") or cl.get("extracted_case_name") or cl.get("case_name") or "").strip()
                        if nm and nm != "N/A" and has_case_name(nm):
                            cl_name_index.append((nm, cl.get("cluster_id")))
                    for c in response.get("citations") or []:
                        if not isinstance(c, dict):
                            continue
                        cid = c.get("cluster_id")
                        if cid and cid in cl_by_id:
                            cl = cl_by_id[cid]
                            if cl.get("cluster_case_name"):
                                c["cluster_case_name"] = cl.get("cluster_case_name")
                            if cl.get("cluster_year") is not None:
                                c["cluster_year"] = cl.get("cluster_year")
                            if cl.get("cluster_size") is not None:
                                c["cluster_size"] = cl.get("cluster_size")

                        md = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
                        y = str(md.get("year") or "").strip()
                        src = str(md.get("extracted_date_source") or "")
                        if y.isdigit() and 1700 <= int(y) <= 2030 and src.startswith("citation_"):
                            c["extracted_date"] = y

                    # If a citation has a strong extracted_case_name, ensure it is placed under the matching cluster.
                    # This fixes "subsequent history" cites (e.g., "aff'd ..., 347 U.S. 521 (1954)") being attached
                    # to an unrelated nearby case card.
                    for c in response.get("citations") or []:
                        if not isinstance(c, dict):
                            continue
                        ecn = (c.get("extracted_case_name") or "").strip()
                        if not ecn or ecn == "N/A" or not has_case_name(ecn):
                            continue
                        current = (c.get("cluster_case_name") or "").strip()
                        if current and current != "N/A" and names_are_same_case(ecn, current):
                            continue
                        # At minimum, ensure the citation row's cluster_case_name matches its extracted_case_name.
                        # (Even if the upstream cluster_id is imperfect, this prevents obviously wrong display names.)
                        c["cluster_case_name"] = ecn
                        target_id = None
                        for nm, clid in cl_name_index:
                            if clid and names_are_same_case(ecn, nm):
                                target_id = clid
                                break
                        if not target_id:
                            continue
                        old_id = c.get("cluster_id")
                        if old_id == target_id:
                            continue
                        # Move citation between cluster citation lists (best-effort).
                        c["cluster_id"] = target_id
                        tgt = cl_by_id.get(target_id)
                        if isinstance(tgt, dict):
                            if tgt.get("cluster_case_name"):
                                c["cluster_case_name"] = tgt.get("cluster_case_name")
                            if tgt.get("cluster_year") is not None:
                                c["cluster_year"] = tgt.get("cluster_year")
                            if tgt.get("cluster_size") is not None:
                                c["cluster_size"] = tgt.get("cluster_size")
                            tgt.setdefault("citations", [])
                            if isinstance(tgt.get("citations"), list):
                                tgt["citations"].append(c)
                        if old_id and old_id in cl_by_id:
                            old = cl_by_id.get(old_id)
                            if isinstance(old, dict) and isinstance(old.get("citations"), list):
                                cit_txt = (c.get("citation") or "").strip()
                                if cit_txt:
                                    old["citations"] = [
                                        cc for cc in old.get("citations")
                                        if not (isinstance(cc, dict) and (cc.get("citation") or "").strip() == cit_txt)
                                    ]

                    # Recompute cluster_size after any moves.
                    for cl in clusters_out:
                        if isinstance(cl, dict) and isinstance(cl.get("citations"), list):
                            cl["cluster_size"] = len(cl.get("citations") or [])

                    # If we still have strong named citations with no corresponding cluster name, create a safety cluster.
                    # This is a last-resort repair for cases where clustering attached named citations to unrelated cards.
                    existing_names = []
                    for cl in clusters_out:
                        if not isinstance(cl, dict):
                            continue
                        nm = (cl.get("cluster_case_name") or "").strip()
                        if nm and nm != "N/A" and has_case_name(nm):
                            existing_names.append(nm)

                    def _norm_name(s: str) -> str:
                        return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", str(s or "").lower())).strip()

                    def _has_cluster_for(name: str) -> bool:
                        nn = _norm_name(name)
                        return any(_norm_name(nm) == nn for nm in existing_names)

                    by_ecn = {}
                    for c in response.get("citations") or []:
                        if not isinstance(c, dict):
                            continue
                        ecn = (c.get("extracted_case_name") or "").strip()
                        if ecn and ecn != "N/A" and has_case_name(ecn):
                            by_ecn.setdefault(ecn, []).append(c)

                    next_idx = 1
                    for ecn, rows in by_ecn.items():
                        # Only build a safety cluster when clustering clearly attached these named citations
                        # to a different case card.
                        mismatch = False
                        for r in rows:
                            cur = (r.get("cluster_case_name") or "").strip()
                            if not cur or cur == "N/A" or not has_case_name(cur):
                                mismatch = True
                                break
                            if not names_are_same_case(ecn, cur):
                                mismatch = True
                                break
                        if not mismatch:
                            continue
                        # Create a new cluster and move these citations into it.
                        new_id = f"cluster_safety_ecn_{next_idx}"
                        next_idx += 1
                        yrs = []
                        for r in rows:
                            try:
                                yv = str(r.get("extracted_date") or "").strip()
                                if yv.isdigit() and 1700 <= int(yv) <= 2030:
                                    yrs.append(int(yv))
                            except Exception:
                                logger.debug("Suppressed exception", exc_info=True)
                        cluster_year = str(min(yrs)) if yrs else None
                        new_cluster = {
                            "cluster_id": new_id,
                            "cluster_case_name": ecn,
                            "extracted_case_name": ecn,
                            "case_name": ecn,
                            "cluster_year": cluster_year,
                            "cluster_size": len(rows),
                            "size": len(rows),
                            "citations": [],
                            "cluster_members": [],
                        }
                        # Remove from old clusters and attach to new.
                        for r in rows:
                            old_id = r.get("cluster_id")
                            r["cluster_id"] = new_id
                            r["cluster_case_name"] = ecn
                            if old_id and old_id in cl_by_id:
                                old = cl_by_id.get(old_id)
                                if isinstance(old, dict) and isinstance(old.get("citations"), list):
                                    cit_txt = (r.get("citation") or "").strip()
                                    if cit_txt:
                                        old["citations"] = [
                                            cc for cc in old.get("citations")
                                            if not (isinstance(cc, dict) and (cc.get("citation") or "").strip() == cit_txt)
                                        ]
                            new_cluster["citations"].append(r)
                            if r.get("citation"):
                                new_cluster["cluster_members"].append(r.get("citation"))
                        clusters_out.append(new_cluster)
                        cl_by_id[new_id] = new_cluster
                except Exception:
                    logger.debug("Suppressed exception", exc_info=True)

                return jsonify(response)

            else:
                try:
                    position = queue.get_job_position(task_id)
                except Exception:
                    position = -1
                # Total jobs ahead (includes this one if position >= 0)
                try:
                    queue_total = queue.count
                except Exception:
                    queue_total = None
                # Rough ETA: ~120 s per job; position 0 means next up (~30 s)
                try:
                    _pos = max(0, int(position)) if position is not None and position != -1 else 0
                    estimated_wait_seconds = max(30, _pos * 120)
                    _mins = estimated_wait_seconds // 60
                    _secs = estimated_wait_seconds % 60
                    if _mins > 0:
                        estimated_wait_human = f"~{_mins} min {_secs}s" if _secs else f"~{_mins} min"
                    else:
                        estimated_wait_human = f"~{estimated_wait_seconds}s"
                except Exception:
                    estimated_wait_seconds = None
                    estimated_wait_human = None
                try:
                    from src.verification_manager import VerificationManager
                    vm = VerificationManager()
                    vstatus = vm.get_verification_status(task_id)
                except Exception:
                    vstatus = None
                response = {
                    "status": "queued",
                    "task_id": task_id,
                    "message": f"Task is queued (position: {position})",
                    "position": position,
                    "queue_total": queue_total,
                    "estimated_wait_seconds": estimated_wait_seconds,
                    "estimated_wait_human": estimated_wait_human,
                    "success": True,
                    "citations": [],
                    "clusters": [],
                }
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
                    logger.debug("Suppressed exception", exc_info=True)
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

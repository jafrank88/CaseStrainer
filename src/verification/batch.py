"""
Batch Verification Module
===========================

Batch verification for multiple citations using CourtListener's
citation-lookup API with true text-based batch requests.

Uses COURTLISTENER_API_KEY from config (env) for citation-lookup API.

CourtListener API limits:
- 250 citations matched per single request
- 64,000 characters max per request (~50 pages)
- 60 valid citations per minute throttle
- Sends back 429 with wait_until when throttled
"""

import re
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import List, Dict, Any, Optional, Callable, Sequence, cast
import time

from .sources import CourtListenerVerifier
from .courtlistener_throttle import throttle_courtlistener

logger = logging.getLogger(__name__)

# Regex for volume-reporter-page (e.g. 965 F.3d 596, 578 U.S. 330)
_VOL_REP_PAGE = re.compile(
    r"(\d+)\s+([A-Za-z.]+\s*(?:\d[a-z]{0,2})?)\s+(\d+)"
)


def _vol_rep_page_from_string(s: str) -> Optional[str]:
    """First volume-reporter-page in string (e.g. '965 F.3d 596')."""
    if not s:
        return None
    m = _VOL_REP_PAGE.search(s)
    return f"{m.group(1)} {m.group(2).strip()} {m.group(3)}" if m else None


def _primary_vol_rep_page(citation: str) -> Optional[str]:
    """
    Extract the primary (main) volume-reporter-page from a citation string.
    When the citation contains "(quoting ...)" or "(citing ...)", use only the
    text before that so we match the main case (e.g. 965 F.3d 596) not the
    quoted one (799 F.3d 701). This fixes wrong binding to Levitt when
    verifying Soo Line R.R. Co. v. Consol. Rail Corp., 965 F.3d 596 (quoting ... 799 F.3d 701).
    """
    if not citation or not citation.strip():
        return None
    text = citation.strip()
    # Truncate at parentheticals that introduce a quoted/cited source
    for pattern in [r"\s*\(quoting\s+", r"\s*\(citing\s+", r"\s*\(quoting\s*$", r"\s*\(citing\s*$"]:
        idx = re.search(pattern, text, re.IGNORECASE)
        if idx:
            text = text[: idx.start()].strip()
    return _vol_rep_page_from_string(text)


def _courtlistener_api_key(api_key: Optional[str]) -> str:
    """Use provided key or config (env) so citation-lookup always uses env-backed key."""
    if api_key and api_key.strip():
        return api_key.strip()
    try:
        from src.config import COURTLISTENER_API_KEY
        return (COURTLISTENER_API_KEY or "").strip()
    except Exception:
        return ""

# CourtListener batch limits (use API max to minimize API calls under 5-min rate limit)
MAX_CITATIONS_PER_REQUEST = 250
MAX_CHARS_PER_REQUEST = 64000  # API max 64K chars per request
# Upstream (UnifiedCitationProcessorV2._sanitize_citation_for_verification_query) already caps at 220 chars.
# This is a safety net if any caller passes long strings so we still get reasonable batch sizes.
MAX_CHARS_PER_CITATION_IN_BATCH = 500
# Keep request timeout tighter so we surface progress/fallback sooner on slow external calls.
MAX_BATCH_REQUEST_TIMEOUT_SECONDS = 35
# Hard cap for asyncio.wait_for around the blocking HTTP call (prevents indefinite hang).
MAX_BATCH_ASYNCIO_TIMEOUT_SECONDS = 45
# Per-batch wall-clock timeout (throttle + HTTP). Prevents "stuck at 10 processed" when batch 2+ hangs.
# Must be > throttle max wait (~45s) + HTTP timeout (35s) to avoid false timeouts when rate-limited.
MAX_SECONDS_PER_BATCH = 90


class BatchVerifier:
    """Batch verification using CourtListener's text-based citation-lookup API. Key from config (env)."""
    
    def __init__(self, api_key: Optional[str] = None, session=None):
        self.api_key = _courtlistener_api_key(api_key)
        # Safety net: create session if none provided
        if session is None:
            from .utils import get_retrying_session
            session = get_retrying_session()
        self.session = session
        self.courtlistener = CourtListenerVerifier(self.api_key, session)
        try:
            from src.config import COURTLISTENER_API_URL
            self.base_url = (COURTLISTENER_API_URL or "https://www.courtlistener.com/api/rest/v4").rstrip("/")
        except Exception:
            self.base_url = "https://www.courtlistener.com/api/rest/v4"
    
    def verify_batch_sync(
        self,
        citations: List[str],
        case_names_list: Sequence[Optional[str]],
        dates_list: Sequence[Optional[str]],
        timeout_per_batch: float,
        progress_callback: Optional[Callable[[int, str, str], None]],
    ) -> List[Dict[str, Any]]:
        """Run full batch verification synchronously (throttle + HTTP in this thread).
        Used by verify_batch() via run_in_executor to avoid async/threading hangs."""
        if not citations:
            return []
        logger.info("[BATCH] verify_batch_sync started (running in executor thread)")
        batches = self._build_text_batches(
            citations,
            cast(List[Optional[str]], list(case_names_list)),
            cast(List[Optional[str]], list(dates_list)),
        )
        logger.info(f"[BATCH] Split {len(citations)} citations into {len(batches)} API request(s)")
        all_results: List[Optional[Dict[str, Any]]] = [None] * len(citations)
        for batch_idx, batch_info in enumerate(batches):
            n_this = len(batch_info["indices"])
            processed_so_far = sum(len(b["indices"]) for b in batches[:batch_idx])
            logger.info(
                f"[BATCH] Sending batch {batch_idx + 1}/{len(batches)} ({n_this} citations), "
                f"{processed_so_far} already processed"
            )
            # Do NOT call progress_callback here: it can block on Redis and cause "stuck at 10"
            # (we never reach batch_ex.submit for batch 2). Progress is updated only after each batch.
            # Run throttle+HTTP in a sub-thread with per-batch timeout to avoid indefinite hang.
            # Do NOT use "with ThreadPoolExecutor": shutdown(wait=True) would block forever on a stuck
            # thread after we've already timed out. Use shutdown(wait=False) on timeout so we continue.
            batch_ex = ThreadPoolExecutor(max_workers=1)
            timed_out = False
            try:
                future = batch_ex.submit(
                    self._send_batch_request_sync,
                    batch_info,
                    timeout_per_batch,
                )
                try:
                    batch_results = future.result(timeout=MAX_SECONDS_PER_BATCH)
                except FuturesTimeoutError:
                    logger.warning(
                        f"[BATCH] Batch {batch_idx + 1}/{len(batches)} timed out after {MAX_SECONDS_PER_BATCH}s "
                        "(throttle or HTTP); marking this batch as unverified and continuing."
                    )
                    batch_results = [
                        {
                            "citation": c,
                            "verified": False,
                            "error": "Batch request timed out",
                            "extracted_case_name": cn,
                            "extracted_date": d,
                        }
                        for c, cn, d in zip(
                            batch_info["citation_strings"],
                            batch_info["case_names"],
                            batch_info["dates"],
                        )
                    ]
                    timed_out = True
            finally:
                batch_ex.shutdown(wait=not timed_out)
            logger.info(f"[BATCH] Batch {batch_idx + 1}/{len(batches)} done ({n_this} results)")
            for idx, result in zip(batch_info["indices"], batch_results):
                all_results[idx] = result
            # Update progress after each batch so UI shows 10, 20, 30... (not stuck at 10).
            # Fire-and-forget: run callback in a daemon thread so we never block the batch loop on Redis.
            processed_after = processed_so_far + n_this
            if progress_callback:
                def _run_cb():
                    try:
                        progress_callback(
                            processed_after,
                            "Verifying",
                            f"Verifying citations... ({processed_after}/{len(citations)} citations)",
                        )
                    except Exception as e:
                        logger.warning(f"[BATCH] progress_callback error: {e}")
                import threading
                t = threading.Thread(target=_run_cb, daemon=True)
                t.start()
            import gc
            gc.collect()
            try:
                import ctypes
                ctypes.CDLL("libc.so.6").malloc_trim(0)
            except Exception:
                pass
            if batch_idx < len(batches) - 1:
                try:
                    from src.config import BATCH_DELAY_BETWEEN_REQUESTS_SECONDS
                    delay = max(0.0, float(BATCH_DELAY_BETWEEN_REQUESTS_SECONDS))
                except Exception:
                    delay = 0.5
                if delay > 0:
                    time.sleep(delay)
        for i, result in enumerate(all_results):
            if result is None:
                all_results[i] = {
                    "citation": citations[i],
                    "verified": False,
                    "error": "Not processed",
                    "extracted_case_name": case_names_list[i],
                    "extracted_date": dates_list[i],
                }
        verified_count = sum(1 for r in all_results if r and r.get("verified"))
        logger.info(f"[BATCH] Completed: {verified_count}/{len(all_results)} verified")
        return [r for r in all_results if r is not None]

    async def verify_batch(
        self,
        citations: List[str],
        case_names: Optional[List[str]] = None,
        dates: Optional[List[str]] = None,
        batch_size: int = 250,
        timeout_per_batch: float = 75.0,
        progress_callback: Optional[Callable[[int, str, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Verify multiple citations using CourtListener batch text lookup.
        Runs the entire batch loop in a single executor to avoid async/threading issues.
        """
        if not citations:
            return []
        logger.info(f"[BATCH] Starting batch verification of {len(citations)} citations")
        case_names_list = list(case_names) if case_names else [None] * len(citations)
        dates_list = list(dates) if dates else [None] * len(citations)
        loop = asyncio.get_event_loop()
        total_timeout = 600.0
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.verify_batch_sync(
                        citations,
                        case_names_list,
                        dates_list,
                        timeout_per_batch,
                        progress_callback,
                    ),
                ),
                timeout=total_timeout,
            )
            logger.info(f"[BATCH] verify_batch (async) completed: {len(result)} results")
            return result
        except asyncio.TimeoutError:
            logger.warning(f"[BATCH] Full batch verification timed out after {total_timeout}s")
            return [
                {
                    "citation": c,
                    "verified": False,
                    "error": "Batch verification timed out",
                    "extracted_case_name": cn,
                    "extracted_date": d,
                }
                for c, cn, d in zip(citations, case_names_list, dates_list)
            ]
    
    def _build_text_batches(
        self,
        citations: List[str],
        case_names: List[Optional[str]],
        dates: List[Optional[str]],
    ) -> List[Dict[str, Any]]:
        """
        Build text batches for the citation-lookup API.
        
        Each batch contains:
        - text: joined citation strings separated by ". "
        - indices: original indices of citations in this batch
        - case_names: corresponding case names
        - dates: corresponding dates
        - citation_strings: the raw citation strings
        - spans: (start, end) offsets of each input citation inside text
        """
        batches = []
        current_batch = {"text": "", "indices": [], "case_names": [], "dates": [], "citation_strings": [], "spans": []}
        current_char_count = 0
        
        for i, (citation, case_name, date) in enumerate(zip(citations, case_names, dates)):
            # Use truncated citation for batch text so we don't hit char limit with long strings.
            # Upstream should already pass pruned citations (~220 chars); this is a safety net.
            cite_for_text = (citation or "")[:MAX_CHARS_PER_CITATION_IN_BATCH]
            entry = cite_for_text if not current_batch["indices"] else ". " + cite_for_text
            entry_len = len(entry)

            # Check if adding this citation would exceed limits
            if (len(current_batch["indices"]) >= MAX_CITATIONS_PER_REQUEST or
                    current_char_count + entry_len > MAX_CHARS_PER_REQUEST):
                # Save current batch and start new one
                if current_batch["indices"]:
                    batches.append(current_batch)
                current_batch = {"text": "", "indices": [], "case_names": [], "dates": [], "citation_strings": [], "spans": []}
                current_char_count = 0
                entry = cite_for_text  # No separator for first entry
                entry_len = len(entry)

            start_off = len(current_batch["text"]) + (2 if current_batch["indices"] else 0)
            current_batch["text"] += entry
            current_batch["indices"].append(i)
            current_batch["case_names"].append(case_name)
            current_batch["dates"].append(date)
            current_batch["citation_strings"].append(citation)  # full citation for result mapping
            current_batch["spans"].append((start_off, start_off + len(cite_for_text)))  # spans into sent text
            current_char_count += entry_len
        
        # Don't forget the last batch
        if current_batch["indices"]:
            batches.append(current_batch)

        # Log why batch count is what it is (char limit often forces small batches when citations are long)
        if batches:
            sizes = [len(b["indices"]) for b in batches]
            total_chars = sum(len(b["text"]) for b in batches)
            logger.info(
                f"[BATCH] Built {len(batches)} batch(es): {sizes} citations each, ~{total_chars} total chars "
                f"(limit {MAX_CHARS_PER_REQUEST} chars / {MAX_CITATIONS_PER_REQUEST} cites per request)"
            )

        return batches

    def _split_batch_info(
        self, batch_info: Dict[str, Any], start: int, end: int
    ) -> Dict[str, Any]:
        """Slice batch_info into a sub-batch for indices [start:end]. Rebuilds text and spans."""
        indices = batch_info["indices"][start:end]
        citation_strings = batch_info["citation_strings"][start:end]
        case_names = batch_info["case_names"][start:end]
        dates = batch_info["dates"][start:end]
        # Rebuild text and spans for the sub-batch (same format as _build_text_batches)
        text_parts: List[str] = []
        spans_list: List[tuple] = []
        offset = 0
        for i, cite in enumerate(citation_strings):
            cite_for_text = (cite or "")[:MAX_CHARS_PER_CITATION_IN_BATCH]
            start_off = offset
            text_parts.append(cite_for_text)
            spans_list.append((start_off, start_off + len(cite_for_text)))
            offset += len(cite_for_text)
            if i < len(citation_strings) - 1:
                offset += 2  # ". " separator
        text = ". ".join(text_parts) if text_parts else ""
        return {
            "text": text,
            "indices": indices,
            "case_names": case_names,
            "dates": dates,
            "citation_strings": citation_strings,
            "spans": spans_list,
        }

    def _send_batch_request_sync(
        self,
        batch_info: Dict[str, Any],
        timeout: float
    ) -> List[Dict[str, Any]]:
        """Send a single batch request synchronously (throttle + HTTP). Used when entire
        batch verification runs in one executor to avoid async/threading issues."""
        if not self.api_key:
            return [
                {"citation": c, "verified": False, "error": "No API key",
                 "extracted_case_name": cn, "extracted_date": d}
                for c, cn, d in zip(batch_info["citation_strings"], batch_info["case_names"], batch_info["dates"])
            ]
        url = f"{self.base_url}/citation-lookup/"
        headers = {"Authorization": f"Token {self.api_key}"}
        text = batch_info["text"]
        form_data = {"text": text}
        req_timeout = (10, min(timeout, MAX_BATCH_REQUEST_TIMEOUT_SECONDS))
        cost = max(1, len(batch_info.get("citation_strings") or []))
        try:
            try:
                import psutil, os
                _mem_before = psutil.Process(os.getpid()).memory_info().rss // (1024 * 1024)
                logger.info(f"[BATCH-MEM] Before API call: {_mem_before}MB, text_len={len(text)}")
            except Exception:
                pass
            throttle_courtlistener(cost=cost, context="batch-citation-lookup")
            resp = self.session.post(url, data=form_data, headers=headers, timeout=req_timeout)
            # Automatically adapt on payload too large: split batch in half and retry
            if resp.status_code == 413 and len(batch_info.get("indices") or []) > 1:
                n = len(batch_info["indices"])
                mid = n // 2
                logger.warning(
                    f"[BATCH] API returned 413 (payload too large) for batch of {n} citations; "
                    f"retrying as two batches of {mid} and {n - mid}"
                )
                resp.close()
                first = self._split_batch_info(batch_info, 0, mid)
                second = self._split_batch_info(batch_info, mid, n)
                results_first = self._send_batch_request_sync(first, timeout)
                results_second = self._send_batch_request_sync(second, timeout)
                return results_first + results_second
            return self._process_batch_response(resp, batch_info)
        except Exception as e:
            logger.error(f"[BATCH] Batch request failed: {e}")
            return [
                {"citation": c, "verified": False, "error": str(e),
                 "extracted_case_name": cn, "extracted_date": d}
                for c, cn, d in zip(batch_info["citation_strings"], batch_info["case_names"], batch_info["dates"])
            ]

    def _process_batch_response(
        self,
        resp: Any,
        batch_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Parse HTTP response and map to citation results. Shared by sync and async paths."""
        if resp.status_code == 429:
            try:
                error_data = resp.json()
                wait_until = error_data.get("wait_until", "unknown")
                logger.warning(f"[BATCH] Rate limited. Wait until: {wait_until}")
            except Exception:
                logger.warning("[BATCH] Rate limited (no wait_until in response)")
            return [
                {"citation": c, "verified": False, "error": "Rate limited",
                 "extracted_case_name": cn, "extracted_date": d}
                for c, cn, d in zip(batch_info["citation_strings"], batch_info["case_names"], batch_info["dates"])
            ]
        if resp.status_code != 200:
            logger.error(f"[BATCH] API returned HTTP {resp.status_code}")
            return [
                {"citation": c, "verified": False, "error": f"HTTP {resp.status_code}",
                 "extracted_case_name": cn, "extracted_date": d}
                for c, cn, d in zip(batch_info["citation_strings"], batch_info["case_names"], batch_info["dates"])
            ]
        raw = resp.json()
        api_results = raw if isinstance(raw, list) else []
        resp_size = len(resp.content) if hasattr(resp, 'content') else 0
        resp.close()
        del resp
        num_input = len(batch_info["indices"])
        if not isinstance(raw, list) and raw:
            logger.warning("[BATCH-DIAG] API response was not a list (type=%s). Using empty results.", type(raw).__name__)
        logger.info(f"[BATCH] API returned {len(api_results)} parsed citations for {num_input} input citations (resp_size={resp_size})")
        if api_results:
            sample = [
                (r.get("citation"), r.get("status"), len(r.get("clusters") or []))
                for r in api_results[:5]
            ]
            logger.info(f"[BATCH-DIAG] API result sample (citation, status, num_clusters): {sample}")
        if num_input > 1 and len(api_results) <= 1:
            logger.warning(
                "[BATCH-DIAG] API returned %s result(s) for %s input citations. "
                "If you sent many citations, the API may expect form-encoded body (data=text) not JSON.",
                len(api_results), num_input,
            )
        try:
            import psutil, os
            _mem_after = psutil.Process(os.getpid()).memory_info().rss // (1024 * 1024)
            logger.info(f"[BATCH-MEM] After API call + parse: {_mem_after}MB")
        except Exception:
            pass
        return self._match_results_to_citations(api_results, batch_info)

    def _match_results_to_citations(
        self,
        api_results: List[Dict[str, Any]],
        batch_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Match API results back to input citations.
        
        The API parses its own citations from the text, so we need to match
        them back to our input citations by text position and citation string.
        """
        input_citations = batch_info["citation_strings"]
        case_names = batch_info["case_names"]
        dates = batch_info["dates"]
        text = batch_info["text"]
        
        # Build a lookup from API results keyed by their position in the text
        # Each API result has start_index/end_index into the text we sent
        api_by_position = []
        for api_result in api_results:
            start_idx = api_result.get("start_index", -1)
            end_idx = api_result.get("end_index", -1)
            parsed_citation = api_result.get("citation", "")
            status = api_result.get("status", 0)
            clusters = api_result.get("clusters", [])
            api_by_position.append({
                "start": start_idx,
                "end": end_idx,
                "parsed_citation": parsed_citation,
                "status": status,
                "clusters": clusters,
                "matched": False,
            })
        
        # Normalize citation for comparison (collapse spaces, strip)
        def _norm(s: str) -> str:
            return " ".join((s or "").split())

        # For each input citation, find the best matching API result
        results = []
        matched_count = 0
        spans = batch_info.get("spans") or [(None, None)] * len(input_citations)
        input_norms = [_norm(c) for c in input_citations]

        # Stage 1: deterministic span-based assignment (global greedy by score).
        pair_candidates = []
        for i, input_cit in enumerate(input_citations):
            span_start, span_end = spans[i] if i < len(spans) else (None, None)
            if span_start is None or span_end is None:
                continue
            in_norm = input_norms[i]
            for api_idx, api in enumerate(api_by_position):
                a_start = api.get("start", -1)
                a_end = api.get("end", -1)
                if a_start < 0 or a_end <= a_start:
                    continue
                overlap = max(0, min(span_end, a_end) - max(span_start, a_start))
                start_inside = span_start <= a_start < span_end
                if not overlap and not start_inside:
                    continue

                # Base score from span alignment, then boost text agreement.
                score = overlap + (50 if start_inside else 0)
                parsed = api.get("parsed_citation") or ""
                parsed_norm = _norm(parsed)
                if parsed_norm and parsed_norm == in_norm:
                    score += 200
                elif parsed and (parsed in input_cit or input_cit in parsed):
                    score += 75
                # Prefer API result that matches the primary cite (e.g. 965 F.3d 596), not a quoted one (799 F.3d 701)
                primary_vrp = _primary_vol_rep_page(input_cit)
                parsed_vrp = _vol_rep_page_from_string(parsed)
                if primary_vrp and parsed_vrp and primary_vrp == parsed_vrp:
                    score += 100
                pair_candidates.append((score, i, api_idx))

        pair_candidates.sort(reverse=True)
        assigned_input = set()
        assigned_api = set()
        span_match_by_input: Dict[int, Dict[str, Any]] = {}
        for score, input_idx, api_idx in pair_candidates:
            if input_idx in assigned_input or api_idx in assigned_api:
                continue
            assigned_input.add(input_idx)
            assigned_api.add(api_idx)
            span_match_by_input[input_idx] = api_by_position[api_idx]
        
        for i, (input_cit, case_name, date) in enumerate(zip(input_citations, case_names, dates)):
            best_match = span_match_by_input.get(i)
            if best_match is None:
                # Stage 2 fallback: only consider API results without valid spans.
                # This avoids re-binding already-positioned results to the wrong input.
                best_match = self._find_best_api_match(
                    input_cit,
                    api_by_position,
                    text,
                    allow_positionless_only=True,
                )
            
            if best_match and best_match["clusters"]:
                cluster = self._select_best_cluster(
                    best_match["clusters"], case_name, extracted_date=date
                )
                if cluster:
                    matched_count += 1
                    best_match["matched"] = True
                    canonical_name = cluster.get("case_name") or cluster.get("caseName")
                    date_filed = cluster.get("date_filed") or cluster.get("dateFiled", "")
                    canonical_date = None
                    if date_filed:
                        year_match = re.search(r"(\d{4})", date_filed)
                        if year_match:
                            canonical_date = year_match.group(1)

                    absolute_url = cluster.get("absolute_url", "")
                    canonical_url = f"https://www.courtlistener.com{absolute_url}" if absolute_url else None

                    results.append({
                        "citation": input_cit,
                        "verified": True,
                        "canonical_name": canonical_name,
                        "canonical_date": canonical_date,
                        "canonical_url": canonical_url,
                        "source": "CourtListener",
                        "confidence": 0.95 if best_match["status"] == 200 else 0.7,
                        "extracted_case_name": case_name,
                        "extracted_date": date,
                    })
                else:
                    # Single cluster rejected: document name clearly different (e.g. Arco vs Utils. Transp. Comm'n)
                    results.append({
                        "citation": input_cit,
                        "verified": False,
                        "error": "Name mismatch",
                        "extracted_case_name": case_name,
                        "extracted_date": date,
                    })
            else:
                error = "No results"
                if best_match and best_match["status"] == 429:
                    error = "Too many citations in request"
                # Log first few unmatched for debugging
                if len([r for r in results if not r.get("verified")]) <= 3:
                    logger.info(
                        "[BATCH-DIAG] No match for input #%s %r (best_match=%s, clusters=%s)",
                        i, input_cit, best_match is not None, len(best_match["clusters"]) if best_match else 0,
                    )
                results.append({
                    "citation": input_cit,
                    "verified": False,
                    "error": error,
                    "extracted_case_name": case_name,
                    "extracted_date": date,
                })
        
        logger.info(f"[BATCH-DIAG] Matched {matched_count}/{len(input_citations)} input citations to API results (API returned {len(api_by_position)} results)")
        return results

    def _cluster_name_matches_extracted(self, cluster: Dict[str, Any], extracted_case_name: str) -> bool:
        """
        Return False when the cluster's case name is clearly a different case than the document's.
        E.g. document "Utils. Transp. Comm'n Seattle, Inc. v. Utils. & Transp. Comm'n" should not
        match CourtListener "Arco Products Co. v. Utilities & Transportation Commission" (same cite, wrong case).
        """
        if not extracted_case_name or len(extracted_case_name.strip()) < 4:
            return True
        cn = (cluster.get("case_name") or cluster.get("caseName") or "").strip()
        if not cn:
            return True
        ecn_lower = extracted_case_name.lower().strip()
        cn_lower = cn.lower()
        # First party must have some overlap (e.g. "utils" / "utilities", "arco" vs "utils" = no)
        ecn_parts = re.split(r"\s+v\.?\s+", ecn_lower, maxsplit=1)
        cn_parts = re.split(r"\s+v\.?\s+", cn_lower, maxsplit=1)
        ecn_first = (ecn_parts[0].strip() if ecn_parts else "").split()
        cn_first = (cn_parts[0].strip() if cn_parts else "").split()
        if not ecn_first or not cn_first:
            return True
        # Normalize: drop common suffixes for comparison
        stop = {"inc", "co", "ltd", "llc", "corp", "comm'n", "commission", "commissioner"}
        ecn_tokens = set(w.strip(".,'") for w in ecn_first if w.strip(".,'") and w.strip(".,'") not in stop)
        cn_tokens = set(w.strip(".,'") for w in cn_first if w.strip(".,'") and w.strip(".,'") not in stop)
        if not ecn_tokens or not cn_tokens:
            return True
        # Reject if no token overlap (e.g. "arco","products" vs "utils","transp","seattle")
        if ecn_tokens.isdisjoint(cn_tokens):
            # Allow if one side is abbreviation of the other (e.g. "utils" vs "utilities")
            ecn_str = " ".join(sorted(ecn_tokens))
            cn_str = " ".join(sorted(cn_tokens))
            if not (ecn_str in cn_str or cn_str in ecn_str or any(
                a in b or b in a for a in ecn_tokens for b in cn_tokens
            )):
                return False
        return True

    def _select_best_cluster(
        self,
        clusters: List[Dict[str, Any]],
        extracted_case_name: Optional[str] = None,
        extracted_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Select the best cluster from CourtListener results using extracted case name and year.
        
        When CourtListener returns multiple clusters for a citation (e.g. "In re Mercer"
        returns both 1987 and 2009 opinions), prefer the cluster whose date_filed matches
        the citation's extracted year (e.g. 1987 for "108 Wn.2d 714, 741 P.2d 559 (1987)").
        Also pick by case_name match when names differ (e.g. '1 Cranch 137' -> Marbury v. Madison).
        When there is only one cluster but the document's extracted name clearly refers
        to a different case (e.g. first party mismatch), return {} so the citation is
        not marked verified (avoids wrong URL e.g. Arco for "Utils. Transp. Comm'n Seattle").
        """
        if not clusters:
            return {}
        if len(clusters) == 1:
            single = clusters[0]
            if not extracted_case_name or (extracted_case_name or "").strip() == "N/A":
                return single
            # Reject single cluster when document name clearly refers to a different case
            if not self._cluster_name_matches_extracted(single, extracted_case_name.strip()):
                return {}
            return single

        # Prefer cluster whose date_filed year matches extracted year (e.g. Mercer 1987 vs 2009)
        want_year = None
        if extracted_date:
            ym = re.search(r"(19|20)\d{2}", str(extracted_date))
            if ym:
                want_year = int(ym.group(0))

        ecn_lower = extracted_case_name.lower().strip() if extracted_case_name else ""
        if not ecn_lower or ecn_lower == "n/a":
            if want_year is not None:
                for cluster in clusters:
                    date_filed = cluster.get("date_filed") or cluster.get("dateFiled", "")
                    if date_filed:
                        fm = re.search(r"(19|20)\d{2}", str(date_filed))
                        if fm and int(fm.group(0)) == want_year:
                            return cluster
            return clusters[0]

        # Extract first party from extracted name for matching
        ecn_parts = re.split(r"\s+v\.?\s+", ecn_lower, maxsplit=1)
        ecn_first = ecn_parts[0].strip().split()[-1] if ecn_parts else ""

        best_cluster = clusters[0]
        best_score = -1

        for cluster in clusters:
            cn = (cluster.get("case_name") or cluster.get("caseName") or "").lower().strip()
            if not cn:
                continue
            
            score = 0
            # Year match: prefer cluster whose date_filed matches citation year (Mercer 1987 vs 2009)
            if want_year is not None:
                date_filed = cluster.get("date_filed") or cluster.get("dateFiled", "")
                if date_filed:
                    fm = re.search(r"(19|20)\d{2}", str(date_filed))
                    if fm and int(fm.group(0)) == want_year:
                        score += 15
            # Exact substring match
            if ecn_lower in cn or cn in ecn_lower:
                score += 10
            # First party match
            cn_parts = re.split(r"\s+v\.?\s+", cn, maxsplit=1)
            cn_first = cn_parts[0].strip().split()[-1] if cn_parts else ""
            if ecn_first and cn_first and ecn_first == cn_first:
                score += 5
            # Word overlap
            ecn_words = set(re.findall(r"[a-z]+", ecn_lower)) - {"v", "the", "of", "and", "inc", "llc"}
            cn_words = set(re.findall(r"[a-z]+", cn)) - {"v", "the", "of", "and", "inc", "llc"}
            if ecn_words and cn_words:
                overlap = len(ecn_words & cn_words) / max(len(ecn_words | cn_words), 1)
                score += overlap * 3
            
            if score > best_score:
                best_score = score
                best_cluster = cluster
        
        if best_score > 0 and best_cluster != clusters[0]:
            selected_name = best_cluster.get("case_name") or best_cluster.get("caseName") or "?"
            first_name = clusters[0].get("case_name") or clusters[0].get("caseName") or "?"
            logger.info(
                f"[BATCH-CLUSTER-SELECT] Selected '{selected_name}' over '{first_name}' "
                f"for extracted name '{extracted_case_name}' (score={best_score:.1f})"
            )
        
        return best_cluster

    def _find_best_api_match(
        self,
        input_citation: str,
        api_results: List[Dict[str, Any]],
        text: str,
        allow_positionless_only: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Find the best API result matching an input citation."""
        # Prefer the API result whose vol-rep-page matches the *primary* cite (before "(quoting ...)")
        # so we bind Soo Line (965 F.3d 596) to the Soo Line opinion, not Levitt (799 F.3d 701).
        primary_vrp = _primary_vol_rep_page(input_citation)

        # First try: exact substring match, but prefer match to primary cite
        primary_match = None
        other_matches = []
        for api_result in api_results:
            if api_result["matched"]:
                continue
            if allow_positionless_only and api_result.get("start", -1) >= 0:
                continue
            parsed = api_result["parsed_citation"]
            if not parsed or parsed not in input_citation:
                continue
            parsed_vrp = _vol_rep_page_from_string(parsed)
            if primary_vrp and parsed_vrp and primary_vrp == parsed_vrp:
                primary_match = api_result
                break
            other_matches.append(api_result)
        if primary_match:
            return primary_match
        if other_matches:
            return other_matches[0]

        # Second try: normalized volume/reporter/page match (use primary cite for input)
        input_normalized = primary_vrp or _vol_rep_page_from_string(input_citation)
        if input_normalized:
            for api_result in api_results:
                if api_result["matched"]:
                    continue
                if allow_positionless_only and api_result.get("start", -1) >= 0:
                    continue
                parsed = api_result["parsed_citation"]
                parsed_normalized = _vol_rep_page_from_string(parsed) if parsed else None
                if parsed_normalized and input_normalized == parsed_normalized:
                    return api_result

        return None

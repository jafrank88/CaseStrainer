"""
Batch Verification Module
===========================

Batch verification for multiple citations using CourtListener's
citation-lookup API with true text-based batch requests.

CourtListener API limits:
- 250 citations matched per single request
- 64,000 characters max per request (~50 pages)
- 60 valid citations per minute throttle
- Sends back 429 with wait_until when throttled
"""

import re
import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
import time

from .sources import CourtListenerVerifier

logger = logging.getLogger(__name__)

# CourtListener batch limits
MAX_CITATIONS_PER_REQUEST = 250
MAX_CHARS_PER_REQUEST = 60000  # Leave 4K buffer under 64K limit


class BatchVerifier:
    """Batch verification using CourtListener's text-based citation-lookup API."""
    
    def __init__(self, api_key: Optional[str] = None, session=None):
        self.api_key = api_key
        # Safety net: create session if none provided
        if session is None:
            from .utils import get_retrying_session
            session = get_retrying_session()
        self.session = session
        self.courtlistener = CourtListenerVerifier(api_key, session)
        self.base_url = "https://www.courtlistener.com/api/rest/v4"
    
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
        
        Joins citations into a text block and sends one API request per batch
        (up to 250 citations / 64K chars per request). Much faster than
        individual lookups.
        """
        if not citations:
            return []
        
        logger.info(f"[BATCH] Starting batch verification of {len(citations)} citations")
        
        # Prepare data
        case_names = case_names or [None] * len(citations)
        dates = dates or [None] * len(citations)
        
        # Build text batches respecting both citation count and char limits
        batches = self._build_text_batches(citations, case_names, dates)
        logger.info(f"[BATCH] Split {len(citations)} citations into {len(batches)} API request(s)")
        
        all_results = [None] * len(citations)  # Pre-allocate to preserve order
        
        for batch_idx, batch_info in enumerate(batches):
            if progress_callback:
                processed = sum(len(b["indices"]) for b in batches[:batch_idx])
                progress_callback(
                    processed,
                    "Verifying",
                    f"API batch {batch_idx + 1}/{len(batches)} ({len(batch_info['indices'])} citations)..."
                )
            
            # Send batch request
            batch_results = await self._send_batch_request(batch_info, timeout_per_batch)
            
            # Map results back to original indices
            for idx, result in zip(batch_info["indices"], batch_results):
                all_results[idx] = result
            
            # Free HTTP response objects between batches to reduce peak memory
            import gc
            gc.collect()
            try:
                import ctypes
                ctypes.CDLL("libc.so.6").malloc_trim(0)
            except Exception:
                pass

            # Rate limiting between batches (60 citations/min = wait if needed)
            if batch_idx < len(batches) - 1:
                await asyncio.sleep(2.0)
        
        # Fill any gaps with unverified results
        for i, result in enumerate(all_results):
            if result is None:
                all_results[i] = {
                    "citation": citations[i],
                    "verified": False,
                    "error": "Not processed",
                    "extracted_case_name": case_names[i],
                    "extracted_date": dates[i],
                }
        
        verified_count = sum(1 for r in all_results if r.get("verified"))
        logger.info(f"[BATCH] Completed: {verified_count}/{len(all_results)} verified")
        return all_results
    
    def _build_text_batches(
        self,
        citations: List[str],
        case_names: List[Optional[str]],
        dates: List[Optional[str]]
    ) -> List[Dict[str, Any]]:
        """
        Build text batches for the citation-lookup API.
        
        Each batch contains:
        - text: joined citation strings separated by ". "
        - indices: original indices of citations in this batch
        - case_names: corresponding case names
        - dates: corresponding dates
        - citation_strings: the raw citation strings
        """
        batches = []
        current_batch = {"text": "", "indices": [], "case_names": [], "dates": [], "citation_strings": []}
        current_char_count = 0
        
        for i, (citation, case_name, date) in enumerate(zip(citations, case_names, dates)):
            # Each citation gets a separator ". " for the parser
            entry = citation if not current_batch["indices"] else ". " + citation
            entry_len = len(entry)
            
            # Check if adding this citation would exceed limits
            if (len(current_batch["indices"]) >= MAX_CITATIONS_PER_REQUEST or
                    current_char_count + entry_len > MAX_CHARS_PER_REQUEST):
                # Save current batch and start new one
                if current_batch["indices"]:
                    batches.append(current_batch)
                current_batch = {"text": "", "indices": [], "case_names": [], "dates": [], "citation_strings": []}
                current_char_count = 0
                entry = citation  # No separator for first entry
                entry_len = len(entry)
            
            current_batch["text"] += entry
            current_batch["indices"].append(i)
            current_batch["case_names"].append(case_name)
            current_batch["dates"].append(date)
            current_batch["citation_strings"].append(citation)
            current_char_count += entry_len
        
        # Don't forget the last batch
        if current_batch["indices"]:
            batches.append(current_batch)
        
        return batches
    
    async def _send_batch_request(
        self,
        batch_info: Dict[str, Any],
        timeout: float
    ) -> List[Dict[str, Any]]:
        """Send a single batch text request to CourtListener citation-lookup API."""
        if not self.api_key:
            return [
                {"citation": c, "verified": False, "error": "No API key",
                 "extracted_case_name": cn, "extracted_date": d}
                for c, cn, d in zip(batch_info["citation_strings"], batch_info["case_names"], batch_info["dates"])
            ]
        
        url = f"{self.base_url}/citation-lookup/"
        headers = {"Authorization": f"Token {self.api_key}"}
        text = batch_info["text"]
        
        try:
            # Log memory before API call
            try:
                import psutil, os
                _mem_before = psutil.Process(os.getpid()).memory_info().rss // (1024 * 1024)
                logger.info(f"[BATCH-MEM] Before API call: {_mem_before}MB, text_len={len(text)}")
            except Exception:
                pass

            resp = self.session.post(
                url,
                json={"text": text},
                headers=headers,
                timeout=min(timeout, 60)
            )
            
            if resp.status_code == 429:
                # Rate limited - extract wait time if available
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
            
            api_results = resp.json()
            # Explicitly release HTTP response to free memory
            resp_size = len(resp.content) if hasattr(resp, 'content') else 0
            resp.close()
            del resp
            logger.info(f"[BATCH] API returned {len(api_results)} parsed citations for {len(batch_info['indices'])} input citations (resp_size={resp_size})")

            # Log memory after API call
            try:
                import psutil, os
                _mem_after = psutil.Process(os.getpid()).memory_info().rss // (1024 * 1024)
                logger.info(f"[BATCH-MEM] After API call + parse: {_mem_after}MB")
            except Exception:
                pass

            # Match API results back to input citations
            return self._match_results_to_citations(api_results, batch_info)
            
        except Exception as e:
            logger.error(f"[BATCH] Batch request failed: {e}")
            return [
                {"citation": c, "verified": False, "error": str(e),
                 "extracted_case_name": cn, "extracted_date": d}
                for c, cn, d in zip(batch_info["citation_strings"], batch_info["case_names"], batch_info["dates"])
            ]
    
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
        
        # For each input citation, find the best matching API result
        results = []
        for i, (input_cit, case_name, date) in enumerate(zip(input_citations, case_names, dates)):
            best_match = self._find_best_api_match(input_cit, api_by_position, text)
            
            if best_match and best_match["clusters"]:
                best_match["matched"] = True
                cluster = self._select_best_cluster(best_match["clusters"], case_name)
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
                error = "No results"
                if best_match and best_match["status"] == 429:
                    error = "Too many citations in request"
                results.append({
                    "citation": input_cit,
                    "verified": False,
                    "error": error,
                    "extracted_case_name": case_name,
                    "extracted_date": date,
                })
        
        return results
    
    def _select_best_cluster(
        self,
        clusters: List[Dict[str, Any]],
        extracted_case_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Select the best cluster from CourtListener results using extracted case name.
        
        When CourtListener returns multiple clusters for a citation (e.g., '1 Cranch 137'
        returns both 'Green v. Fry' and 'Marbury v. Madison'), pick the one whose
        case_name best matches the extracted_case_name from the document.
        """
        if not clusters:
            return {}
        if len(clusters) == 1 or not extracted_case_name or extracted_case_name == "N/A":
            return clusters[0]
        
        ecn_lower = extracted_case_name.lower().strip()
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
        text: str
    ) -> Optional[Dict[str, Any]]:
        """Find the best API result matching an input citation."""
        # Strategy: find API results whose parsed citation appears in the input citation
        # or whose text position overlaps with where the input citation is in the text
        
        # First try: exact substring match on citation string
        for api_result in api_results:
            if api_result["matched"]:
                continue
            parsed = api_result["parsed_citation"]
            # Check if the parsed citation is a substring of the input (common case)
            # e.g. parsed "578 U.S. 330" matches input "Spokeo, Inc. v. Robins, 578 U.S. 330 (2016)"
            if parsed and parsed in input_citation:
                return api_result
        
        # Second try: check if input citation appears near the API result's position in text
        input_pos = text.find(input_citation)
        if input_pos >= 0:
            for api_result in api_results:
                if api_result["matched"]:
                    continue
                start = api_result["start"]
                end = api_result["end"]
                # Check if positions overlap or are very close
                if (start >= input_pos and start < input_pos + len(input_citation) + 5) or \
                   (input_pos >= start and input_pos < end + 5):
                    return api_result
        
        # Third try: normalized volume/reporter/page match
        vol_rep_page = re.search(r"(\d+)\s+([A-Za-z.]+\s*(?:\d[a-z]{0,2})?)\s+(\d+)", input_citation)
        if vol_rep_page:
            input_normalized = f"{vol_rep_page.group(1)} {vol_rep_page.group(2).strip()} {vol_rep_page.group(3)}"
            for api_result in api_results:
                if api_result["matched"]:
                    continue
                parsed = api_result["parsed_citation"]
                if parsed:
                    parsed_vrp = re.search(r"(\d+)\s+([A-Za-z.]+\s*(?:\d[a-z]{0,2})?)\s+(\d+)", parsed)
                    if parsed_vrp:
                        parsed_normalized = f"{parsed_vrp.group(1)} {parsed_vrp.group(2).strip()} {parsed_vrp.group(3)}"
                        if input_normalized == parsed_normalized:
                            return api_result
        
        return None

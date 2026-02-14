"""CourtListener Search API fallback for citations that get 0 clusters from citation-lookup."""
import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def cl_search_fallback(session, api_key, citation, extracted_case_name=None, extracted_date=None, timeout=10.0):
    """Search CourtListener by case name when citation-lookup returns 0 clusters."""
    if not api_key or not extracted_case_name or extracted_case_name == "N/A":
        return {"verified": False, "error": "No case name for search"}
    base = "https://www.courtlistener.com/api/rest/v4"
    headers = {"Authorization": f"Token {api_key}"}

    # Strategy 1: Opinion search with case_name + date filter
    params: Dict[str, Any] = {"case_name": extracted_case_name, "type": "o"}
    year = None
    if extracted_date:
        ym = re.search(r"(19|20)\d{2}", str(extracted_date))
        if ym:
            year = int(ym.group(0))
            params["filed_after"] = f"{year-1}-01-01"
            params["filed_before"] = f"{year+1}-12-31"
    try:
        resp = session.get(f"{base}/search/", params=params, headers=headers, timeout=min(timeout, 20))
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            resp.close(); del resp
            if results:
                best = _pick_best(results, extracted_case_name)
                if best:
                    return _build_result(best, citation, "opinion-search")
        else:
            resp.close(); del resp

        # Strategy 1.5: Keyword free-text search with date filter
        # Handles abbreviation mismatches (e.g. "DHS" vs "Dep't of Homeland Sec.")
        # by searching content words from the case name with date bounds
        stop = {"v", "the", "of", "and", "in", "for", "on", "at", "to", "a", "an", "re"}
        kw = [w for w in re.findall(r"[A-Za-z]+", extracted_case_name) if w.lower() not in stop and len(w) > 1]
        if kw:
            kw_q = " ".join(kw)
            params15: Dict[str, Any] = {"q": kw_q, "type": "o"}
            if year:
                params15["filed_after"] = f"{year-1}-01-01"
                params15["filed_before"] = f"{year+1}-12-31"
            try:
                resp15 = session.get(f"{base}/search/", params=params15, headers=headers, timeout=min(timeout, 20))
                if resp15.status_code == 200:
                    results15 = resp15.json().get("results", [])
                    resp15.close(); del resp15
                    if results15:
                        best15 = _pick_best(results15, extracted_case_name)
                        if best15:
                            return _build_result(best15, citation, "keyword-search")
                else:
                    resp15.close(); del resp15
            except Exception:
                pass

        # Strategy 2: Free-text search with case name + citation
        params2: Dict[str, Any] = {"q": f"{extracted_case_name} {citation}", "type": "o"}
        resp2 = session.get(f"{base}/search/", params=params2, headers=headers, timeout=min(timeout, 20))
        if resp2.status_code == 200:
            results2 = resp2.json().get("results", [])
            resp2.close(); del resp2
            if results2:
                best2 = _pick_best(results2, extracted_case_name)
                if best2:
                    return _build_result(best2, citation, "freetext-search")
        else:
            resp2.close(); del resp2

        # Strategy 3: Docket search (finds cases not yet in opinion DB)
        # Use quoted first-party + second-party for targeted search
        parts = re.split(r"\s+v\.?\s+", extracted_case_name, maxsplit=1)
        if len(parts) == 2:
            first_party = parts[0].strip().split()[0]  # First word of first party
            second_party = parts[1].strip().split()[0]  # First word of second party
            docket_q = f'"{first_party}" "{second_party}"'
        else:
            docket_q = extracted_case_name
        params3: Dict[str, Any] = {"q": docket_q, "type": "r"}
        resp3 = session.get(f"{base}/search/", params=params3, headers=headers, timeout=min(timeout, 20))
        if resp3.status_code == 200:
            results3 = resp3.json().get("results", [])
            resp3.close(); del resp3
            if results3:
                best3 = _pick_best_docket(results3, extracted_case_name)
                if best3:
                    cn = best3.get("caseName") or best3.get("case_name") or ""
                    dn = best3.get("docketNumber") or ""
                    court = best3.get("court") or ""
                    au = best3.get("absolute_url") or ""
                    cu = f"https://www.courtlistener.com{au}" if au else None
                    # Use extracted_date as canonical_date since docket may not have it
                    cd = str(year) if year else None
                    logger.info(f"[CL-SEARCH-FALLBACK] Found docket '{cn}' for '{citation}'")
                    return {"verified": True, "canonical_name": cn, "canonical_date": cd, "canonical_url": cu, "source": "CourtListener-Docket", "confidence": 0.75}

        return {"verified": False, "error": "No matching results in any search strategy"}
    except Exception as e:
        logger.warning(f"CL search fallback failed: {e}")
        return {"verified": False, "error": str(e)}


def _build_result(best, citation, method):
    cn = best.get("caseName") or best.get("case_name") or ""
    df = best.get("dateFiled") or best.get("date_filed") or ""
    au = best.get("absolute_url") or ""
    cd = None
    if df:
        m = re.search(r"(\d{4})", df)
        if m:
            cd = m.group(1)
    cu = f"https://www.courtlistener.com{au}" if au else None
    logger.info(f"[CL-SEARCH-FALLBACK] Found '{cn}' for '{citation}' via {method}")
    return {"verified": True, "canonical_name": cn, "canonical_date": cd, "canonical_url": cu, "source": "CourtListener-Search", "confidence": 0.85}


def _prefix_overlap(set_a, set_b):
    """Count words in set_a that match a word in set_b exactly or by prefix (min 3 chars)."""
    hits = 0
    for wa in set_a:
        if wa in set_b:
            hits += 1
            continue
        if len(wa) >= 3:
            for wb in set_b:
                if len(wb) >= 3 and (wa.startswith(wb) or wb.startswith(wa)):
                    hits += 1
                    break
    return hits


def _pick_best(results, ecn):
    ecn_w = set(re.findall(r"[a-z]+", ecn.lower())) - {"v", "the", "of", "and", "inc", "llc", "co"}
    if not ecn_w:
        return results[0] if results else None
    best, best_s = None, 0
    for r in results[:10]:
        cn = (r.get("caseName") or r.get("case_name") or "").lower()
        cn_w = set(re.findall(r"[a-z]+", cn)) - {"v", "the", "of", "and", "inc", "llc", "co"}
        if cn_w:
            s = _prefix_overlap(ecn_w, cn_w) / len(ecn_w)
            if s > best_s:
                best_s = s
                best = r
    return best if best_s >= 0.4 else None


def _pick_best_docket(results, ecn):
    """Pick best docket result matching extracted case name. Requires first party match."""
    ecn_lower = ecn.lower().strip()
    ecn_w = set(re.findall(r"[a-z]+", ecn_lower)) - {"v", "the", "of", "and", "inc", "llc", "co"}
    # Extract first party for stricter matching
    ecn_parts = re.split(r"\s+v\.?\s+", ecn_lower, maxsplit=1)
    ecn_first_words = set(re.findall(r"[a-z]+", ecn_parts[0])) - {"inc", "llc", "co", "corp", "ltd"}
    if not ecn_w:
        return results[0] if results else None
    best, best_s = None, 0
    for r in results[:10]:
        cn = (r.get("caseName") or r.get("case_name") or "").lower()
        cn_parts = re.split(r"\s+v\.?\s+", cn, maxsplit=1)
        cn_first_words = set(re.findall(r"[a-z]+", cn_parts[0])) - {"inc", "llc", "co", "corp", "ltd"}
        # Require at least one first-party word to match
        if ecn_first_words and cn_first_words and not (ecn_first_words & cn_first_words):
            continue
        cn_w = set(re.findall(r"[a-z]+", cn)) - {"v", "the", "of", "and", "inc", "llc", "co"}
        if cn_w:
            s = len(ecn_w & cn_w) / len(ecn_w)
            if s > best_s:
                best_s = s
                best = r
    return best if best_s >= 0.5 else None

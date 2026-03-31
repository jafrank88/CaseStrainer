"""CourtListener Search API fallback for citations that get 0 clusters from citation-lookup. Uses same API key from config (env) as citation-lookup."""
import re
import logging
from typing import Optional, Dict, Any
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .courtlistener_throttle import throttle_courtlistener

try:
    from src.utils.state_reporter_map import infer_court_from_citation
    from src.utils.legal_abbreviations import expand_abbreviations
    _CL_SEARCH_UTILS = True
except Exception:
    _CL_SEARCH_UTILS = False
    def infer_court_from_citation(t): return None
    def expand_abbreviations(s): return s

logger = logging.getLogger(__name__)
_FAST_CL_SESSION: Optional[requests.Session] = None


def _cl_search_api_key_and_base(api_key: Optional[str]):
    """Resolve API key and base URL from config (env) so search API uses same key as citation-lookup."""
    key = (api_key or "").strip()
    base = "https://www.courtlistener.com/api/rest/v4"
    try:
        from src.config import COURTLISTENER_API_KEY, COURTLISTENER_API_URL
        if not key:
            key = (COURTLISTENER_API_KEY or "").strip()
        if COURTLISTENER_API_URL:
            base = (COURTLISTENER_API_URL or base).rstrip("/")
    except Exception:
        pass
    return key, base


def _get_fast_cl_session() -> requests.Session:
    """
    Dedicated fail-fast session for CL /search fallback.
    Avoids inherited retry adapters that can multiply latency per call.
    """
    global _FAST_CL_SESSION
    if _FAST_CL_SESSION is None:
        retry = Retry(
            total=0,
            read=0,
            connect=0,
            status=0,
            redirect=0,
            backoff_factor=0.0,
            allowed_methods=frozenset(["GET"]),
        )
        adapter = HTTPAdapter(max_retries=retry)
        s = requests.Session()
        trust_env_raw = (os.getenv("VERIFICATION_TRUST_ENV", "false") or "").strip().lower()
        s.trust_env = trust_env_raw in ("1", "true", "yes", "on")
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        _FAST_CL_SESSION = s
    return _FAST_CL_SESSION


def _cl_get(url: str, params: Dict[str, Any], headers: Dict[str, str], timeout: float):
    """Use fail-fast session for CL search API calls."""
    throttle_courtlistener(cost=1, context="search-fallback")
    s = _get_fast_cl_session()
    return s.get(url, params=params, headers=headers, timeout=timeout)


def _extract_us_reporter_cite(citation_text: str) -> Optional[str]:
    m = re.search(r"\b(\d+)\s+U\.?\s*S\.?\s+(\d+)\b", str(citation_text or ""), re.IGNORECASE)
    if not m:
        return None
    return f"{m.group(1)} U.S. {m.group(2)}"


def _has_reporter_citation(citation_text: str) -> bool:
    """
    True when citation contains a volume-reporter-page pattern (e.g. 766 F. Supp. 3d 266,
    965 F.3d 596, 578 U.S. 330, 97 Wash. 2d 148, 641 P.2d 1180). Used to trigger exact
    citation search for federal and state reporter cites, not just U.S. / WL / docket.
    """
    if not citation_text or not citation_text.strip():
        return False
    return bool(
        re.search(
            r"\b\d+\s+(?:U\.?\s*S\.?|F\.?\s*Supp\.?\s*(?:\d+d)?|F\.?\d+d|F\.?\d+th|S\.?\s*Ct\.?|L\.?\s*Ed\.?\s*(?:2d)?|Tenn\.?|Wash\.?\s*2d|Wn\.?\s*2d|P\.?\s*2d|P\.?\s*3d)\s+\d+\b",
            citation_text,
            re.IGNORECASE,
        )
    )


# Administrative / agency reporters: CourtListener free-text search often returns unrelated
# federal district/circuit opinions that merely mention the cite. Skip search fallback for these.
_ADMIN_REPORTER_SKIP_RES = (
    re.compile(
        r"\b\d+\s+F\.?\s*C\.?\s*C\.?\s*(?:\d+d)?\s+\d+\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d+\s+F\.?\s*T\.?\s*C\.?\s*(?:\d+d)?\s+\d+\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d+\s+I\.?\s*C\.?\s*C\.?\s*(?:\d+d)?\s+\d+\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d+\s+N\.?\s*L\.?\s*R\.?\s*B\.?\s*(?:\d+d)?\s+\d+\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d+\s+S\.?\s*E\.?\s*C\.?\s*(?:\d+d)?\s+\d+\b",
        re.IGNORECASE,
    ),
    # Federal Register volume (distinct from F.3d / F.2d: requires R before page)
    re.compile(r"\b\d+\s+F\.?\s*R\.?\s+\d+\b", re.IGNORECASE),
)


def should_skip_cl_text_search_for_citation(citation_text: str) -> bool:
    """True when citation looks like an admin/agency reporter cite; CL text search is unsafe."""
    t = str(citation_text or "").strip()
    if not t:
        return False
    return any(rx.search(t) for rx in _ADMIN_REPORTER_SKIP_RES)


def _clean_citation_query(citation_text: str) -> str:
    """
    Normalize noisy citation strings into a cleaner query string for CL search.
    Keeps citation core and strips parentheticals/pincites where possible.
    """
    txt = re.sub(r"\s+", " ", str(citation_text or "")).strip()
    if not txt:
        return ""

    # Prefer the reporter core for U.S. citations (e.g., "591 U.S. 1").
    us_cite = _extract_us_reporter_cite(txt)
    if us_cite:
        return us_cite

    # Remove dense parenthetical tails that hurt search quality.
    txt = re.sub(r"\([^)]{0,140}\)", " ", txt)
    txt = re.sub(r",\s*\d+\s*$", "", txt)  # trailing pinpoint
    txt = re.sub(r"\s+", " ", txt).strip(" ,;")
    return txt


# CourtListener PACER court IDs (match PACER subdomains per https://www.courtlistener.com/help/api/rest/pacer/)
_COURT_ABBREV_TO_CL_ID: Dict[str, str] = {
    "S.D.N.Y.": "nysd",
    "S.D. N.Y.": "nysd",
    "SDNY": "nysd",
    "D.D.C.": "dcd",
    "D. D.C.": "dcd",
    "DDC": "dcd",
    "N.D. Cal.": "cand",
    "N.D.Cal.": "cand",
    "ND Cal": "cand",
    "E.D. Pa.": "paed",
    "E.D.Pa.": "paed",
    "W.D. Pa.": "pawd",
    "M.D. Pa.": "pamd",
    "N.D. Ill.": "ilnd",
    "N.D.Ill.": "ilnd",
    "S.D. Tex.": "txsd",
    "N.D. Tex.": "txnd",
    "E.D. Tex.": "txed",
    "W.D. Tex.": "txwd",
    "C.D. Cal.": "cacd",
    "E.D. Cal.": "caed",
    "S.D. Cal.": "casd",
    "N.D. Ga.": "gand",
    "S.D. Fla.": "flsd",
    "M.D. Fla.": "flmd",
    "N.D. Ohio": "ohnd",
    "S.D. Ohio": "ohsd",
    "E.D. Mich.": "mied",
    "W.D. Mich.": "miwd",
    "D. Mass.": "mad",
    "D. Md.": "mdd",
    "D. Colo.": "cod",
    "D. Ariz.": "azd",
    "9th Cir.": "ca9",
    "D.C. Cir.": "cadc",
    "Fed. Cir.": "cafc",
}


def _extract_docket_and_court(citation_text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract docket number and CourtListener court ID from citation.
    Returns (docket_number_normalized, court_id) or (None, None).
    """
    txt = str(citation_text or "").strip()
    if not txt:
        return None, None

    # Extract court from parenthetical: (S.D.N.Y.), (D.D.C.), (9th Cir.), etc.
    court_id = None
    paren = re.search(r"\(([^)]{4,50})\)", txt)
    if paren:
        inner = paren.group(1).strip()
        inner_upper = inner.upper()
        for abbrev, cid in _COURT_ABBREV_TO_CL_ID.items():
            if abbrev.upper() in inner_upper or inner_upper in abbrev.upper():
                court_id = cid
                break
        if not court_id and re.search(r"S\.?\s*D\.?\s*N\.?\s*Y\.?", inner, re.I):
            court_id = "nysd"
        if not court_id and re.search(r"D\.?\s*D\.?\s*C\.?", inner, re.I):
            court_id = "dcd"
        if not court_id and re.search(r"N\.?\s*D\.?\s*Cal", inner, re.I):
            court_id = "cand"

    # Docket patterns: "No. 24-1287", "17 Cv. 7507", "17-cv-7507", "20-CV-453-LM", "1:16-cv-00745"
    docket_raw = None
    m = re.search(r"\bNo\.\s*([A-Za-z0-9\-]+)", txt, re.IGNORECASE)
    if m:
        docket_raw = m.group(1).strip()
    if not docket_raw:
        m = re.search(r"\b(\d{1,2})\s*[-]?\s*[Cc][vV]\.?\s*[-]?\s*(\d+)(?:[-]?([A-Za-z0-9]+))?", txt)
        if m:
            docket_raw = f"{m.group(1)}-cv-{m.group(2)}"
            if m.group(3):
                docket_raw += f"-{m.group(3)}"
    if not docket_raw:
        m = re.search(r"\b(\d{1,2})\s*:\s*(\d{2})\s*[-]?\s*[Cc][vV]\.?\s*(\d+)", txt)
        if m:
            docket_raw = f"{m.group(1)}:{m.group(2)}-cv-{m.group(3)}"

    if not docket_raw:
        return None, court_id

    # Normalize: collapse spaces, lowercase cv
    normalized = re.sub(r"\s+", "", docket_raw).strip()
    normalized = re.sub(r"[Cc][Vv]", "cv", normalized)
    return normalized or docket_raw, court_id


def _cl_pacer_docket_lookup(
    base: str, headers: Dict[str, str], docket_number: str, court_id: Optional[str], timeout: float
) -> Optional[Dict[str, Any]]:
    """
    Query CourtListener PACER Dockets API. Uses same API key as citation-lookup.
    Returns first matching docket dict or None. PACER endpoints may require select-user access.
    """
    if not docket_number:
        return None
    params: Dict[str, Any] = {"docket_number": docket_number}
    if court_id:
        params["court"] = court_id
    try:
        throttle_courtlistener(cost=1, context="pacer-dockets")
        s = _get_fast_cl_session()
        resp = s.get(f"{base}/dockets/", params=params, headers=headers, timeout=min(timeout, 8.0))
        status = resp.status_code
        if status == 200:
            data = resp.json()
            results = data.get("results", [])
            resp.close()
            del resp
            if results:
                d = results[0]
                cn = d.get("case_name") or d.get("caseName") or ""
                au = d.get("absolute_url") or ""
                df = d.get("date_filed") or d.get("dateFiled") or ""
                cd = None
                if df:
                    ym = re.search(r"(\d{4})", str(df))
                    if ym:
                        cd = ym.group(1)
                return {
                    "verified": True,
                    "canonical_name": cn,
                    "canonical_date": cd,
                    "canonical_url": f"https://www.courtlistener.com{au}" if au else None,
                    "source": "CourtListener-PACER",
                    "confidence": 0.90,
                }
        else:
            if status in (401, 403):
                logger.debug("[CL-PACER] PACER Dockets API may require select-user access")
            resp.close()
            del resp
    except Exception as e:
        logger.debug(f"[CL-PACER] Docket lookup failed: {e}")
    return None


def _expand_case_aliases(case_name: str) -> list[str]:
    """Generate a few deterministic aliases for common federal party abbreviations and state reporter short names."""
    base = re.sub(r"\s+", " ", str(case_name or "")).strip()
    if not base:
        return []
    aliases = {base}
    # Feature: add abbreviation-expanded alias for better search coverage
    expanded = expand_abbreviations(base)
    if expanded and expanded != base:
        aliases.add(expanded)
    if re.search(r"\bDHS\b", base, re.IGNORECASE):
        aliases.add(re.sub(r"\bDHS\b", "Department of Homeland Security", base, flags=re.IGNORECASE))
        aliases.add(re.sub(r"\bDHS\b", "Dept. of Homeland Sec.", base, flags=re.IGNORECASE))
    if re.search(r"\bDep'?t\b", base, re.IGNORECASE):
        aliases.add(re.sub(r"\bDep'?t\b", "Department", base, flags=re.IGNORECASE))
    if re.search(r"\bUniv\.?\b", base, re.IGNORECASE):
        aliases.add(re.sub(r"\bUniv\.?\b", "University", base, flags=re.IGNORECASE))
    # Senear v. Daily J.-Am / Daily J. -Am -> Daily Journal American (Court Listener canonical name)
    if re.search(r"Daily\s+J\.?\s*-?\s*Am\.?", base, re.IGNORECASE):
        aliases.add(re.sub(r"Daily\s+J\.?\s*-?\s*Am\.?", "Daily Journal American", base, flags=re.IGNORECASE))
    return [a for a in aliases if a]


def _normalize_case_name_for_cl_search(raw: Optional[str]) -> Optional[str]:
    """
    Normalize extracted case names for CourtListener search queries only (not for scoring).
    Strips trailing ", YYYY", expands legal abbreviations (e.g. Cnty. -> County), and
    replaces spaced ampersands with "and" so fielded caseName / keyword queries match index text.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.upper() == "N/A":
        return None
    # Common extraction artifact: "Party v. Party, 2020" — caseName in CL rarely includes the year
    s = re.sub(r",?\s+(19|20)\d{2}\s*$", "", s).strip()
    if not s:
        return None
    if _CL_SEARCH_UTILS:
        try:
            s = expand_abbreviations(s)
        except Exception:
            pass
    # expand_abbreviations may match "Cnty" without the following period, leaving "County. of"
    s = re.sub(r"\bCounty\.\s+", "County ", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+&\s+", " and ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


async def cl_search_fallback(session, api_key, citation, extracted_case_name=None, extracted_date=None, timeout=10.0):
    """Search CourtListener by case name when citation-lookup returns 0 clusters. API key from config (env)."""
    api_key, base = _cl_search_api_key_and_base(api_key)
    if not api_key:
        return {"verified": False, "error": "No CourtListener API key for search"}
    headers = {"Authorization": f"Token {api_key}"}
    deadline = time.monotonic() + max(0.5, float(timeout or 0.0))

    citation_text = str(citation or "")
    if should_skip_cl_text_search_for_citation(citation_text):
        logger.info(
            "[CL-SEARCH-SKIP] Skipping CL search for administrative/agency reporter cite: %s",
            citation_text[:120],
        )
        return {
            "verified": False,
            "error": "administrative_reporter_skip",
            "method": "cl_search_skipped",
        }

    q_case_name = _normalize_case_name_for_cl_search(extracted_case_name)

    def _next_timeout(cap: float = 8.0) -> float:
        remaining = deadline - time.monotonic()
        return min(cap, remaining) if remaining > 0 else 0.0

    def _year_from_hint(value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        m = re.search(r"(19|20)\d{2}", str(value))
        return int(m.group(0)) if m else None

    us_reporter_cite = _extract_us_reporter_cite(citation_text)
    clean_citation = _clean_citation_query(citation_text)
    is_wl_or_lexis = bool(re.search(r"\b(?:19|20)\d{2}\s+(?:WL|[A-Za-z\.\s]*LEXIS)\s+\d+\b", citation_text, re.IGNORECASE))
    has_docket = bool(re.search(r"\bNo\.\s*[A-Za-z0-9\-]+", citation_text, re.IGNORECASE))
    has_reporter_cite = _has_reporter_citation(citation_text)
    do_exact_search = bool(is_wl_or_lexis or has_docket or us_reporter_cite or has_reporter_cite)

    # Strategy -1: CourtListener PACER Dockets API (direct lookup when docket number present)
    docket_num, court_id = _extract_docket_and_court(citation_text)
    # Feature: infer court from reporter when parenthetical didn't yield one
    if not court_id:
        court_id = infer_court_from_citation(citation_text)
    if docket_num:
        t_pacer = _next_timeout(6.0)
        if t_pacer > 0:
            pacer_result = _cl_pacer_docket_lookup(base, headers, docket_num, court_id, t_pacer)
            if pacer_result:
                logger.info(f"[CL-PACER] Found docket for '{citation}' via PACER Dockets API")
                return pacer_result
        # Also try without court filter if court-specific lookup returned nothing
        if court_id and t_pacer > 0:
            t_pacer2 = _next_timeout(4.0)
            if t_pacer2 > 0:
                pacer_result = _cl_pacer_docket_lookup(base, headers, docket_num, None, t_pacer2)
                if pacer_result:
                    logger.info(f"[CL-PACER] Found docket for '{citation}' via PACER (no court filter)")
                    return pacer_result

    # Strategy 0: Exact citation free-text search first (critical for WL/LEXIS/dockets)
    # This often returns the right docket/opinion even when name matching is noisy.
    if do_exact_search:
        exact_queries = []
        if us_reporter_cite:
            exact_queries.append(us_reporter_cite)
        if clean_citation:
            exact_queries.append(clean_citation)
        if citation_text:
            exact_queries.append(citation_text)
        name_for_exact = q_case_name or (
            str(extracted_case_name).strip()
            if extracted_case_name and str(extracted_case_name).strip().upper() != "N/A"
            else ""
        )
        if name_for_exact:
            for alias in _expand_case_aliases(name_for_exact):
                if us_reporter_cite:
                    exact_queries.append(f"{us_reporter_cite} {alias}")
                elif clean_citation:
                    exact_queries.append(f"{clean_citation} {alias}")

        # Keep order, drop duplicates.
        seen_q = set()
        deduped_queries = []
        for q in exact_queries:
            qn = re.sub(r"\s+", " ", str(q or "")).strip()
            if not qn or qn in seen_q:
                continue
            seen_q.add(qn)
            deduped_queries.append(qn)

        try:
            for q in deduped_queries[:4]:
                params0: Dict[str, Any] = {"q": q, "type": "o"}
                t0 = _next_timeout(4.0)
                if t0 <= 0:
                    return {"verified": False, "error": "CL search timeout budget exhausted"}
                resp0 = _cl_get(f"{base}/search/", params=params0, headers=headers, timeout=t0)
                if resp0.status_code == 200:
                    results0 = resp0.json().get("results", [])
                    resp0.close(); del resp0
                    if results0:
                        best0 = _pick_best_exact(results0, citation, extracted_case_name, prefer_docket=False)
                        if best0:
                            return _build_result(best0, citation, "exact-citation-search", extracted_case_name)
                else:
                    resp0.close(); del resp0
        except Exception:
            pass
        try:
            params0r: Dict[str, Any] = {"q": str(citation), "type": "r"}
            t0r = _next_timeout(6.0)
            if t0r <= 0:
                return {"verified": False, "error": "CL search timeout budget exhausted"}
            resp0r = _cl_get(f"{base}/search/", params=params0r, headers=headers, timeout=t0r)
            if resp0r.status_code == 200:
                results0r = resp0r.json().get("results", [])
                resp0r.close(); del resp0r
                if results0r:
                    best0r = _pick_best_exact(results0r, citation, extracted_case_name, prefer_docket=True)
                    if best0r:
                        cn = best0r.get("caseName") or best0r.get("case_name") or ""
                        au = best0r.get("absolute_url") or ""
                        cu = f"https://www.courtlistener.com{au}" if au else None
                        df = best0r.get("dateFiled") or best0r.get("date_filed") or ""
                        cd = None
                        if df:
                            m = re.search(r"(\d{4})", str(df))
                            if m:
                                cd = m.group(1)
                        return {
                            "verified": True,
                            "canonical_name": cn,
                            "canonical_date": cd,
                            "canonical_url": cu,
                            "source": "CourtListener-Docket",
                            "confidence": 0.85,
                            "candidate_citation": _candidate_citation_from_record(best0r),
                        }
            else:
                resp0r.close(); del resp0r
        except Exception:
            pass

    # Strategy 0.5: Name + date recovery lane, even when citation text is noisy.
    # CourtListener Search API expects fielded queries in the q parameter:
    # caseName:"..." AND dateFiled:[YYYY-MM-DD TO YYYY-MM-DD]
    year_hint = _year_from_hint(extracted_date)
    if q_case_name and year_hint and not _is_case_name_too_weak(extracted_case_name):
        try:
            case_escaped = q_case_name.replace('"', '\\"').strip()
            filed_after = f"{year_hint - 2}-01-01"
            filed_before = f"{year_hint + 2}-12-31"
            q_nd = f'caseName:("{case_escaped}") AND dateFiled:[{filed_after} TO {filed_before}]'
            params_nd: Dict[str, Any] = {"q": q_nd, "type": "o"}
            t_nd = _next_timeout(6.0)
            if t_nd > 0:
                resp_nd = _cl_get(f"{base}/search/", params=params_nd, headers=headers, timeout=t_nd)
                if resp_nd.status_code == 200:
                    results_nd = resp_nd.json().get("results", [])
                    resp_nd.close(); del resp_nd
                    if results_nd:
                        best_nd = _pick_best_name_date(results_nd, extracted_case_name, year_hint, citation)
                        if best_nd:
                            return _build_result(best_nd, citation, "name-date-search", extracted_case_name)
                else:
                    resp_nd.close(); del resp_nd
        except Exception:
            pass

    # Strategy 1: Opinion search with case_name + date filter
    # Use fielded q: caseName:"..." AND dateFiled:[... TO ...]
    if not q_case_name:
        return {"verified": False, "error": "No matching results for exact citation search"}
    if _is_case_name_too_weak(extracted_case_name):
        return {"verified": False, "error": "Case name too weak for reliable name-based search"}

    year = None
    if extracted_date:
        ym = re.search(r"(19|20)\d{2}", str(extracted_date))
        if ym:
            year = int(ym.group(0))
    case_escaped = q_case_name.replace('"', '\\"').strip()
    if year is not None:
        q1 = f'caseName:("{case_escaped}") AND dateFiled:[{year - 1}-01-01 TO {year + 1}-12-31]'
    else:
        q1 = f'caseName:("{case_escaped}")'
    params: Dict[str, Any] = {"q": q1, "type": "o"}
    if court_id:
        params["court"] = court_id
    try:
        t1 = _next_timeout(6.0)
        if t1 <= 0:
            return {"verified": False, "error": "CL search timeout budget exhausted"}
        resp = _cl_get(f"{base}/search/", params=params, headers=headers, timeout=t1)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            resp.close(); del resp
            if results:
                best = _pick_best(results, extracted_case_name)
                if best:
                    return _build_result(best, citation, "opinion-search", extracted_case_name)
        else:
            resp.close(); del resp

        # Strategy 1.5: Keyword free-text search with date filter
        # Handles abbreviation mismatches (e.g. "DHS" vs "Dep't of Homeland Sec.")
        # by searching content words from the case name with date bounds
        stop = {"v", "the", "of", "and", "in", "for", "on", "at", "to", "a", "an", "re"}
        kw = [w for w in re.findall(r"[A-Za-z]+", q_case_name) if w.lower() not in stop and len(w) > 1]
        if kw:
            kw_q = " ".join(kw)
            if year is not None:
                q15 = f"({kw_q}) AND dateFiled:[{year - 1}-01-01 TO {year + 1}-12-31]"
            else:
                q15 = kw_q
            params15: Dict[str, Any] = {"q": q15, "type": "o"}
            try:
                t15 = _next_timeout(5.0)
                if t15 <= 0:
                    return {"verified": False, "error": "CL search timeout budget exhausted"}
                resp15 = _cl_get(f"{base}/search/", params=params15, headers=headers, timeout=t15)
                if resp15.status_code == 200:
                    results15 = resp15.json().get("results", [])
                    resp15.close(); del resp15
                    if results15:
                        best15 = _pick_best(results15, extracted_case_name)
                        if best15:
                            return _build_result(best15, citation, "keyword-search", extracted_case_name)
                else:
                    resp15.close(); del resp15
            except Exception:
                pass

        # Strategy 2: Free-text search with case name + citation
        params2: Dict[str, Any] = {"q": f"{q_case_name} {citation}", "type": "o"}
        t2 = _next_timeout(5.0)
        if t2 <= 0:
            return {"verified": False, "error": "CL search timeout budget exhausted"}
        resp2 = _cl_get(f"{base}/search/", params=params2, headers=headers, timeout=t2)
        if resp2.status_code == 200:
            results2 = resp2.json().get("results", [])
            resp2.close(); del resp2
            if results2:
                best2 = _pick_best(results2, extracted_case_name)
                if best2:
                    return _build_result(best2, citation, "freetext-search", extracted_case_name)
        else:
            resp2.close(); del resp2

        # Strategy 3: Docket search (finds cases not yet in opinion DB)
        # Use quoted first-party + second-party for targeted search
        parts = re.split(r"\s+v\.?\s+", q_case_name, maxsplit=1)
        if len(parts) == 2:
            first_party = parts[0].strip().split()[0]  # First word of first party
            second_party = parts[1].strip().split()[0]  # First word of second party
            docket_q = f'"{first_party}" "{second_party}"'
        else:
            docket_q = q_case_name
        params3: Dict[str, Any] = {"q": docket_q, "type": "r"}
        t3 = _next_timeout(5.0)
        if t3 <= 0:
            return {"verified": False, "error": "CL search timeout budget exhausted"}
        resp3 = _cl_get(f"{base}/search/", params=params3, headers=headers, timeout=t3)
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

        # Strategy 3b: RECAP docket-entries drill-down with year-range filter
        # When Strategy 3 finds a docket by name but not a specific document, fetch
        # docket entries filtered by the citation year to locate the actual filing.
        if results3 and year:
            try:
                best3_raw = _pick_best_docket(results3, extracted_case_name)
                docket_id_recap = best3_raw.get("docket_id") or best3_raw.get("id") if best3_raw else None
                if docket_id_recap and _next_timeout() > 0:
                    after = f"{year - 1}-01-01"
                    before = f"{year + 1}-12-31"
                    t3b = _next_timeout(5.0)
                    s = _get_fast_cl_session()
                    throttle_courtlistener(cost=1, context="recap-entries")
                    re3b = s.get(
                        f"{base}/docket-entries/",
                        params={"docket": docket_id_recap, "date_filed__gte": after, "date_filed__lte": before},
                        headers=headers,
                        timeout=min(t3b, 5),
                    )
                    if re3b.status_code == 200:
                        entries = re3b.json().get("results", [])
                        re3b.close()
                        # Pick entry closest to citation year; prefer entries with "opinion" in description
                        best_entry = None
                        best_entry_score = -1
                        for entry in entries[:20]:
                            df_e = entry.get("date_filed") or ""
                            desc = (entry.get("description") or "").lower()
                            score_e = 0
                            if df_e:
                                em = re.search(r"(\d{4})", df_e)
                                if em and int(em.group(1)) == year:
                                    score_e += 5
                            if any(kw in desc for kw in ("opinion", "order", "judgment", "decision")):
                                score_e += 3
                            docs = entry.get("recap_documents", [])
                            if docs:
                                score_e += 1
                            if score_e > best_entry_score:
                                best_entry_score = score_e
                                best_entry = entry
                        if best_entry and best_entry_score >= 3:
                            recap_docs = best_entry.get("recap_documents", [])
                            doc_url = None
                            if recap_docs:
                                doc_url = recap_docs[0].get("absolute_url") or ""
                                if doc_url and not doc_url.startswith("http"):
                                    doc_url = "https://www.courtlistener.com" + doc_url
                            if not doc_url:
                                au_recap = best3_raw.get("absolute_url") or ""
                                doc_url = f"https://www.courtlistener.com{au_recap}" if au_recap else None
                            cn_recap = best3_raw.get("caseName") or best3_raw.get("case_name") or ""
                            logger.info(f"[CL-RECAP-ENTRIES] Found dated entry for '{citation}' (score={best_entry_score})")
                            return {
                                "verified": True,
                                "canonical_name": cn_recap,
                                "canonical_date": str(year),
                                "canonical_url": doc_url,
                                "source": "CourtListener-RECAP",
                                "confidence": 0.80,
                                "diagnostic": "Found via RECAP docket-entries date filter",
                            }
            except Exception:
                pass

        return {"verified": False, "error": "No matching results in any search strategy"}
    except Exception as e:
        logger.warning(f"CL search fallback failed: {e}")
        return {"verified": False, "error": str(e)}


def _candidate_citation_from_record(best: Dict[str, Any]) -> Optional[str]:
    if not isinstance(best, dict):
        return None
    direct = best.get("citation") or best.get("short_citation")
    if direct:
        return str(direct)
    cits = best.get("citations") or best.get("cites") or best.get("citations_text")
    if isinstance(cits, list):
        for item in cits:
            if item:
                return str(item)
    if isinstance(cits, str):
        return cits
    return None


def _citation_core_key(text: str) -> str:
    s = str(text or "")
    m = re.search(r"\b((?:17|18|19|20)\d{2})\s*(WL|U\.?\s*S\.?\s*LEXIS|LEXIS)\s*(\d+)\b", s, re.IGNORECASE)
    if m:
        return f"{m.group(1)} {m.group(2).lower()} {m.group(3)}"
    m = re.search(
        r"\b\d+\s+(?:U\.?\s*S\.?|F\.?\s*Supp\.?\s*(?:\d+d)?|F\.?\d+d|F\.?\d+th|S\.?\s*Ct\.?|L\.?\s*Ed\.?\s*(?:2d)?|Tenn\.?)\s+\d+\b",
        s,
        re.IGNORECASE,
    )
    if m:
        return re.sub(r"\s+", " ", m.group(0).strip()).lower()
    # Normalize state reporter abbreviations for gate comparison (e.g. 19 Wn. App. 2d 113 vs 19 Wash. App. 2d 113)
    s = re.sub(r"\bWn\.?\s*", "Wash. ", s, flags=re.IGNORECASE)
    s = re.sub(r"\bWash\.?\s*", "Wash. ", s, flags=re.IGNORECASE)
    # Normalize P.3d/P.2d spacing (e.g. "P. 3d" vs "P.3d")
    s = re.sub(r"\bP\.\s*3d\b", "P.3d", s, flags=re.IGNORECASE)
    s = re.sub(r"\bP\.\s*2d\b", "P.2d", s, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", s.strip()).lower()


def _build_result(best, citation, method, extracted_case_name=None):
    cn = best.get("caseName") or best.get("case_name") or ""
    df = best.get("dateFiled") or best.get("date_filed") or ""
    au = best.get("absolute_url") or ""
    cd = None
    if df:
        m = re.search(r"(\d{4})", df)
        if m:
            cd = m.group(1)
    cu = "https://www.courtlistener.com" + au if au else None
    candidate_citation = _candidate_citation_from_record(best)
    logger.info("[CL-SEARCH-FALLBACK] Found '{}' for '{}' via {}".format(cn, citation, method))
    result = {
        "verified": True,
        "canonical_name": cn,
        "canonical_date": cd,
        "canonical_url": cu,
        "source": "CourtListener-Search",
        "confidence": 0.85,
        "candidate_citation": candidate_citation,
        "search_method": method,
    }
    # Feature 5 & 6: weighted scoring + diagnostics
    try:
        from src.utils.verification_scoring import compute_weighted_confidence
        year_m = re.search(r"(\d{4})", str(citation or ""))
        sub_year = int(year_m.group(1)) if year_m else None
        can_year_m = re.search(r"(\d{4})", str(cd or ""))
        can_year = int(can_year_m.group(1)) if can_year_m else None
        scoring = compute_weighted_confidence(
            submitted_name=extracted_case_name,
            canonical_name=cn,
            submitted_year=sub_year,
            canonical_year=can_year,
        )
        result["confidence_detail"] = scoring
        if scoring.get("diagnostics"):
            result["verification_note"] = "; ".join(scoring["diagnostics"])
    except Exception:
        pass
    return result


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


def _is_case_name_too_weak(ecn):
    if not ecn:
        return True
    e = str(ecn).strip()
    if not e or e.lower() == "n/a":
        return True
    # Single-token or no-versus names are too ambiguous for name-only searches.
    tokens = re.findall(r"[A-Za-z]+", e)
    if len(tokens) <= 1:
        return True
    if not re.search(r"\bv\.?\b", e, re.IGNORECASE):
        return True
    return False


def _pick_best_exact(results, citation, extracted_case_name, prefer_docket=False):
    """
    Score exact-citation search results using citation fingerprints first, then name overlap.
    Prevents weak-name mismatches like "Gomes" -> unrelated case.
    """
    if not results:
        return None
    citation_text = str(citation or "")
    citation_lower = citation_text.lower()
    wl_match = re.search(r"\b((?:19|20)\d{2})\s+WL\s+(\d+)\b", citation_text, re.IGNORECASE)
    year_hint = wl_match.group(1) if wl_match else None
    wl_id_hint = wl_match.group(2) if wl_match else None
    docket_hint = None
    docket_m = re.search(r"\bNo\.\s*([A-Za-z0-9\-]+)", citation_text, re.IGNORECASE)
    if docket_m:
        docket_hint = docket_m.group(1).lower()

    name_tokens = []
    if extracted_case_name and str(extracted_case_name).strip().lower() != "n/a":
        stop = {"v", "the", "of", "and", "inc", "llc", "co", "corp", "ltd", "dep", "dept", "secy", "sec"}
        name_tokens = [w for w in re.findall(r"[a-z]+", str(extracted_case_name).lower()) if w not in stop and len(w) >= 3]

    best = None
    best_score = -1

    def _wl_in_authoritative_fields(rec, wl_year, wl_id):
        """True when WL appears in citation-identity fields, not just generic snippets."""
        if not wl_year or not wl_id or not isinstance(rec, dict):
            return False
        wl_pat = re.compile(rf"\b{re.escape(str(wl_year))}\s+WL\s+{re.escape(str(wl_id))}\b", re.IGNORECASE)
        wl_id_pat = re.compile(rf"\bWL\s+{re.escape(str(wl_id))}\b", re.IGNORECASE)

        authoritative_keys = (
            "citation", "citations", "cites", "citations_text",
            "docketNumber", "docket_number",
            "absolute_url", "caseName", "case_name", "short_citation",
        )
        for k in authoritative_keys:
            if k not in rec:
                continue
            v = rec.get(k)
            txt = str(v or "")
            if wl_pat.search(txt) or wl_id_pat.search(txt):
                return True
        return False

    for r in results[:15]:
        score = 0
        blob = str(r).lower()
        case_name = (r.get("caseName") or r.get("case_name") or "").lower()
        abs_url = (r.get("absolute_url") or "").lower()

        # Strongest: explicit WL fingerprint in result payload.
        authoritative_wl = _wl_in_authoritative_fields(r, year_hint, wl_id_hint) if wl_id_hint else False
        if wl_id_hint and authoritative_wl:
            score += 8
        elif wl_id_hint and wl_id_hint in blob:
            # WL appears only in broad/snippet payload - weak evidence, avoid high scoring.
            score += 1
        if year_hint and year_hint in blob:
            score += 2

        # Docket hint from citation text.
        if docket_hint and docket_hint in blob:
            score += 4

        # Helpful when WL id is absent from payload: party token match in case name.
        if name_tokens:
            overlap = sum(1 for t in name_tokens if t in case_name)
            if overlap:
                score += min(4, overlap)

        # Prefer docket-style hits when searching type=r.
        if prefer_docket and ("/docket/" in abs_url or "docket" in blob):
            score += 2

        # Exact citation text fragments can appear in snippets.
        if citation_lower and citation_lower[:20] in blob:
            score += 1

        # For WL citations, require explicit WL-id evidence to avoid cross-case picks.
        if wl_id_hint and (wl_id_hint not in blob):
            continue
        # For WL citations, reject low-quality matches unless WL is present in citation-like fields.
        if wl_id_hint and not authoritative_wl:
            # Allow only if extracted case-name has meaningful overlap with candidate.
            name_overlap = 0
            if name_tokens:
                name_overlap = sum(1 for t in name_tokens if t in case_name)
            if name_overlap < 2:
                continue

        if score > best_score:
            best_score = score
            best = r

    # Avoid taking arbitrary first result unless we have a strong enough signal.
    min_score = 9 if wl_id_hint else 3
    return best if best_score >= min_score else None


def _pick_best(results, ecn):
    stop = {"v", "the", "of", "and", "inc", "llc", "co", "corp", "ltd"}
    ecn_w = set(re.findall(r"[a-z]+", ecn.lower())) - stop
    if not ecn_w:
        return results[0] if results else None
    # Extract first-party words for stricter matching
    ecn_parts = re.split(r"\s+v\.?\s+", ecn.lower(), maxsplit=1)
    ecn_first = set(re.findall(r"[a-z]+", ecn_parts[0])) - stop
    best, best_s = None, 0
    for r in results[:10]:
        cn = (r.get("caseName") or r.get("case_name") or "").lower()
        cn_w = set(re.findall(r"[a-z]+", cn)) - stop
        if cn_w:
            # Require at least one first-party word to match (prevents e.g. "Trump v. Trump" for "Doe v. Trump")
            if ecn_first:
                cn_parts = re.split(r"\s+v\.?\s+", cn, maxsplit=1)
                cn_all_parties = set(re.findall(r"[a-z]+", cn)) - stop
                if not _prefix_overlap(ecn_first, cn_all_parties):
                    continue
            s = _prefix_overlap(ecn_w, cn_w) / len(ecn_w)
            if s > best_s:
                best_s = s
                best = r
    return best if best_s >= 0.4 else None


def _pick_best_name_date(results, ecn, year_hint, submitted_citation=""):
    """Score by case-name overlap and date proximity for citation-mismatch recovery."""
    stop = {"v", "the", "of", "and", "inc", "llc", "co", "corp", "ltd", "dept", "dep"}
    ecn_w = set(re.findall(r"[a-z]+", str(ecn or "").lower())) - stop
    if not ecn_w:
        return None

    best = None
    best_score = -1.0
    submitted_core = _citation_core_key(str(submitted_citation or ""))
    submitted_has_reporter_core = bool(
        re.search(
            r"\b\d+\s+(?:U\.?\s*S\.?|F\.?\s*Supp\.?\s*(?:\d+d)?|F\.?\d+d|F\.?\d+th|S\.?\s*Ct\.?|L\.?\s*Ed\.?\s*(?:2d)?|Tenn\.?)\s+\d+\b",
            str(submitted_citation or ""),
            re.IGNORECASE,
        )
    )
    for r in results[:20]:
        cn = (r.get("caseName") or r.get("case_name") or "").lower()
        if not cn:
            continue
        cn_w = set(re.findall(r"[a-z]+", cn)) - stop
        if not cn_w:
            continue
        overlap = len(ecn_w & cn_w) / max(1, len(ecn_w | cn_w))
        if overlap < 0.30:
            continue

        score = overlap * 10.0
        candidate_citation = _candidate_citation_from_record(r)
        candidate_core = _citation_core_key(str(candidate_citation or ""))
        if submitted_has_reporter_core and candidate_citation:
            if submitted_core == candidate_core:
                score += 6.0
            else:
                score -= 6.0
        df = str(r.get("dateFiled") or r.get("date_filed") or "")
        ym = re.search(r"(19|20)\d{2}", df)
        if ym:
            y = int(ym.group(0))
            diff = abs(y - int(year_hint))
            if diff == 0:
                score += 4.0
            elif diff == 1:
                score += 2.0
            elif diff == 2:
                score += 1.0
            else:
                score -= min(3.0, float(diff) * 0.5)

        if score > best_score:
            best_score = score
            best = r

    return best if best_score >= 5.0 else None


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

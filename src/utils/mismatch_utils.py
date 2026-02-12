"""
Standalone mismatch annotation utilities.

Extracted from citation_extraction_endpoint.py to avoid circular imports
when called from rq_worker.py.
"""

import difflib
import logging
import re

logger = logging.getLogger(__name__)


def _normalize_name_tokens(name: str) -> set:
    """Normalize a case name into a set of meaningful tokens."""
    s = str(name).lower().replace("'", "'")
    repl = {
        "dept.": "department",
        "dep't": "department",
        "dep.": "department",
        "comm'n": "commission",
        "comm.": "commission",
        "admin.": "administration",
        "auth.": "authority",
        "ins.": "insurance",
        "transp.": "transportation",
        "educ.": "education",
        "corp.": "corporation",
        "corp": "corporation",
        "co.": "company",
        "assn.": "association",
        "ass'n": "association",
        "nat'l": "national",
        "int'l": "international",
        "nat.": "natural",
        "nat": "natural",
        "res.": "resources",
        "res": "resources",
        "mut.": "mutual",
        "auto": "automobile",
        "sch.": "school",
        "dist.": "district",
        "u.s.": "us",
    }
    for k, v in repl.items():
        s = s.replace(k, v)
    cleaned = re.sub(r"[^a-z0-9\s]", " ", s)
    raw = [t for t in cleaned.split() if len(t) > 2 and not t.isdigit()]
    stop = {
        "state", "of", "the", "and", "city", "borough", "board",
        "united", "states", "et", "al", "v",
        "inc", "llc", "company", "corporation", "association",
        "foundation", "institute", "services", "service",
        "department", "commission", "administration", "agency",
        "authority", "office", "division", "bureau", "public",
        "utility", "insurance", "motor", "vehicle", "transportation",
        "education", "commerce", "community", "economic", "development",
        "corporations", "business", "professional", "licensing",
        "petitioners", "respondent", "appellant", "appellee",
        "plaintiff", "defendant", "aka", "no",
    }
    tokens = [t for t in raw if t not in stop]
    return set(tokens)


def _name_similarity(extracted: str, canonical: str) -> float:
    """Calculate similarity between two case names using fuzzy token matching."""
    a = _normalize_name_tokens(extracted)
    b = _normalize_name_tokens(canonical)
    if not a or not b:
        def light_tokens(s: str) -> set:
            s2 = re.sub(r"[^a-z0-9\s]", " ", str(s).lower())
            return set(t for t in s2.split() if len(t) > 2 and not t.isdigit())

        la = light_tokens(extracted)
        lb = light_tokens(canonical)
        if not la or not lb:
            return 0.0
        inter = la.intersection(lb)
        union = la.union(lb)
        return (len(inter) / len(union)) if union else 0.0

    matched_a = set()
    matched_b = set()
    for ta in a:
        if ta in b:
            matched_a.add(ta)
            matched_b.add(ta)
            continue
        best = None
        best_r = 0.0
        for tb in b:
            r = difflib.SequenceMatcher(None, ta, tb).ratio()
            if r > best_r:
                best_r = r
                best = tb
        if best_r >= 0.88 and (len(ta) >= 5 or len(best or "") >= 5):
            matched_a.add(ta)
            matched_b.add(best)

    inter_size = len(matched_a)
    union_size = len(a.union(b))
    j = (inter_size / union_size) if union_size else 0.0
    cov_a = (inter_size / len(a)) if a else 0.0
    cov_b = (inter_size / len(b)) if b else 0.0
    return max(j, cov_a, cov_b)


def _names_equivalent(
    extracted: str, canonical: str, *, verified: bool = False, canonical_url: str | None = None
) -> bool:
    """Decide if two case names should be treated as equivalent."""
    if not extracted or not canonical or extracted == "N/A" or canonical == "N/A":
        return False

    def strip_trailing_date(name: str) -> str:
        s = re.sub(r",?\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}\s*$", "", name)
        s = re.sub(r",?\s*\d{4}\s*$", "", s)
        s = re.sub(r"\s*\(\d{4}\)\s*$", "", s)
        return s.strip()

    extracted_clean = strip_trailing_date(extracted)
    canonical_clean = strip_trailing_date(canonical)

    if extracted_clean.lower() == canonical_clean.lower():
        return True

    def normalize_punctuation(s: str) -> str:
        s = re.sub(r'\b(Co|Inc|Corp|Ltd|Ass|Assn|Assoc|Dept|Org|Mfg|Manuf|Dist|Servs|Serv)\b\.?', r'\1', s, flags=re.IGNORECASE)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    if normalize_punctuation(extracted_clean).lower() == normalize_punctuation(canonical_clean).lower():
        return True

    def fix_missing_spaces(s: str) -> str:
        s = re.sub(r'([a-z])(of|the|and|for|in|to|by|at|on|v)\b', r'\1 \2', s)
        s = re.sub(r'([A-Z][a-z]+)(of|the|and|for|in|to|by|at|on)\b', r'\1 \2', s)
        return s

    extracted_fixed = fix_missing_spaces(extracted_clean)
    canonical_fixed = fix_missing_spaces(canonical_clean)
    if normalize_punctuation(extracted_fixed).lower() == normalize_punctuation(canonical_fixed).lower():
        return True

    sim = _name_similarity(extracted_fixed, canonical_fixed)
    if sim >= 0.6:
        return True

    if sim < 0.1:
        return False

    if verified or canonical_url:
        if sim >= 0.5:
            return True

    def gov_strip_tokens(s: str) -> set:
        s2 = str(s).lower().replace("'", "'")
        s2 = re.sub(r"[^a-z0-9\s]", " ", s2)
        raw = [t for t in s2.split() if len(t) > 2 and not t.isdigit()]
        gov_words = {
            "department", "commission", "administration", "agency",
            "authority", "office", "division", "bureau", "public",
            "utility", "insurance", "motor", "vehicle", "commonwealth",
            "state", "pennsylvania", "michigan", "transportation",
            "education", "commerce", "community", "economic",
            "development", "corporations", "business", "professional",
            "licensing", "petitioners", "respondent", "appellant",
            "appellee", "plaintiff", "defendant", "aka", "no", "et", "al",
        }
        return set(t for t in raw if t not in gov_words)

    ga = gov_strip_tokens(extracted)
    gb = gov_strip_tokens(canonical)
    if ga and gb:
        inter = ga.intersection(gb)
        union = ga.union(gb)
        j = (len(inter) / len(union)) if union else 0.0
        cov = max(len(inter) / len(ga) if ga else 0.0, len(inter) / len(gb) if gb else 0.0)
        if max(j, cov) >= 0.85:
            return True
        if verified or canonical_url:
            if ga.issubset(gb) or gb.issubset(ga):
                if inter:
                    return True

    def extract_parties(name: str) -> tuple:
        parts = re.split(r"\bv\b", name.lower(), maxsplit=1)
        if len(parts) == 2:
            first_party = parts[0].strip()
            second_party = parts[1].strip()
            common_words = {"the", "and", "of", "in", "on", "at", "by", "for", "with", "a", "an"}
            first_words = set(w for w in first_party.split() if len(w) > 2 and w not in common_words)
            second_words = set(w for w in second_party.split() if len(w) > 2 and w not in common_words)
            return first_words, second_words
        return set(), set()

    first1, second1 = extract_parties(extracted)
    first2, second2 = extract_parties(canonical)

    if second1 and second2:
        second_overlap = second1 & second2
        if second_overlap:
            first_overlap = first1 & first2
            if first_overlap:
                return True
            if first1.issubset(first2) or first2.issubset(first1):
                return True
            if first1 and first2:
                first_smaller = min(first1, first2, key=len)
                first_larger = max(first1, first2, key=len)
                first_overlap_count = len(first_smaller & first_larger)
                if first_smaller and first_overlap_count / len(first_smaller) >= 0.3:
                    return True
            if verified or canonical_url:
                if len(second_overlap) >= 1:
                    return True

    return False


def _extract_year(date_str) -> str | None:
    """Extract 4-digit year from a date string."""
    if not date_str:
        return None
    match = re.search(r"(19|20)\d{2}", str(date_str))
    return match.group(0) if match else None


def annotate_mismatch_flags(
    citations: list, clusters: list, name_threshold: float = 0.4, year_tolerance: int = 0
) -> None:
    """Annotate per-citation mismatch flags and compute cluster-level summaries in-place."""
    try:
        for cit in citations or []:
            if not isinstance(cit, dict):
                continue
            extracted = cit.get("extracted_case_name")
            canonical = cit.get("canonical_name")
            verified = bool(cit.get("verified"))
            canonical_url = cit.get("canonical_url")

            if not extracted or extracted == "N/A":
                name_mismatch = False
            elif extracted and canonical:
                equiv = _names_equivalent(extracted, canonical, verified=verified, canonical_url=canonical_url)
                name_mismatch = not equiv
            else:
                sim = _name_similarity(extracted, canonical) if (extracted and canonical) else 0.0
                name_mismatch = bool(extracted and canonical and sim < name_threshold)

            y_ex = _extract_year(cit.get("extracted_date"))
            y_ca = _extract_year(cit.get("canonical_date"))
            if not y_ca:
                date_mismatch = False
            else:
                effective_tolerance = year_tolerance
                if verified and canonical_url:
                    effective_tolerance = max(year_tolerance, 1)
                date_mismatch = bool(y_ex and y_ca and abs(int(y_ex) - int(y_ca)) > effective_tolerance)

            cit["name_mismatch"] = name_mismatch
            cit["date_mismatch"] = date_mismatch
            if cit.get("verified") and name_mismatch:
                cit["possible_match"] = True

        for cluster in clusters or []:
            cluster_cits = cluster.get("citations") or []
            mm_indices = []
            has_name = False
            has_date = False
            for idx, c in enumerate(cluster_cits):
                if isinstance(c, dict):
                    nm = bool(c.get("name_mismatch"))
                    dm = bool(c.get("date_mismatch"))
                    is_verified = bool(c.get("verified"))
                else:
                    nm = bool(getattr(c, "name_mismatch", False))
                    dm = bool(getattr(c, "date_mismatch", False))
                    is_verified = bool(getattr(c, "verified", False))
                if is_verified and (nm or dm):
                    mm_indices.append(idx)
                if is_verified:
                    has_name = has_name or nm
                    has_date = has_date or dm

            cluster["has_name_mismatch"] = has_name
            cluster["has_date_mismatch"] = has_date
            cluster["mismatch_indices"] = mm_indices
    except Exception as e:
        logger.warning(f"[MISMATCH-ANNOTATE] Failed to annotate mismatch flags: {e}")

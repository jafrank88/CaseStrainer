"""
Canonical date extraction from CourtListener data.

Handles complex date priority logic including Supreme Court DB update detection.
Extracted from unified_verification_master.py (P1 refactoring).

CRITICAL: date_modified is the DB record update timestamp, not decision date
All Supreme Court reporters: U.S., S. Ct., L. Ed., S.Ct., L.Ed., L.Ed.2d
"""

import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def extract_canonical_date(cluster: Dict[str, Any], citation: str = "", extracted_year: Optional[int] = None) -> Optional[str]:
    """
    Extract canonical date from CourtListener cluster with correct priority.

    CourtListener Date Field Priority (from best to worst):
    1. date_reargued / dateReargued - When case was reargued (most specific, if applicable)
    2. Extracted year from document - Year from citation context (reliable for verification)
    3. date_filed / dateFiled - Decision/filing date (generally correct, but can be DB update for old cases)
    4. date_argued / dateArgued - Argument date (fallback only)

    CRITICAL NOTES:
    - date_modified / dateModified is IGNORED - it's the DB record update timestamp, not decision date
    - date_filed is often WRONG for older cases - it can be:
      * Database update date (when CourtListener added/modified the record)
      * For SCOTUS cases from 1970s-2000s, date_filed often shows 2020-2021 (DB updates)
    - extracted_year from document context is often more reliable than date_filed for verification
    """
    from datetime import datetime

    # Get all available date fields from CourtListener (try both camelCase and snake_case)
    decided = cluster.get("date_filed") or cluster.get("dateFiled")
    argued = cluster.get("date_argued") or cluster.get("dateArgued")
    date_reargued = cluster.get("date_reargued") or cluster.get("dateReargued")

    logger.info(
        f"[DATE] {citation}: Available dates - "
        f"filed:{decided}, reargued:{date_reargued}, argued:{argued}, extracted_year:{extracted_year}"
    )

    # PRIORITY 1: If case was reargued, use reargument date (more specific than original filing)
    if date_reargued:
        return date_reargued

    # Check if this is a Supreme Court case
    is_supreme_court = False

    court_str = str(cluster.get("court", "")).lower()
    if any(court in court_str for court in ["supreme", "scotus", "u.s. supreme"]):
        is_supreme_court = True

    if not is_supreme_court and citation:
        citation_str = str(citation)
        scotus_reporters = [
            " U.S. ", " S. Ct. ", " S.Ct. ", " L. Ed. ", " L.Ed. ",
            " L. Ed. 2d ", " L.Ed.2d ",
        ]
        scotus_start_reporters = ["U.S. ", "S. Ct. ", "S.Ct. ", "L. Ed. ", "L.Ed. ", "L. Ed. 2d ", "L.Ed.2d "]

        if any(reporter in citation_str for reporter in scotus_reporters) or \
           any(citation_str.startswith(reporter) for reporter in scotus_start_reporters):
            is_supreme_court = True

    # SUPREME COURT HANDLING
    if is_supreme_court and decided and extracted_year is not None:
        try:
            decided_dt = datetime.strptime(decided, "%Y-%m-%d")
            decided_year = decided_dt.year
            year_diff = abs(decided_year - extracted_year)

            # SCOTUS date_filed priority: decided_year < 2019 uses date_filed directly
            if decided_year < 2019:
                return decided

            if decided_year >= 2019 and extracted_year < 2015 and year_diff > 5:
                logger.warning(
                    f"[DATE] {citation}: Supreme Court - date_filed ({decided_year}) is from bulk update period "
                    f"but extracted_year ({extracted_year}) is much older ({year_diff} years). "
                    f"Using extracted year - date_filed is likely DB update date."
                )
                return f"{extracted_year}-01-01"

            if decided_year >= 2015 and extracted_year >= 2015:
                if abs(decided_year - extracted_year) <= 1:
                    try:
                        decided_dt = datetime.strptime(decided, "%Y-%m-%d")
                        if extracted_year == decided_year - 1 and decided_dt.month <= 3:
                            logger.warning(
                                f"[DATE] {citation}: Supreme Court - date_filed {decided} appears to be DB update "
                                f"(early {decided_year} for case from {extracted_year}). Using extracted year."
                            )
                            return f"{extracted_year}-12-31"
                    except Exception:
                        pass
                    return decided
                return decided

            if decided_year >= 2019 and extracted_year >= 2015:
                try:
                    decided_dt = datetime.strptime(decided, "%Y-%m-%d")
                    if extracted_year == decided_year - 1 and decided_dt.month <= 3:
                        logger.warning(
                            f"[DATE] {citation}: Supreme Court - date_filed {decided} appears to be DB update "
                            f"(early {decided_year} for case from {extracted_year}). Using extracted year."
                        )
                        return f"{extracted_year}-12-31"
                except Exception:
                    pass
                return decided

            return decided

        except Exception as e:
            logger.warning(f"[DATE] {citation}: Error parsing date_filed: {e}")

    if extracted_year is not None and is_supreme_court:
        return f"{extracted_year}-01-01"

    # NON-SUPREME COURT HANDLING
    if extracted_year is not None:
        if decided:
            try:
                decided_dt = datetime.strptime(decided, "%Y-%m-%d")
                decided_year = decided_dt.year
                year_diff = abs(decided_year - extracted_year)

                if decided_year >= 2015 and extracted_year < 2015 and year_diff > 5:
                    logger.warning(
                        f"[DATE] {citation}: date_filed ({decided_year}) is recent but extracted_year ({extracted_year}) "
                        f"is much older ({year_diff} years difference). Likely DB update date - using extracted year."
                    )
                    return str(extracted_year)

                if year_diff > 1:
                    logger.warning(f"[DATE] {citation}: Year mismatch - date_filed:{decided_year} vs extracted:{extracted_year}, trusting date_filed")
                    return decided

                    # Unreachable snippet search code preserved for reference
                    opinions = cluster.get("opinions", [])
                    if opinions and isinstance(opinions, list):
                        for opinion in opinions:
                            snippet = opinion.get("snippet", "").lower()
                            if "decided" in snippet:
                                for pattern in [
                                    r"decided\s+([a-z]+\s+\d{1,2},\s*\d{4})",
                                    r"decided\s+on\s+([a-z]+\s+\d{1,2},\s*\d{4})",
                                    r"opinion\s+delivered\s+([a-z]+\s+\d{1,2},\s*\d{4})"
                                ]:
                                    match = re.search(pattern, snippet)
                                    if match:
                                        date_str = match.group(1)
                                        for fmt in ["%B %d, %Y", "%b %d, %Y", "%b. %d, %Y"]:
                                            try:
                                                parsed_date = datetime.strptime(date_str, fmt)
                                                if parsed_date.year == extracted_year:
                                                    formatted = parsed_date.strftime("%Y-%m-%d")
                                                    return formatted
                                            except:
                                                continue

                    try:
                        corrected_date = decided_dt.replace(year=extracted_year)
                        formatted_date = corrected_date.strftime("%Y-%m-%d")
                        return formatted_date
                    except:
                        return str(extracted_year)

            except Exception as e:
                logger.warning(f"[DATE] {citation}: Error processing dates: {e}")

    if decided:
        return decided
    if argued:
        return argued

    # Try docket as last resort
    try:
        docket = cluster.get("docket", {})
        if isinstance(docket, dict):
            docket_date = docket.get("date_filed") or docket.get("dateFiled")
            if docket_date:
                return docket_date
    except:
        pass

    if extracted_year is not None and decided:
        try:
            decided_dt = datetime.strptime(decided, "%Y-%m-%d")
            decided_year = decided_dt.year
            year_diff = abs(decided_year - extracted_year)

            if decided_year >= 2015 and extracted_year < 2015 and year_diff > 5:
                return str(extracted_year)
        except Exception:
            pass

    if decided:
        try:
            decided_dt = datetime.strptime(decided, "%Y-%m-%d")
            decided_year = decided_dt.year
            current_year = datetime.now().year

            if decided_year >= 2015 and extracted_year is not None and extracted_year < 2015:
                year_diff = abs(decided_year - extracted_year)
                if year_diff > 5:
                    return str(extracted_year)
                return decided

            if decided_year >= current_year - 5:
                volume_match = re.search(r"(\d+)\s+(?:U\.S\.|F\.\s*3d|F\.\s*2d|F\.\s*Supp|Va\.|S\.E\.|N\.E\.|N\.W\.|S\.W\.|So\.|P\.|P\.2d|A\.|A\.2d)", citation)
                if volume_match:
                    volume = int(volume_match.group(1))
                    if "U.S." in citation and 400 <= volume <= 550:
                        if extracted_year:
                            return str(extracted_year)
                    elif any(reporter in citation for reporter in ["Va.", "S.E.", "N.E.", "N.W.", "S.W.", "So.", "P.", "A."]):
                        if extracted_year and extracted_year < 2015:
                            return str(extracted_year)
        except Exception:
            pass

        return decided

    if extracted_year is not None:
        return str(extracted_year)

    if argued:
        return argued

    docket = cluster.get("docket", {})
    if isinstance(docket, dict):
        docket_date = docket.get("date_filed") or docket.get("dateFiled")
        if docket_date:
            return docket_date

    logger.warning(f"[DATE] {citation}: No date found in cluster")
    return None


def _year_from_date_or_citation(date_str: Optional[str], citation: str) -> Optional[int]:
    """Extract a 4-digit year from date string or citation. Used to skip CaseMine for pre-1851 cases."""
    if date_str:
        m = re.search(r"\b(18|19|20)\d{2}\b", str(date_str))
        if m:
            return int(m.group(0))
    m = re.search(r"\b(18|19|20)\d{2}\b", citation)
    if m:
        return int(m.group(0))
    return None

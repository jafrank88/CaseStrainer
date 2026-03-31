"""
Known citation lookup tables and helpers.

Static lookup tables for citations that are frequently misresolved by APIs.
Extracted from unified_verification_master.py (P1 refactoring).
"""

import re
from typing import Dict, Any, Optional, cast


def _normalize_citation_for_known_lookup(citation: str) -> str:
    """Normalize citation so it matches KNOWN_FEDERAL_CITATIONS keys (e.g. '426 U. S. 26' -> '426 u.s. 26')."""
    if not citation:
        return ""
    s = re.sub(r"\s+", " ", citation.strip()).lower()
    # Collapse "u. s." to "u.s." so "426 u. s. 26" matches key "426 u.s. 26"
    s = re.sub(r"u\.\s*s\.?", "u.s.", s, flags=re.IGNORECASE)
    # Supreme Court Reporter: "143 S. Ct. 2429" -> "143 s. ct. 2429"
    s = re.sub(r"s\.\s*ct\.\s*", "s. ct. ", s, flags=re.IGNORECASE)
    # Collapse "f. 3d" / "f. 2d" / "f. 4th" to "f.3d" etc. so "199 f. 3d 263" matches "199 f.3d 263"
    s = re.sub(r"f\.\s*3d\b", "f.3d", s, flags=re.IGNORECASE)
    s = re.sub(r"f\.\s*2d\b", "f.2d", s, flags=re.IGNORECASE)
    s = re.sub(r"f\.\s*4th\b", "f.4th", s, flags=re.IGNORECASE)
    # F. Supp.: normalize 2d/3d before first series so "968 F. Supp. 2d 367" is not parsed as supp + "2"
    s = re.sub(r"f\.\s*supp\.?\s*2d\b", "f. supp. 2d", s, flags=re.IGNORECASE)
    s = re.sub(r"f\.\s*supp\.?\s*3d\b", "f. supp. 3d", s, flags=re.IGNORECASE)
    s = re.sub(r"f\.\s*supp\.?\s+", "f. supp. ", s, flags=re.IGNORECASE)
    return s.strip()


def _wl_citation_key(citation: str) -> Optional[str]:
    """Return normalized 'YYYY wl NNNNNNN' if citation contains a Westlaw id, else None."""
    if not citation:
        return None
    s = re.sub(r"\s+", " ", citation.strip().lower())
    m = re.search(r"\b((?:19|20)\d{2})\s+wl\s+(\d+)\b", s, re.IGNORECASE)
    if not m:
        return None
    return f"{m.group(1)} wl {m.group(2)}"


# Westlaw / WL cites CourtListener often does not cluster; batch CL can also return the wrong MDL sibling.
# force_override is added by _lookup_known_federal so batch mode can replace a bad verified hit.
KNOWN_WL_CITATIONS = {
    # 74 F. Supp. 3d 1052 (N.D. Cal. 2014); CL opinion https://www.courtlistener.com/opinion/2171586/
    "2014 wl 6465235": {
        "canonical_name": "United Food & Commercial Workers Local 1776 v. Teikoku Pharma USA, Inc.",
        "canonical_date": "2014-11-17",
        "canonical_year": "2014",
        "canonical_url": "https://www.courtlistener.com/opinion/7311104/united-food-commercial-workers-local-1776-v-teikoku-pharma-usa-inc/",
    },
    # In re Effexor XR Antitrust Litig., No. 11-cv-5479 (D.N.J. Oct. 6, 2014) — RECAP PDF on CL storage
    "2014 wl 4988410": {
        "canonical_name": "In re Effexor XR Antitrust Litigation",
        "canonical_date": "2014-10-06",
        "canonical_year": "2014",
        "canonical_url": "https://storage.courtlistener.com/recap/gov.uscourts.njd.264958.19.0.pdf",
    },
    # Cal. Supreme May 7, 2015, S198616 — fixes CL returning unrelated federal WL clusters (e.g. Neal v. …)
    "2015 wl 2125291": {
        "canonical_name": "In re Cipro Cases I & II",
        "canonical_date": "2015-05-07",
        "canonical_year": "2015",
        "canonical_url": "https://law.justia.com/cases/california/supreme-court/2015/s198616.html",
    },
    # In re Aggrenox Antitrust Litig. (D.R.I.); TOA often carries wrong year vs WL token
    "2015 wl 1311352": {
        "canonical_name": "In re Aggrenox Antitrust Litigation",
        "canonical_date": "2015",
        "canonical_year": "2015",
        "canonical_url": "https://www.courtlistener.com/docket/4535884/in-re-aggrenox-antitrust-litigation/",
    },
    # MDL 2332 — no single slip; docket hub on CourtListener
    "2013 wl 4780496": {
        "canonical_name": "In re Lipitor Antitrust Litigation",
        "canonical_date": "2013",
        "canonical_year": "2013",
        "canonical_url": "https://www.courtlistener.com/docket/17279455/in-re-lipitor-antitrust-litigation/",
    },
}


KNOWN_FEDERAL_CITATIONS = {
    "426 u.s. 26": {
        "canonical_name": "Simon v. Eastern Kentucky Welfare Rights Organization",
        "canonical_date": "1976-06-01",
        "canonical_year": "1976",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/426/26/",
    },
    "524 u.s. 11": {
        "canonical_name": "Federal Election Commission v. Akins",
        "canonical_date": "1998-06-01",
        "canonical_year": "1998",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/524/11/",
    },
    "554 u.s. 269": {
        "canonical_name": "Sprint Communications Co. v. APCC Services, Inc.",
        "canonical_date": "2008-06-23",
        "canonical_year": "2008",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/554/269/",
    },
    "523 u.s. 83": {
        "canonical_name": "Steel Co. v. Citizens for a Better Environment",
        "canonical_date": "1998-01-12",
        "canonical_year": "1998",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/523/83/",
    },
    "6 wheat. 264": {
        "canonical_name": "Cohens v. Virginia",
        "canonical_date": "1821-03-03",
        "canonical_year": "1821",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/19/264/",
    },
    "455 u.s. 363": {
        "canonical_name": "Havens Realty Corp. v. Coleman",
        "canonical_date": "1982-02-24",
        "canonical_year": "1982",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/455/363/",
    },
    "490 u.s. 605": {
        "canonical_name": "ASARCO Inc. v. Kadish",
        "canonical_date": "1989-05-30",
        "canonical_year": "1989",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/490/605/",
    },
    "199 f.3d 263": {
        "canonical_name": "Washington v. CSC Credit Services, Inc.",
        "canonical_date": "2000-01-01",
        "canonical_year": "2000",
        "canonical_url": "https://law.justia.com/cases/federal/appellate-courts/F3/199/263/",
    },
    "578 u.s. 330": {
        "canonical_name": "Spokeo, Inc. v. Robins",
        "canonical_date": "2016-05-16",
        "canonical_year": "2016",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/578/330/",
    },
    "568 u.s. 398": {
        "canonical_name": "Clapper v. Amnesty Int'l USA",
        "canonical_date": "2013-02-26",
        "canonical_year": "2013",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/568/398/",
    },
    "555 u.s. 460": {
        "canonical_name": "Pleasant Grove City v. Summum",
        "canonical_date": "2009-02-25",
        "canonical_year": "2009",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/555/460/",
    },
    "591 u.s. 1": {
        "canonical_name": "Department of Homeland Security v. Regents of the University of California",
        "canonical_date": "2020-06-18",
        "canonical_year": "2020",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/591/1/",
    },
    "145 s. ct. 13": {
        "canonical_name": "A.A.R.P. v. Trump",
        "canonical_date": "2025-05-16",
        "canonical_year": "2025",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/605/24a1007/",
    },
    # Cert. grant order cite often mis-resolved by search (wrong merits case at same reporter page)
    "143 s. ct. 2429": {
        "canonical_name": "Loper Bright Enterprises v. Raimondo",
        "canonical_date": "2023-05-22",
        "canonical_year": "2023",
        "canonical_url": "https://www.supremecourt.gov/search.aspx?filename=docketfiles/html/public/22-451.html",
    },
    "603 u.s. 369": {
        "canonical_name": "Loper Bright Enterprises v. Raimondo",
        "canonical_date": "2024-06-28",
        "canonical_year": "2024",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/603/369/",
    },
    # CourtListener "No results" fallbacks - valid federal cases often missed by API
    "573 u.s. 149": {
        "canonical_name": "Susan B. Anthony List v. Driehaus",
        "canonical_date": "2014-06-16",
        "canonical_year": "2014",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/573/149/",
    },
    "964 f.3d 990": {
        "canonical_name": "Trichell v. Midland Credit Mgmt., Inc.",
        "canonical_date": "2020-07-06",
        "canonical_year": "2020",
        "canonical_url": "https://law.justia.com/cases/federal/appellate-courts/ca11/18-14144/18-14144-2020-07-06.html",
    },
    # CourtListener cluster miss / TOA OCR ("O'Flahaven"); opinion: https://www.courtlistener.com/opinion/2008316/federal-deposit-ins-v-oflahaven/
    "857 f. supp. 154": {
        "canonical_name": "Federal Deposit Insurance Corp. v. O'Flahaven",
        "canonical_date": "1994-03-31",
        "canonical_year": "1994",
        "canonical_url": "https://www.courtlistener.com/opinion/2008316/federal-deposit-ins-v-oflahaven/",
    },
    # NAAG briefs: reporter line can pick up adjacent case name (e.g. UFCW) — cite is Delta Dental
    "943 f. supp. 172": {
        "canonical_name": "United States v. Delta Dental of Rhode Island",
        "canonical_date": "1996-06-28",
        "canonical_year": "1996",
        "canonical_url": "https://www.courtlistener.com/opinion/2250934/united-states-v-delta-dental-of-rhode-island/",
    },
    # In re Cardizem CD (6th Cir. 2003); TOA/context often injects unrelated year (e.g. 1992)
    "332 f.3d 896": {
        "canonical_name": "In re Cardizem CD Antitrust Litigation",
        "canonical_date": "2003-07-31",
        "canonical_year": "2003",
        "canonical_url": "https://www.courtlistener.com/opinion/782340/in-re-cardizem-cd-antitrust-litigation-louisiana-wholesale-drug-co-v/",
        "force_override": True,
    },
    # 423 U.S. 150 — merits decision 1976; batch search sometimes returns wrong modern year
    "423 u.s. 150": {
        "canonical_name": "American Foreign Steamship Corp. v. Matise",
        "canonical_date": "1976-01-21",
        "canonical_year": "1976",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/423/150/",
    },
    # Parallel reporter for 2014 WL 6465235 (Teikoku / Lidoderm MDL order)
    "74 f. supp. 3d 1052": {
        "canonical_name": "United Food & Commercial Workers Local 1776 v. Teikoku Pharma USA, Inc.",
        "canonical_date": "2014-11-17",
        "canonical_year": "2014",
        "canonical_url": "https://www.courtlistener.com/opinion/7311104/united-food-commercial-workers-local-1776-v-teikoku-pharma-usa-inc/",
    },
    # NAAG antitrust briefs: duplicate rows / wrong TOA year; CL opinion is 2013 merits decision
    "133 s. ct. 2223": {
        "canonical_name": "Federal Trade Commission v. Actavis, Inc.",
        "canonical_date": "2013-06-17",
        "canonical_year": "2013",
        "canonical_url": "https://www.courtlistener.com/opinion/9240878/federal-trade-commission-v-actavis-inc/",
    },
    # Cert. denial order; same underlying court of appeals case as 604 F.3d 98 (2010)
    "131 s. ct. 1606": {
        "canonical_name": "Louisiana Wholesale Drug Co. v. Bayer AG",
        "canonical_date": "2011-03-07",
        "canonical_year": "2011",
        "canonical_url": "https://www.courtlistener.com/opinion/7343436/louisiana-wholesale-drug-co-v-bayer-ag/",
    },
    # Loestrin MDL D.R.I.; fixes Effexor/TOA neighbor bleed on extracted_case_name
    "45 f. supp. 3d 180": {
        "canonical_name": "In re Loestrin 24 FE Antitrust Litigation",
        "canonical_date": "2014-09-04",
        "canonical_year": "2014",
        "canonical_url": "https://www.courtlistener.com/opinion/8343787/in-re-loestrin-24-fe-antitrust-litigation/",
    },
    # Nexium MDL D. Mass.; align caption with common TOA "Nexium Antitrust Litig."
    "968 f. supp. 2d 367": {
        "canonical_name": "In re Nexium Antitrust Litigation",
        "canonical_date": "2013-09-11",
        "canonical_year": "2013",
        "canonical_url": "https://www.courtlistener.com/opinion/8727943/in-re-nexium/",
    },
}

# State citations that citation-lookup often misses. Key = normalized "vol reporter page" (lowercase).
# Senear v. Daily Journal American: https://www.courtlistener.com/opinion/1222849/senear-v-daily-journal-american/
KNOWN_STATE_CITATIONS = {
    "97 wash. 2d 148": {
        "canonical_name": "Senear v. Daily Journal American",
        "canonical_date": "1982",
        "canonical_year": "1982",
        "canonical_url": "https://www.courtlistener.com/opinion/1222849/senear-v-daily-journal-american/",
    },
    "97 wn.2d 148": {
        "canonical_name": "Senear v. Daily Journal American",
        "canonical_date": "1982",
        "canonical_year": "1982",
        "canonical_url": "https://www.courtlistener.com/opinion/1222849/senear-v-daily-journal-american/",
    },
    "641 p.2d 1180": {
        "canonical_name": "Senear v. Daily Journal American",
        "canonical_date": "1982",
        "canonical_year": "1982",
        "canonical_url": "https://www.courtlistener.com/opinion/1222849/senear-v-daily-journal-american/",
    },
}


def _normalize_state_citation_for_known_lookup(citation: str) -> str:
    """Normalize state citation for KNOWN_STATE_CITATIONS key (e.g. '97 Wash. 2d 148' -> '97 wash. 2d 148')."""
    if not citation:
        return ""
    s = re.sub(r"\s+", " ", citation.strip()).lower()
    s = re.sub(r"wash\.\s*2d", "wash. 2d", s, flags=re.IGNORECASE)
    s = re.sub(r"wn\.?\s*2d", "wn.2d", s, flags=re.IGNORECASE)
    s = re.sub(r"p\.\s*2d", "p.2d", s, flags=re.IGNORECASE)
    s = re.sub(r"p\.\s*3d", "p.3d", s, flags=re.IGNORECASE)
    return s.strip()


def _lookup_known_state(citation: str) -> Optional[Dict[str, Any]]:
    """Return KNOWN_STATE_CITATIONS entry for citation string, or None."""
    norm = _normalize_state_citation_for_known_lookup(citation or "")
    if not norm:
        return None
    # Direct key match
    if norm in KNOWN_STATE_CITATIONS:
        return KNOWN_STATE_CITATIONS[norm]
    # Extract vol-reporter-page core (e.g. "97 wash. 2d 148" or "641 p.2d 1180")
    base_m = (
        re.match(r"^(\d+\s+wash\.\s*2d\s+\d+)", norm)
        or re.match(r"^(\d+\s+wn\.?2d\s+\d+)", norm)
        or re.match(r"^(\d+\s+p\.?2d\s+\d+)", norm)
        or re.match(r"^(\d+\s+p\.?3d\s+\d+)", norm)
    )
    if base_m:
        lookup = base_m.group(1).strip().lower()
        lookup = re.sub(r"\s+", " ", lookup)
        if lookup in KNOWN_STATE_CITATIONS:
            return KNOWN_STATE_CITATIONS[lookup]
    # Embedded: "Something, 97 Wash. 2d 148 (1982)" -> extract core
    for pat in [
        r"(\d+\s+wash\.\s*2d\s+\d+)",
        r"(\d+\s+wn\.?2d\s+\d+)",
        r"(\d+\s+p\.?2d\s+\d+)",
        r"(\d+\s+p\.?3d\s+\d+)",
    ]:
        m = re.search(pat, norm)
        if m:
            k = m.group(1).strip().lower()
            k = re.sub(r"\s+", " ", k)
            if k in KNOWN_STATE_CITATIONS:
                return KNOWN_STATE_CITATIONS[k]
    return None


# Slip opinions (e.g. 588 U.S. ___): key = "volume year", value = list of { canonical_name, canonical_date, canonical_url }
# Used when extracted_case_name matches so we resolve to the correct case (e.g. American Legion, not Loper Bright for 588 2019)
KNOWN_SLIP_CITATIONS = {
    "588 2019": [
        {
            "canonical_name": "American Legion v. American Humanist Ass'n",
            "canonical_date": "2019-06-20",
            "canonical_url": "https://supreme.justia.com/cases/federal/us/588/17-1717/",
            "canonical_url_alt": "https://www.supremecourt.gov/opinions/18pdf/17-1717_4f14.pdf",
        },
    ],
    "592 2021": [
        {
            "canonical_name": "Uzuegbunam v. Preczewski",
            "canonical_date": "2021-03-08",
            "canonical_url": "https://supreme.justia.com/cases/federal/us/592/19-968/",
        },
    ],
    "593 2021": [
        {
            "canonical_name": "Niz-Chavez v. Garland",
            "canonical_date": "2021-04-29",
            "canonical_url": "https://supreme.justia.com/cases/federal/us/593/155/",
        },
    ],
}


def _lookup_known_federal(cit_str: str) -> Optional[Dict[str, Any]]:
    """Return KNOWN_FEDERAL_CITATIONS entry for citation string, or None. Shared by dict and object applicators."""
    import re as _re
    raw = cit_str or ""
    wl_key = _wl_citation_key(raw)
    if wl_key and wl_key in KNOWN_WL_CITATIONS:
        row = cast(Dict[str, Any], dict(KNOWN_WL_CITATIONS[wl_key]))
        row["force_override"] = True
        row["verification_source"] = "known_wl"
        return row

    norm = _normalize_citation_for_known_lookup(raw)
    if not norm:
        return None
    lookup = norm
    if lookup not in KNOWN_FEDERAL_CITATIONS:
        base_m = (
            _re.match(r"^(\d+\s+u\.s\.\s*\d+)", norm)
            or _re.match(r"^(\d+\s+wheat\.\s*\d+)", norm)
            or _re.match(r"^(\d+\s+f\.3d\s*\d+)", norm)
            or _re.match(r"^(\d+\s+f\.2d\s*\d+)", norm)
            or _re.match(r"^(\d+\s+f\.4th\s*\d+)", norm)
            or _re.match(r"^(\d+\s+f\.\s*supp\.\s*2d\s+\d+)", norm)
            or _re.match(r"^(\d+\s+f\.\s*supp\.\s*3d\s+\d+)", norm)
            or _re.match(r"^(\d+\s+f\.\s*supp\.\s+\d+)(?!d\b)", norm)
        )
        if base_m:
            lookup = base_m.group(1).strip().lower()
    if lookup in KNOWN_FEDERAL_CITATIONS:
        return KNOWN_FEDERAL_CITATIONS.get(lookup)

    # Fallback: citation strings can include lead case-name text/pincites, e.g.
    # "DHS v. Regents ..., 591 U.S. 1 (2020)". Extract embedded core cite.
    embedded_patterns = [
        r"(\d+\s+u\.s\.\s*\d+)",
        r"(\d+\s+s\.\s*ct\.\s*\d+)",
        r"(\d+\s+wheat\.\s*\d+)",
        r"(\d+\s+f\.3d\s*\d+)",
        r"(\d+\s+f\.2d\s*\d+)",
        r"(\d+\s+f\.4th\s*\d+)",
        r"(\d+\s+f\.\s*supp\.\s*2d\s+\d+)",
        r"(\d+\s+f\.\s*supp\.\s*3d\s+\d+)",
        r"(\d+\s+f\.\s*supp\.\s+\d+)(?!d\b)",
    ]
    for pat in embedded_patterns:
        m = _re.search(pat, norm)
        if not m:
            continue
        embedded_lookup = m.group(1).strip().lower()
        if embedded_lookup in KNOWN_FEDERAL_CITATIONS:
            return KNOWN_FEDERAL_CITATIONS.get(embedded_lookup)
    return None


def _lookup_known_slip(
    citation: str, extracted_case_name: Optional[str], extracted_date: Optional[str]
) -> Optional[Dict[str, Any]]:
    """If citation is a U.S. slip (e.g. 588 U.S. ___) and we have a known slip for that volume+year matching extracted name, return it."""
    from src.verification.utils import calculate_case_name_overlap

    if not citation or not extracted_case_name or (extracted_case_name or "").strip() in ("", "N/A"):
        return None
    m = re.search(r"(\d+)\s+U\.?\s*S\.?\s+[_\u2013\u2014]+", citation, re.IGNORECASE)
    if not m:
        return None
    volume = m.group(1)
    year = None
    if extracted_date:
        ym = re.search(r"(19|20)\d{2}", str(extracted_date))
        if ym:
            year = int(ym.group(0))
    if not year:
        return None
    key = f"{volume} {year}"
    entries = KNOWN_SLIP_CITATIONS.get(key)
    if not entries:
        return None
    for entry in entries:
        canonical_name = entry.get("canonical_name") or ""
        if not canonical_name:
            continue
        overlap = calculate_case_name_overlap(extracted_case_name, canonical_name)
        if overlap >= 0.4:
            return entry
    return None

"""
Parse the U.S. Department of Justice OSG Supreme Court briefs listing table.

Listing page: https://www.justice.gov/osg/supreme-court-briefs

Used by ``scripts/fetch_osg_supreme_court_brief_index.py`` and corpus schema tests.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag

LIST_URL = "https://www.justice.gov/osg/supreme-court-briefs"
DEFAULT_FETCH_UA = (
    "Mozilla/5.0 (compatible; CaseStrainer/1.0; +https://github.com/) "
    "CaseStrainer regression corpus fetch"
)


def _abs_url(base: str, href: str) -> str:
    return urljoin(base + "/", href.lstrip("/"))


def parse_brief_table_rows(html: str, list_url: str = LIST_URL) -> list[dict[str, Any]]:
    """Parse OSG supreme-court-briefs listing HTML into row dicts."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not isinstance(table, Tag):
        return []
    base = f"{urlparse(list_url).scheme}://{urlparse(list_url).netloc}"
    rows_out: list[dict[str, Any]] = []
    for tr in table.find_all("tr")[1:]:
        if not isinstance(tr, Tag):
            continue
        tds = tr.find_all("td")
        if len(tds) < 7:
            continue
        term = tds[0].get_text(strip=True)
        docket = tds[1].get_text(strip=True)
        cap_cell = tds[2]
        if not isinstance(cap_cell, Tag):
            continue
        caption = cap_cell.get_text(strip=True)
        brief_url = None
        brief_a = cap_cell.find("a", href=True)
        if isinstance(brief_a, Tag):
            bh = brief_a.get("href")
            if isinstance(bh, str):
                brief_url = _abs_url(base, bh)
        file_cell = tds[3]
        if not isinstance(file_cell, Tag):
            continue
        pdf_url = None
        pdf_a = file_cell.find("a", href=True)
        if isinstance(pdf_a, Tag):
            pdf_href = pdf_a.get("href")
            if isinstance(pdf_href, str):
                pdf_url = _abs_url(base, pdf_href)
        brief_type = tds[4].get_text(strip=True)
        subject = tds[5].get_text(strip=True)
        filing_date = tds[6].get_text(strip=True)
        rows_out.append(
            {
                "term": term,
                "docket": docket,
                "caption": caption,
                "brief_url": brief_url,
                "pdf_url": pdf_url,
                "brief_type": brief_type,
                "subject": subject,
                "filing_date": filing_date,
            }
        )
    return rows_out


def media_id_from_pdf_url(pdf_url: str | None) -> str | None:
    if not pdf_url:
        return None
    m = re.search(r"/media/(\d+)/", pdf_url)
    return m.group(1) if m else None

"""
Tests for DOJ OSG Supreme Court brief listing metadata (corpus index).

Live fetches against justice.gov are opt-in (see test marked integration).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest

from src.utils.justice_osg_brief_listing import (
    DEFAULT_FETCH_UA,
    LIST_URL,
    media_id_from_pdf_url,
    parse_brief_table_rows,
)

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "justice_osg_supreme_court_briefs_sample.json"

_ENTRY_KEYS = frozenset(
    {
        "term",
        "docket",
        "caption",
        "brief_url",
        "pdf_url",
        "brief_type",
        "subject",
        "filing_date",
    }
)


def test_justice_osg_sample_fixture_schema():
    data = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    assert data.get("source") == LIST_URL
    assert data.get("entry_count") == len(data.get("entries", []))
    for row in data["entries"]:
        assert set(row.keys()) >= _ENTRY_KEYS
        assert row["docket"]
        assert row["caption"]
        if row.get("pdf_url"):
            assert str(row["pdf_url"]).startswith("https://www.justice.gov/")
            assert media_id_from_pdf_url(row["pdf_url"])


def test_parse_brief_table_rows_minimal_html():
    html = """
    <html><body><table>
    <tr><th>Term</th><th>Docket</th><th>Caption</th><th>File</th><th>Type</th><th>Subject</th><th>Date</th></tr>
    <tr>
      <td>2025 Term</td>
      <td>99-1</td>
      <td><a href="/osg/brief/foo-v-bar">Foo v. Bar</a></td>
      <td><a href="/osg/media/12345/dl?inline">PDF</a></td>
      <td>Merits Stage Brief</td>
      <td>Tax</td>
      <td>Monday, January 1, 2020</td>
    </tr>
    <tr>
      <td>2025 Term</td>
      <td>99-2</td>
      <td><a href="/osg/brief/no-pdf">No PDF Row</a></td>
      <td></td>
      <td>Reply</td>
      <td>Other</td>
      <td>Tuesday, January 2, 2020</td>
    </tr>
    </table></body></html>
    """
    rows = parse_brief_table_rows(html)
    assert len(rows) == 2
    assert rows[0]["docket"] == "99-1"
    assert rows[0]["caption"] == "Foo v. Bar"
    assert rows[0]["pdf_url"] == "https://www.justice.gov/osg/media/12345/dl?inline"
    assert media_id_from_pdf_url(rows[0]["pdf_url"]) == "12345"
    assert rows[1]["pdf_url"] is None


@pytest.mark.integration
def test_justice_osg_live_listing_page_matches_fixture_shape():
    """Opt-in network check against https://www.justice.gov/osg/supreme-court-briefs"""
    if os.environ.get("CASSTRAINER_JUSTICE_GOV_LIVE", "").strip() not in ("1", "true", "yes"):
        pytest.skip("Set CASSTRAINER_JUSTICE_GOV_LIVE=1 to run live justice.gov fetch test")

    headers = {"User-Agent": DEFAULT_FETCH_UA}
    with httpx.Client(headers=headers, timeout=60.0, follow_redirects=True) as client:
        r = client.get(LIST_URL)
        r.raise_for_status()
        rows = parse_brief_table_rows(r.text)

    assert len(rows) >= 20
    sample = json.loads(_FIXTURE.read_text(encoding="utf-8"))["entries"][0]
    dockets = {x["docket"] for x in rows}
    assert sample["docket"] in dockets

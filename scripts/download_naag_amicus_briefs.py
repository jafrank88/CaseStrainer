#!/usr/bin/env python3
"""
Download NAAG multistate AG antitrust amicus PDFs into the repo (gitignored by default).

Default output: ``<repo>/downloaded_briefs/naag_amicus/`` (parent ``downloaded_briefs/`` is in ``.gitignore``).

Usage::

    pip install requests
    python scripts/download_naag_amicus_briefs.py
    python scripts/download_naag_amicus_briefs.py --output-dir D:/briefs/naag

Smoke the corpus after download::

    python scripts/smoke_naag_amicus_briefs.py

CourtListener verification + canonical checks (subset; requires ``COURTLISTENER_API_KEY``)::

    python scripts/verify_naag_subset.py

Optional pytest (opt-in; see ``tests/test_naag_amicus_optional.py``)::

    set CASSTRAINER_NAAG_AMICUS_TESTS=1
    python -m pytest tests/test_naag_amicus_optional.py -q --no-cov -o addopts=

Optional verified goldens (slow; see ``tests/test_naag_verification_optional.py``)::

    set CASSTRAINER_NAAG_VERIFY_TESTS=1
    python -m pytest tests/test_naag_verification_optional.py -q --no-cov -o addopts=
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "downloaded_briefs" / "naag_amicus"

# 25 multistate AG amicus briefs from NAAG (public filings). URLs were checked against
# https://www.naag.org/issues/antitrust/attorney-general-amicus-briefs/ and the
# amicus-brief-archive; a few entries use substituted briefs where the original PDF was removed.
BRIEFS: list[dict[str, str]] = [
    {
        "id": "01",
        "case": "Tri-City Valleycats v. Office of the Commissioner (S.Ct. 2023)",
        "states_signing": "CT, AZ, CO, DC, IN, KS, LA, MA, MN, MT, NJ, NM, NY, PA, TN, VT, VA, WV (18 states)",
        "url": "https://www.naag.org/wp-content/uploads/2023/10/10-23-23-Tri-City-Valleycats-v.-Office-of-the-Commissioner.pdf",
        "filename": "01_Tri-City-Valleycats-v-Commissioner_2023.pdf",
    },
    {
        "id": "02",
        "case": "Robinson v. Jackson-Hewitt (D.N.J. 2023)",
        "states_signing": "NJ, AZ, CO, CT, DE, HI, IL, ME, MD, MA, MI, MN, NV, NY, NC, OR, PA, RI, DC (19 states)",
        "url": "https://www.naag.org/wp-content/uploads/2023/10/10-23-2023-Robinson-v.-Jackson-Hewitt-NJ-Amicus-Brief.pdf",
        "filename": "02_Robinson-v-Jackson-Hewitt_2023.pdf",
    },
    {
        "id": "03",
        "case": "Deslandes v. McDonald's USA (7th Cir. 2022)",
        "states_signing": "IL, CA, CO, CT, DE, DC, HI, ID, MD, MA, MN, NE, NV, NJ, NM, NY, NC, OR, PA, RI, WA (21 states)",
        "url": "https://www.naag.org/wp-content/uploads/2023/01/IL-et-al.-Amicus-in-Deslandes-v.-McDonalds.pdf",
        "filename": "03_Deslandes-v-McDonalds_2022.pdf",
    },
    {
        "id": "04",
        "case": "FTC v. Meta Platforms (N.D. Cal. 2022)",
        "states_signing": "NY, CA, CO, CT, DE, DC, HI, ID, IL, IA, ME, MD, MA, MN, NV, NJ, NM, NC, OR, PA, RI, UT, WA, Guam (23 states)",
        "url": "https://www.naag.org/wp-content/uploads/2022/11/FTC-v.-Meta-Platforms-Amicus-Brief-by-23-states.pdf",
        "filename": "04_FTC-v-Meta-Platforms_2022.pdf",
    },
    {
        "id": "05",
        "case": "FTC v. Hackensack Meridian Health (3rd Cir. 2021)",
        "states_signing": "PA, CA, CO, CT, DE, ID, IL, IN, MD, MA, MI, MN, NE, NV, NH, NM, NY, NC, ND, OR, RI, VA, WA, WI, DC, Guam (25+ states)",
        "url": "https://www.naag.org/wp-content/uploads/2021/11/2021.11.05-Filed-States-Amicus-Brief-FTC-v.-Hackensack-Meridian-Health-and-Englewood-Healthcare-Foundation.pdf",
        "filename": "05_FTC-v-Hackensack-Meridian_2021.pdf",
    },
    {
        "id": "06",
        "case": "Impax Laboratories v. FTC (5th Cir. 2019)",
        "states_signing": "MS, WA, AK, CA, CO, CT, DE, DC, HI, ID, IL, IA, ME, MD, MA, MN, MT, NE, NM, NC, OR, PA, VA, WI (24 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/States-Amicus-Brief-12-16-19-Impax-v-FTC.pdf",
        "filename": "06_Impax-v-FTC_2019.pdf",
    },
    {
        "id": "07",
        "case": "Chamber of Commerce v. City of Seattle (9th Cir. 2018)",
        "states_signing": "NY, HI, IL, IA, ME, MD, MA, MN, OR, PA, RI, VT, DC (13 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/US-Chamber-of-Commerce-v-Seattle-amicus-brief-14-states.pdf",
        "filename": "07_Chamber-of-Commerce-v-Seattle_2018.pdf",
    },
    {
        "id": "08",
        "case": "Ohio v. American Express (Supreme Court 2018)",
        "states_signing": "OH, TX, ID, and 14 additional states",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/20171214-State-of-Ohio-v-Amex-Amicus-204120124_16-14541.pdf",
        "filename": "08_Ohio-v-AmEx_2018.pdf",
    },
    {
        "id": "09",
        "case": "FTC & Pennsylvania v. Penn State Hershey Medical (3rd Cir. 2017)",
        "states_signing": "WA, DE, IA, ID, MN, ND, UT, LA, NM, IN (10 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/12.18.17HersheyPinnacleStatesAmicus.pdf",
        "filename": "09_FTC-v-PennState-Hershey_2017.pdf",
    },
    {
        "id": "10",
        "case": "City of Providence v. Warner Chilcott (1st Cir. 2015)",
        "states_signing": "ME, CA, AK, CO, CT, DE, DC, HI, ID, IL, IA, KS, KY, LA, MD, MA, MI, MN, MS, NE, NH, NM, OR, RI, TN, TX, UT, VT, WA (29 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/Loestrin-States-Amicus-Brief-final.pdf",
        "filename": "10_City-of-Providence-v-WarnerChilcott_2015.pdf",
    },
    {
        "id": "11",
        "case": "McWane Inc. v. FTC (11th Cir. 2014)",
        "states_signing": "NY, AZ, CT, HI, ID, IN, IA, KY, MD, MS, NV, NM, Puerto Rico (13 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/2014.09.05.mcwane.amici-states-brief.final-ecf.pdf",
        "filename": "11_McWane-v-FTC_2014.pdf",
    },
    {
        "id": "12",
        "case": "St. Luke's Health Care System v. FTC (9th Cir. 2014)",
        "states_signing": "CA, WA, PA, CT, DE, IL, IA, KY, ME, MD, MS, MT, NV, NM, OR, TN (16 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/St-Lukes-Brief-of-Amicus-Curiae.pdf",
        "filename": "12_St-Lukes-v-FTC_2014.pdf",
    },
    {
        "id": "13",
        "case": "North Carolina Board of Dental Examiners v. FTC — Merits (S.Ct. 2014)",
        "states_signing": "WV, AL, AZ, AR, CO, CT, DE, FL, HI, ID, IN, KS, KY, MD, MI, NE, NC, OH, OR, SC, TN, UT, VA (23 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/WV-Amicus-in-NC-Dental-merits-brief.pdf",
        "filename": "13_NC-Dental-v-FTC-Merits_2014.pdf",
    },
    {
        "id": "14",
        "case": "King Drug Co. v. SmithKline Beecham (3rd Cir. 2014)",
        "states_signing": "MS, AK, AR, AZ, CA, CT, DE, HI, ID, IL, IN, KY, MA, MD, MI, MN, NH, NM, NY, NV, OH, PA, RI, TN, TX, UT, VT, WA (28 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/King-Drug.pdf",
        "filename": "14_King-Drug-v-SmithKline_2014.pdf",
    },
    {
        "id": "15",
        "case": "North Carolina Board of Dental Examiners v. FTC — Cert (S.Ct. 2013)",
        "states_signing": "WV, AL, CO, DE, FL, KS, MD, NC, OH, SC (10 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/WV-Amicus-Brief-re-NC-Dental-FINAL-FINAL.pdf",
        "filename": "15_NC-Dental-v-FTC-Cert_2013.pdf",
    },
    {
        "id": "16",
        "case": "Mississippi ex rel. Hood v. AU Optronics (S.Ct. 2013)",
        "states_signing": "IL and 45 other states (46 states total)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/12-1036-tsac-State-of-Illinois-and-45-Other-States.pdf",
        "filename": "16_Mississippi-v-AU-Optronics_2013.pdf",
    },
    {
        "id": "17",
        "case": "FTC v. Watson Pharmaceuticals (S.Ct. 2013)",
        "states_signing": "NY, AZ, AR, CA, CO, CT, DE, HI, ID, IL, IA, KY, LA, ME, MD, MA, MI, MN, MS, MO, NV, NH, NM, NC, ND, OH, OR, PA, RI, SC, SD, TN, UT, VT, WA, WY, DC, Puerto Rico (38 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/FTC-v-Watson-states-amicus-merits-brief-FINAL-2.pdf",
        "filename": "17_FTC-v-Watson-Pharmaceuticals_2013.pdf",
    },
    {
        "id": "18",
        "case": "American Express v. Italian Colors Restaurant (S.Ct. 2012)",
        "states_signing": "CA, AK, AZ, CT, DE, HI, ID, IL, IA, KY, ME, MD, MA, MN, MS, MT, NE, NV, NH, NM, NY, NC, ND, OR, PA, RI, SD, VT, WA, WV, DC (31 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/Italian-Colors-FINAL-brief.pdf",
        "filename": "18_AmEx-v-Italian-Colors_2012.pdf",
    },
    # Original FTC v. Actavis cert PDF no longer on NAAG; substituted multistate SCOTUS brief (same era).
    {
        "id": "19",
        "case": "FTC v. Phoebe Putney Health System (S.Ct. 2012)",
        "states_signing": "IL, AZ, CA, CO, CT, DE, HI, ID, MD, MI, MN, NV, NH, NM, NY, NC, OR, PA, TN, WV (multistate)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/Phoebe-Putney-amicus-by-IL-8-25-2012.pdf",
        "filename": "19_FTC-v-Phoebe-Putney_2012.pdf",
    },
    {
        "id": "20",
        "case": "Pepper v. Apple Inc. (9th Cir. 2011)",
        "states_signing": "NY, CA, AZ, CT, IL, IA, ME, MD, MA, MI, MN, NV, NH, NM, NC, OR, RI, VT, WA, WI, DC (21 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/Amici-Texas-Iowa-and-29-Other-States-ISO-Respondents-Apple-v.-Pepper.pdf",
        "filename": "20_Pepper-v-Apple_2011.pdf",
    },
    # Conwood PDF removed from NAAG; substituted multistate 2010 amicus from archive.
    {
        "id": "21",
        "case": "Oklahoma ex rel. Edmondson v. BP America (10th Cir. 2010)",
        "states_signing": "KS, OH, and 36 other states (multistate)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/BP-Oklahoma-Amicus-Brief-as-filed-092710_1-2.pdf",
        "filename": "21_OK-v-BP-America_2010.pdf",
    },
    # Leegin 5th Cir. remand PDF removed; substituted K-Dur 3d Cir. multistate brief.
    {
        "id": "22",
        "case": "In re K-Dur Antitrust Litigation (3d Cir. 2011)",
        "states_signing": "OH, AK, AZ, AR, ID, IL, IA, KS, LA, ME, MD, MA, MN, MS, NV, NM, SC, TN, UT, VT, WA, WY (multistate)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/K-Dur-Third-Circuit-Amicus-Final.pdf",
        "filename": "22_K-Dur-3d-Cir_2011.pdf",
    },
    {
        "id": "23",
        "case": "Leegin Creative Leather Products v. PSKS (S.Ct. 2007)",
        "states_signing": "NY, AK, AZ, CA, CT, DE, HI, ID, IL, IA, KS, ME, MD, MA, MI, MN, MS, MT, NE, NV, NH, NM, NC, ND, OH, OR, PA, RI, SD, TN, UT, VT, WA, WI, WY, DC (36 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/Leegin-States.pdf",
        "filename": "23_Leegin-v-PSKS-SCOTUS_2007.pdf",
    },
    # Illinois Tool Works PDF not found on NAAG; substituted DDAVP multistate 2d Cir. brief.
    {
        "id": "24",
        "case": "In re DDAVP Direct Purchaser Antitrust Litigation (2d Cir. 2007)",
        "states_signing": "NY and 41 other states (multistate)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/DDAVP-States-amicus.pdf",
        "filename": "24_DDAVP-2d-Cir_2007.pdf",
    },
    {
        "id": "25",
        "case": "Verizon Communications v. Law Offices of Curtis Trinko (S.Ct. 2004)",
        "states_signing": "NY, AK, AZ, CA, CO, CT, DE, HI, ID, IL, IA, KS, ME, MD, MA, MI, MN, MS, MT, NE, NV, NH, NM, NC, ND, OR, PA, RI, SD, TN, UT, VT, WA, WI, WY, DC (36 states)",
        "url": "https://www.naag.org/wp-content/uploads/2020/11/new-york-trinko.pdf",
        "filename": "25_Verizon-v-Trinko_2004.pdf",
    },
]


def download_briefs(output_dir: Path, *, sleep_s: float = 1.0) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Saving briefs to: {output_dir.resolve()}\n")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "CaseStrainer/1.0 (+https://github.com/jafrank88/CaseStrainer; "
                "NAAG amicus test corpus download)"
            )
        }
    )

    results: dict[str, list] = {"success": [], "failed": []}

    for brief in BRIEFS:
        dest = output_dir / brief["filename"]

        if dest.is_file() and dest.stat().st_size > 10_000:
            print(f"[SKIP] {brief['id']}. Already exists: {brief['filename']}")
            results["success"].append(brief)
            continue

        case_short = brief["case"][:70]
        print(f"[{brief['id']}/25] Downloading: {case_short}")
        print(f"       States: {brief['states_signing']}")

        try:
            resp = session.get(brief["url"], timeout=60, stream=True)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if "pdf" not in content_type.lower() and "octet" not in content_type.lower():
                print(f"       [WARN] Unexpected content-type: {content_type}")

            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            size_kb = dest.stat().st_size / 1024
            print(f"       [OK] Saved ({size_kb:.0f} KB)\n")
            results["success"].append(brief)

        except requests.exceptions.RequestException as e:
            print(f"       [FAIL] {e}\n")
            results["failed"].append({**brief, "error": str(e)})

        time.sleep(sleep_s)

    print("=" * 60)
    print(f"COMPLETE: {len(results['success'])}/25 briefs ok (present or downloaded)")

    if results["failed"]:
        print(f"\n[WARN] {len(results['failed'])} briefs failed:")
        for b in results["failed"]:
            print(f"  - {b['id']}. {b['case']}")
            print(f"    URL: {b['url']}")
            print(f"    Error: {b['error']}")
        print(
            "\nFor failed briefs, try the URL in a browser; NAAG may have moved the file."
        )
        return 1

    print("\n[OK] All 25 briefs are available under the output directory.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Download NAAG multistate amicus PDFs for local testing.")
    p.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Directory for PDFs (default: {DEFAULT_OUTPUT})",
    )
    p.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        help="Seconds between HTTP requests (default: 1)",
    )
    args = p.parse_args(argv)
    return download_briefs(args.output_dir.resolve(), sleep_s=args.sleep)


if __name__ == "__main__":
    raise SystemExit(main())

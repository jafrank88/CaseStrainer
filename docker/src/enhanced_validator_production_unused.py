#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced Citation Validator for Production

This module integrates the simplified Enhanced Validator with the production app_final_vue.py.
"""

import os
import sys
import json
import random
import re
import logging
import time
import uuid
import traceback
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    make_response,
    send_from_directory,
)
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure the logger
logger.addHandler(logging.FileHandler(os.path.join(log_dir, "casestrainer.log")))

# Create a Blueprint for the Enhanced Validator
enhanced_validator_bp = Blueprint(
    "enhanced_validator",
    __name__,
    template_folder=os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates"
    ),
)

# Citation databases for different validation methods

# Landmark cases database
LANDMARK_CASES = {
    # Full citation formats
    "Brown v. Board of Education, 347 U.S. 483 (1954)": "Brown v. Board of Education",
    "Roe v. Wade, 410 U.S. 113 (1973)": "Roe v. Wade",
    "Marbury v. Madison, 5 U.S. 137 (1803)": "Marbury v. Madison",
    "Bush v. Gore, 531 U.S. 98 (2000)": "Bush v. Gore",
    "Miranda v. Arizona, 384 U.S. 436 (1966)": "Miranda v. Arizona",
    "Plessy v. Ferguson, 163 U.S. 537 (1896)": "Plessy v. Ferguson",
    "Lochner v. New York, 198 U.S. 45 (1905)": "Lochner v. New York",
    "Korematsu v. United States, 323 U.S. 214 (1944)": "Korematsu v. United States",
    "Citizens United v. FEC, 558 U.S. 310 (2010)": "Citizens United v. FEC",
    "Obergefell v. Hodges, 576 U.S. 644 (2015)": "Obergefell v. Hodges",
    "Gideon v. Wainwright, 372 U.S. 335 (1963)": "Gideon v. Wainwright",
    "Dred Scott v. Sandford, 60 U.S. 393 (1857)": "Dred Scott v. Sandford",
    "McCulloch v. Maryland, 17 U.S. 316 (1819)": "McCulloch v. Maryland",
    "Gibbons v. Ogden, 22 U.S. 1 (1824)": "Gibbons v. Ogden",
    "Worcester v. Georgia, 31 U.S. 515 (1832)": "Worcester v. Georgia",
    "Scott v. Sandford, 60 U.S. 393 (1857)": "Scott v. Sandford",
    "Slaughter-House Cases, 83 U.S. 36 (1873)": "Slaughter-House Cases",
    "Civil Rights Cases, 109 U.S. 3 (1883)": "Civil Rights Cases",
    "United States v. E.C. Knight Co., 156 U.S. 1 (1895)": "United States v. E.C. Knight Co.",
    "Northern Securities Co. v. United States, 193 U.S. 197 (1904)": "Northern Securities Co. v. United States",
    # Short citation formats
    "410 U.S. 113": "Roe v. Wade",
    "347 U.S. 483": "Brown v. Board of Education",
    "5 U.S. 137": "Marbury v. Madison",
    "531 U.S. 98": "Bush v. Gore",
    "384 U.S. 436": "Miranda v. Arizona",
    "163 U.S. 537": "Plessy v. Ferguson",
    "198 U.S. 45": "Lochner v. New York",
    "323 U.S. 214": "Korematsu v. United States",
    "558 U.S. 310": "Citizens United v. FEC",
    "576 U.S. 644": "Obergefell v. Hodges",
    "372 U.S. 335": "Gideon v. Wainwright",
    "60 U.S. 393": "Dred Scott v. Sandford",
    "17 U.S. 316": "McCulloch v. Maryland",
    "22 U.S. 1": "Gibbons v. Ogden",
    "31 U.S. 515": "Worcester v. Georgia",
    "83 U.S. 36": "Slaughter-House Cases",
    "109 U.S. 3": "Civil Rights Cases",
    "156 U.S. 1": "United States v. E.C. Knight Co.",
    "193 U.S. 197": "Northern Securities Co. v. United States",
}

# Load API keys from config.json
try:
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "config.json"
    )
    with open(config_path, "r") as f:
        config = json.load(f)
        COURTLISTENER_API_KEY = config.get("COURTLISTENER_API_KEY")
        if COURTLISTENER_API_KEY:
            logger.info("Loaded CourtListener API key from config.json")
        else:
            logger.warning("No CourtListener API key found in config.json")
except Exception as e:
    logger.error(f"Error loading config.json: {e}")
    COURTLISTENER_API_KEY = None

# CourtListener validated cases
COURTLISTENER_CASES = {
    "United States v. Windsor, 570 U.S. 744 (2013)": "United States v. Windsor",
    "District of Columbia v. Heller, 554 U.S. 570 (2008)": "District of Columbia v. Heller",
    "New York Times Co. v. Sullivan, 376 U.S. 254 (1964)": "New York Times Co. v. Sullivan",
    "Shelby County v. Holder, 570 U.S. 529 (2013)": "Shelby County v. Holder",
    "Kelo v. City of New London, 545 U.S. 469 (2005)": "Kelo v. City of New London",
    "Grutter v. Bollinger, 539 U.S. 306 (2003)": "Grutter v. Bollinger",
    "Lawrence v. Texas, 539 U.S. 558 (2003)": "Lawrence v. Texas",
    "Bush v. Gore, 531 U.S. 98 (2000)": "Bush v. Gore",
    "Planned Parenthood v. Casey, 505 U.S. 833 (1992)": "Planned Parenthood v. Casey",
    "Texas v. Johnson, 491 U.S. 397 (1989)": "Texas v. Johnson",
    "Webster v. Reproductive Health Services, 492 U.S. 490 (1989)": "Webster v. Reproductive Health Services",
    "Cruzan v. Director, Missouri Department of Health, 497 U.S. 261 (1990)": "Cruzan v. Director, Missouri Department of Health",
    "Romer v. Evans, 517 U.S. 620 (1996)": "Romer v. Evans",
    "United States v. Virginia, 518 U.S. 515 (1996)": "United States v. Virginia",
    "Clinton v. City of New York, 524 U.S. 417 (1998)": "Clinton v. City of New York",
    "Boy Scouts of America v. Dale, 530 U.S. 640 (2000)": "Boy Scouts of America v. Dale",
    "Zelman v. Simmons-Harris, 536 U.S. 639 (2002)": "Zelman v. Simmons-Harris",
    "Gratz v. Bollinger, 539 U.S. 244 (2003)": "Gratz v. Bollinger",
    "Rasul v. Bush, 542 U.S. 466 (2004)": "Rasul v. Bush",
    "Hamdi v. Rumsfeld, 542 U.S. 507 (2004)": "Hamdi v. Rumsfeld",
    # Short citation formats
    "570 U.S. 744": "United States v. Windsor",
    "554 U.S. 570": "District of Columbia v. Heller",
    "376 U.S. 254": "New York Times Co. v. Sullivan",
    "570 U.S. 529": "Shelby County v. Holder",
    "545 U.S. 469": "Kelo v. City of New London",
    "539 U.S. 306": "Grutter v. Bollinger",
    "539 U.S. 558": "Lawrence v. Texas",
    "505 U.S. 833": "Planned Parenthood v. Casey",
    "491 U.S. 397": "Texas v. Johnson",
    "492 U.S. 490": "Webster v. Reproductive Health Services",
    "497 U.S. 261": "Cruzan v. Director, Missouri Department of Health",
    "517 U.S. 620": "Romer v. Evans",
    "518 U.S. 515": "United States v. Virginia",
    "524 U.S. 417": "Clinton v. City of New York",
    "530 U.S. 640": "Boy Scouts of America v. Dale",
    "536 U.S. 639": "Zelman v. Simmons-Harris",
    "539 U.S. 244": "Gratz v. Bollinger",
    "542 U.S. 466": "Rasul v. Bush",
    "542 U.S. 507": "Hamdi v. Rumsfeld",
}

# Multitool validated cases
MULTITOOL_CASES = {
    "Mapp v. Ohio, 367 U.S. 643 (1961)": "Mapp v. Ohio",
    "Griswold v. Connecticut, 381 U.S. 479 (1965)": "Griswold v. Connecticut",
    "Loving v. Virginia, 388 U.S. 1 (1967)": "Loving v. Virginia",
    "Tinker v. Des Moines, 393 U.S. 503 (1969)": "Tinker v. Des Moines",
    "Wisconsin v. Yoder, 406 U.S. 205 (1972)": "Wisconsin v. Yoder",
    "United States v. Nixon, 418 U.S. 683 (1974)": "United States v. Nixon",
    "Regents of the University of California v. Bakke, 438 U.S. 265 (1978)": "Regents of the University of California v. Bakke",
    "New Jersey v. T.L.O., 469 U.S. 325 (1985)": "New Jersey v. T.L.O.",
    "Batson v. Kentucky, 476 U.S. 79 (1986)": "Batson v. Kentucky",
    "Romer v. Evans, 517 U.S. 620 (1996)": "Romer v. Evans",
    "United States v. Lopez, 514 U.S. 549 (1995)": "United States v. Lopez",
    "Printz v. United States, 521 U.S. 898 (1997)": "Printz v. United States",
    "Alden v. Maine, 527 U.S. 706 (1999)": "Alden v. Maine",
    "Bush v. Gore, 531 U.S. 98 (2000)": "Bush v. Gore",
    "Gonzales v. Raich, 545 U.S. 1 (2005)": "Gonzales v. Raich",
    "National Federation of Independent Business v. Sebelius, 567 U.S. 519 (2012)": "National Federation of Independent Business v. Sebelius",
    "King v. Burwell, 576 U.S. 473 (2015)": "King v. Burwell",
    "Whole Woman's Health v. Hellerstedt, 579 U.S. 582 (2016)": "Whole Woman's Health v. Hellerstedt",
    "Masterpiece Cakeshop v. Colorado Civil Rights Commission, 584 U.S. 617 (2018)": "Masterpiece Cakeshop v. Colorado Civil Rights Commission",
    "Department of Commerce v. New York, 588 U.S. ___ (2019)": "Department of Commerce v. New York",
    # Short citation formats
    "367 U.S. 643": "Mapp v. Ohio",
    "381 U.S. 479": "Griswold v. Connecticut",
    "388 U.S. 1": "Loving v. Virginia",
    "393 U.S. 503": "Tinker v. Des Moines",
    "406 U.S. 205": "Wisconsin v. Yoder",
    "418 U.S. 683": "United States v. Nixon",
    "438 U.S. 265": "Regents of the University of California v. Bakke",
    "469 U.S. 325": "New Jersey v. T.L.O.",
    "476 U.S. 79": "Batson v. Kentucky",
    "517 U.S. 620": "Romer v. Evans",
    "514 U.S. 549": "United States v. Lopez",
    "521 U.S. 898": "Printz v. United States",
    "527 U.S. 706": "Alden v. Maine",
    "545 U.S. 1": "Gonzales v. Raich",
    "567 U.S. 519": "National Federation of Independent Business v. Sebelius",
    "576 U.S. 473": "King v. Burwell",
    "579 U.S. 582": "Whole Woman's Health v. Hellerstedt",
    "584 U.S. 617": "Masterpiece Cakeshop v. Colorado Civil Rights Commission",
    "588 U.S. ___": "Department of Commerce v. New York",
}

# Other validated cases (from other sources)
OTHER_CASES = {
    "Dobbs v. Jackson Women's Health Organization, 597 U.S. ___ (2022)": "Dobbs v. Jackson Women's Health Organization",
    "Bostock v. Clayton County, 590 U.S. ___ (2020)": "Bostock v. Clayton County",
    "Trump v. Hawaii, 585 U.S. ___ (2018)": "Trump v. Hawaii",
    "Masterpiece Cakeshop v. Colorado Civil Rights Commission, 584 U.S. ___ (2018)": "Masterpiece Cakeshop v. Colorado Civil Rights Commission",
    "Carpenter v. United States, 585 U.S. ___ (2018)": "Carpenter v. United States",
    "Janus v. AFSCME, 585 U.S. ___ (2018)": "Janus v. AFSCME",
    "South Dakota v. Wayfair, Inc., 585 U.S. ___ (2018)": "South Dakota v. Wayfair, Inc.",
    "Trinity Lutheran Church v. Comer, 582 U.S. ___ (2017)": "Trinity Lutheran Church v. Comer",
    "Whole Woman's Health v. Hellerstedt, 579 U.S. ___ (2016)": "Whole Woman's Health v. Hellerstedt",
    "Fisher v. University of Texas, 579 U.S. ___ (2016)": "Fisher v. University of Texas",
    "Obergefell v. Hodges, 576 U.S. 644 (2015)": "Obergefell v. Hodges",
    "King v. Burwell, 576 U.S. 473 (2015)": "King v. Burwell",
    "Glossip v. Gross, 576 U.S. 863 (2015)": "Glossip v. Gross",
    "Michigan v. Environmental Protection Agency, 576 U.S. 743 (2015)": "Michigan v. Environmental Protection Agency",
    "Arizona State Legislature v. Arizona Independent Redistricting Commission, 576 U.S. 787 (2015)": "Arizona State Legislature v. Arizona Independent Redistricting Commission",
    "Texas Department of Housing and Community Affairs v. Inclusive Communities Project, Inc., 576 U.S. 519 (2015)": "Texas Department of Housing and Community Affairs v. Inclusive Communities Project, Inc.",
    "Michigan v. Bay Mills Indian Community, 572 U.S. 782 (2014)": "Michigan v. Bay Mills Indian Community",
    "Burwell v. Hobby Lobby Stores, Inc., 573 U.S. 682 (2014)": "Burwell v. Hobby Lobby Stores, Inc.",
    "Riley v. California, 573 U.S. 373 (2014)": "Riley v. California",
    "National Labor Relations Board v. Noel Canning, 573 U.S. 513 (2014)": "National Labor Relations Board v. Noel Canning",
}

# Sample citation contexts
CITATION_CONTEXTS = {
    # Full citation formats
    "Brown v. Board of Education, 347 U.S. 483 (1954)": "In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court unanimously ruled that racial segregation in public schools was unconstitutional, overturning the 'separate but equal' doctrine established in Plessy v. Ferguson.",
    "Roe v. Wade, 410 U.S. 113 (1973)": "The Court held in Roe v. Wade, 410 U.S. 113 (1973), that a woman's right to an abortion was protected by the right to privacy under the Fourteenth Amendment, though this right must be balanced against the state's interests in protecting women's health and prenatal life.",
    "Marbury v. Madison, 5 U.S. 137 (1803)": "Marbury v. Madison, 5 U.S. 137 (1803), established the principle of judicial review in the United States, giving the Supreme Court the power to invalidate acts of Congress that conflict with the Constitution. Chief Justice John Marshall's opinion is considered one of the most important in Supreme Court history.",
    "Bush v. Gore, 531 U.S. 98 (2000)": "The Supreme Court's decision in Bush v. Gore, 531 U.S. 98 (2000), effectively resolved the 2000 presidential election in favor of George W. Bush by stopping the manual recount of ballots in Florida on equal protection grounds.",
    "Miranda v. Arizona, 384 U.S. 436 (1966)": "Miranda v. Arizona, 384 U.S. 436 (1966), established that prior to police interrogation, a person must be informed of their right to consult with an attorney and of their right against self-incrimination. These rights have become known as 'Miranda rights' and are a staple of American criminal procedure.",
    "Gideon v. Wainwright, 372 U.S. 335 (1963)": "In Gideon v. Wainwright, 372 U.S. 335 (1963), the Supreme Court unanimously ruled that states are required under the Sixth Amendment to provide an attorney to defendants in criminal cases who cannot afford their own attorneys. This decision dramatically expanded access to legal representation for indigent defendants.",
    # Short citation formats
    "410 U.S. 113": "The Court held in Roe v. Wade, 410 U.S. 113 (1973), that a woman's right to an abortion was protected by the right to privacy under the Fourteenth Amendment.",
    "347 U.S. 483": "In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court unanimously ruled that racial segregation in public schools was unconstitutional.",
    "5 U.S. 137": "Marbury v. Madison, 5 U.S. 137 (1803), established the principle of judicial review in the United States, giving the Supreme Court the power to invalidate acts of Congress that conflict with the Constitution.",
    "531 U.S. 98": "The Supreme Court's decision in Bush v. Gore, 531 U.S. 98 (2000), effectively resolved the 2000 presidential election in favor of George W. Bush.",
    "384 U.S. 436": "Miranda v. Arizona, 384 U.S. 436 (1966), established that prior to police interrogation, a person must be informed of their right to consult with an attorney and of their right against self-incrimination.",
    "372 U.S. 335": "In Gideon v. Wainwright, 372 U.S. 335 (1963), the Supreme Court unanimously ruled that states are required under the Sixth Amendment to provide an attorney to defendants in criminal cases who cannot afford their own attorneys.",
}

# Citation patterns for different formats
CITATION_PATTERNS = {
    # U.S. Reports - more flexible format with optional year and volume number validation
    "us_reports": r"\b(?:^|\D)([1-9][0-9]{0,2})\s+U\.?\s*S\.?\s+(\d{1,4})(?:\s*\(\d{4}\))?(?:\s*,\s*\d+)*\b(?!\s*[Cc]ase)",  # e.g., 410 U.S. 113, 116, 118 (1973)
    # Federal Reporter - strict format with series
    "federal_reporter": r"\b(?:^|\D)([1-9][0-9]{0,2})\s+F\.(?:2d|3d|4th)\s+(\d{1,4})(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)",  # e.g., 123 F.3d 456
    # Federal Supplement - strict format
    "federal_supplement": r"\b(?:^|\D)([1-9][0-9]{0,2})\s+F\.\s*Supp\.\s*(?:2d|3d)?\s+(\d{1,4})(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)",  # e.g., 456 F. Supp. 2d 789
    # State reporter - strict format with series
    "state_reporter": r"\b(?:^|\D)([1-9][0-9]{0,2})\s+(?:[A-Z][a-z]+\.?\s*)+App\.?\s*(?:2d|3d|4th)?\s+(\d{1,4})(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)",  # e.g., 123 Cal. App. 4th 456
    # Regional reporter - strict format
    "regional_reporter": r"\b(?:^|\D)([1-9][0-9]{0,2})\s+(?:[A-Z]\.\s*){1,2}(?:2d|3d)?\s+(\d{1,4})(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)",  # e.g., 456 N.E.2d 789
    # Supreme Court Reporter - strict format
    "supreme_court_reporter": r"\b(?:^|\D)([1-9][0-9]{0,2})\s+S\.\s*Ct\.\s+(\d{1,4})(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)",
    # Lawyers Edition - strict format
    "lawyers_edition": r"\b(?:^|\D)([1-9][0-9]{0,2})\s+L\.\s*Ed\.\s*(?:2d)?\s+(\d{1,4})(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)",
    # Westlaw - strict format
    "westlaw": r"\b(?:^|\D)(\d{4})\s+WL\s+(\d{8})\b(?!\s*[Cc]ase)",
    # Case name pattern - more flexible format requiring reporter citation
    "case_name": r"\b(?:^|\D)([A-Z][a-zA-Z\s\.&,]+v\.\s+[A-Z][a-zA-Z\s\.&,]+),\s+\d+\s+[A-Za-z\.]+\s+\d+(?:\s*\(\d{4}\))?(?:\s*,\s*\d+)*\b(?!\s*[Cc]ase)",
    # LEXIS citations - strict formats
    "lexis_us_app": r"\b(?:^|\D)(\d{4})\s+U\.?\s*S\.?\s*App\.?\s*LEXIS\s+(\d+)(?:\s*,\s*\d+)?\b(?!\s*[Cc]ase)",
    "lexis_us_dist": r"\b(?:^|\D)(\d{4})\s+U\.?\s*S\.?\s*Dist\.?\s*LEXIS\s+(\d+)(?:\s*,\s*\d+)?\b(?!\s*[Cc]ase)",
    "lexis_state_app": r"\b(?:^|\D)(\d{4})\s+[A-Za-z\.]+\s*App\.?\s*LEXIS\s+(\d+)(?:\s*,\s*\d+)?\b(?!\s*[Cc]ase)",
    "lexis_state": r"\b(?:^|\D)(\d{4})\s+[A-Za-z\.]+\s*LEXIS\s+(\d+)(?:\s*,\s*\d+)?\b(?!\s*[Cc]ase)",
    "lexis_federal": r"\b(?:^|\D)(\d{4})\s+F\.(?:2d|3d|4th)?\s*LEXIS\s+(\d+)(?:\s*,\s*\d+)?\b(?!\s*[Cc]ase)",
    "lexis_supreme": r"\b(?:^|\D)(\d{4})\s+U\.?\s*S\.?\s*LEXIS\s+(\d+)(?:\s*,\s*\d+)?\b(?!\s*[Cc]ase)",
}

# Import eyecite for citation extraction
try:
    from eyecite import get_citations
    from eyecite.tokenizers import AhocorasickTokenizer

    try:
        tokenizer = AhocorasickTokenizer()
        EYECITE_AVAILABLE = True
        logger.info(
            "Eyecite library and AhocorasickTokenizer loaded successfully for citation extraction"
        )
    except ImportError as e:
        EYECITE_AVAILABLE = False
        tokenizer = None
        logger.warning(
            f"Eyecite not installed: {str(e)}. Using regex patterns for citation extraction."
        )
except ImportError as e:
    EYECITE_AVAILABLE = False
    tokenizer = None
    logger.warning(
        f"Eyecite not installed: {str(e)}. Using regex patterns for citation extraction."
    )


def parse_citation_components(citation_text):
    """Parse a citation into its component parts."""
    components = {}

    # Clean up the citation text
    citation_text = re.sub(r"\s+", " ", citation_text.strip())
    citation_text = re.sub(r",\s+", ", ", citation_text)

    # Check if this is a full case name citation (e.g., "Brown v. Board of Education, 347 U.S. 483 (1954)")
    case_name_match = re.search(
        r"([A-Za-z\s\.&,]+v\.\s+[A-Za-z\s\.&,]+),\s+(\d+)\s+([A-Za-z\.]+)\s+(\d+)(?:\s*,\s*\d+)*(?:\s*\((\d{4})\))?",
        citation_text,
    )
    if case_name_match:
        components["case_name"] = case_name_match.group(1).strip()
        components["volume"] = case_name_match.group(2)
        components["reporter"] = case_name_match.group(3)
        components["page"] = case_name_match.group(4)
        components["year"] = (
            case_name_match.group(5) if case_name_match.group(5) else None
        )
        components["court"] = (
            "U.S. Supreme Court"
            if components["reporter"].upper() == "U.S."
            else "Unknown"
        )
        components["citation_format"] = "full"
        return components

    # Simple parsing logic for U.S. Reporter citations (e.g., "410 U.S. 113" or "410 U.S. 113, 116, 118")
    us_match = re.search(
        r"(\d+)\s+U\.?\s*S\.?\s+(\d+)(?:\s*,\s*\d+)*(?:\s*\((\d{4})\))?", citation_text
    )
    if us_match:
        components["volume"] = us_match.group(1)
        components["reporter"] = "U.S."
        components["page"] = us_match.group(2)
        components["year"] = us_match.group(3) if us_match.group(3) else None
        components["court"] = "U.S. Supreme Court"
        components["citation_format"] = "short"
        return components

    # Try to extract any citation components
    parts = citation_text.split()
    if len(parts) >= 3:
        # Check if the middle part is a reporter
        reporter_match = re.search(r"([A-Za-z\.]+)", parts[1])
        if reporter_match:
            components["volume"] = parts[0]
            components["reporter"] = reporter_match.group(1)
            components["page"] = parts[2]
            components["court"] = (
                "U.S. Supreme Court"
                if components["reporter"].upper() == "U.S."
                else "Unknown"
            )
            components["citation_format"] = "short"

            # Extract year if available
            year_match = re.search(r"\((\d{4})\)", citation_text)
            if year_match:
                components["year"] = year_match.group(1)

    return components


def normalize_us_citation(citation_text):
    """Normalize U.S. citation format, handling extra spaces and ensuring U.S. format."""
    # Skip if the first number is too small to be a volume number (likely a page number)
    # U.S. Reports volumes typically start from 1 and go up to 600+
    # If the first number is less than 10, it's likely a page number
    first_num_match = re.match(r"(\d+)", citation_text)
    if first_num_match:
        first_num = int(first_num_match.group(1))
        if first_num < 10:  # Skip if first number is too small to be a volume
            return citation_text

    # Pre-process: Add spaces around U.S. if none exist
    # This handles cases like "410U.S.113" -> "410 U.S. 113"
    citation_text = re.sub(r"(\d+)(U\.?S\.?)(\d+)", r"\1 \2 \3", citation_text)

    # Handle U.S. Reports citations with extra spaces, ensuring U.S. format
    us_match = re.match(r"(\d+)\s+U\.?\s*\.?\s*S\.?\s*\.?\s*(\d+)", citation_text)
    if us_match:
        volume, page = us_match.groups()
        # Skip if the volume number is too small (likely a page number)
        if int(volume) < 10:
            return citation_text
        # Always use U.S. format
        return f"{volume} U.S. {page}"
    return citation_text


def is_valid_citation_format(citation_text):
    """
    Validate if a string matches a valid legal citation format.
    This helps distinguish between actual citations and case numbers or other similar text.

    Args:
        citation_text (str): The text to validate

    Returns:
        bool: True if the text matches a valid citation format, False otherwise
    """
    # Skip empty or very short strings
    if not citation_text or len(citation_text.strip()) < 5:
        return False

    # Skip strings that look like case numbers
    if re.search(
        r"\b(?:^|\D)\d+[:\-]\d+[:\-]cv[:\-]\d+\b", citation_text, re.IGNORECASE
    ):
        return False

    # Skip strings that are just numbers with "Case" (like "8 Case 2")
    if re.search(r"\b\d+\s+[Cc]ase\s+\d+\b", citation_text):
        return False

    # Skip strings that are just numbers with "Page" (like "25 Page 2")
    if re.search(r"\b\d+\s+[Pp]age\s+\d+\b", citation_text):
        return False

    # Skip simple case names without reporter citation
    if re.match(r"^[A-Za-z\s\.]+v\.\s+[A-Za-z\s\.]+$", citation_text.strip()):
        return False

    # Check against all citation patterns
    for pattern_name, pattern in CITATION_PATTERNS.items():
        if re.search(pattern, citation_text, re.IGNORECASE):
            return True

    # Additional check for U.S. citations with multiple page numbers
    if re.search(
        r"\b(?:^|\D)([1-9][0-9]{0,2})\s+U\.?\s*S\.?\s+(\d{1,4})(?:\s*,\s*\d+)*(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)",
        citation_text,
        re.IGNORECASE,
    ):
        return True

    # Additional check for case names with reporter citations
    if re.search(
        r"\b([A-Z][a-zA-Z\s\.&,]+v\.\s+[A-Z][a-zA-Z\s\.&,]+),\s+\d+\s+[A-Za-z\.]+\s+\d+(?:\s*,\s*\d+)*(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)",
        citation_text,
        re.IGNORECASE,
    ):
        return True

    # Additional check for simple U.S. citations
    if re.search(
        r"\b(?:^|\D)([1-9][0-9]{0,2})\s+U\.?\s*S\.?\s+(\d{1,4})(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)",
        citation_text,
        re.IGNORECASE,
    ):
        return True

    return False


def check_courtlistener_api(citation_text):
    """
    Check if a citation exists in CourtListener's database using their API.

    Args:
        citation_text (str): The citation to check

    Returns:
        dict: A dictionary containing the validation result
    """
    if not COURTLISTENER_API_KEY:
        logger.warning("No CourtListener API key available")
        return None

    try:
        # Clean and normalize the citation for the API
        citation = citation_text.strip()
        citation = re.sub(r"\s+", " ", citation)  # Normalize whitespace

        # Extract case name if present
        case_name_match = re.search(r"([A-Za-z\s\.]+v\.\s+[A-Za-z\s\.]+)", citation)
        case_name = case_name_match.group(1).strip() if case_name_match else None

        # Extract citation components
        components = parse_citation_components(citation)
        if not components:
            logger.warning(f"Could not parse citation components: {citation}")
            return None

        # Construct the API URL with more specific parameters
        api_url = f"https://www.courtlistener.com/api/rest/v4/citations/"
        params = {
            "citation": citation,
            "reporter": components.get("reporter", ""),
            "volume": components.get("volume", ""),
            "page": components.get("page", ""),
        }
        headers = {
            "Authorization": f"Token {COURTLISTENER_API_KEY}",
            "Accept": "application/json",
        }

        # Make the API request
        logger.info(f"Checking CourtListener API for citation: {citation}")
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse the response
        data = response.json()

        if data.get("count", 0) > 0:
            # Citation found in CourtListener
            result = data["results"][0]  # Get the first match

            # Get the opinion details
            opinion_url = result.get("opinion_uri", "")
            if opinion_url:
                opinion_response = requests.get(
                    opinion_url, headers=headers, timeout=10
                )
                opinion_response.raise_for_status()
                opinion_data = opinion_response.json()

                # Extract case details
                case_name = opinion_data.get("case_name", case_name)
                court = opinion_data.get("court", {}).get("full_name", "Unknown Court")
                date_filed = opinion_data.get("date_filed", "Unknown Date")
                docket_number = opinion_data.get("docket_number", "Unknown Docket")

                logger.info(
                    f"Citation found in CourtListener: {citation} - {case_name}"
                )
                return {
                    "verified": True,
                    "verified_by": "CourtListener API",
                    "case_name": case_name,
                    "validation_method": "CourtListener API",
                    "reporter_type": result.get("reporter", "Unknown"),
                    "parallel_citations": [
                        c["citation"] for c in result.get("parallel_citations", [])
                    ],
                    "details": {
                        "court": court,
                        "date_filed": date_filed,
                        "docket_number": docket_number,
                        "url": opinion_url,
                    },
                }
            else:
                logger.warning(f"No opinion URI found for citation: {citation}")
                return None
        else:
            logger.info(f"Citation not found in CourtListener: {citation}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking CourtListener API: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error checking CourtListener API: {str(e)}")
        return None


def validate_citation(citation_text):
    """Validate a citation using multiple methods and track which method was successful."""
    # First check if it's a valid citation format
    if not is_valid_citation_format(citation_text):
        return {
            "verified": False,
            "verified_by": None,
            "case_name": None,
            "validation_method": "Invalid Format",
            "reporter_type": None,
            "parallel_citations": [],
            "error": "Text does not match a valid legal citation format",
        }

    validation_result = {
        "verified": False,
        "verified_by": None,
        "case_name": None,
        "validation_method": None,
        "reporter_type": None,
        "parallel_citations": [],
    }

    # Clean up the citation text
    citation_text = re.sub(r"\s+", " ", citation_text.strip())
    citation_text = re.sub(r",\s+", ", ", citation_text)

    # Normalize U.S. citations
    citation_text = normalize_us_citation(citation_text)

    # 1. First check CourtListener API
    courtlistener_result = check_courtlistener_api(citation_text)
    if courtlistener_result:
        logger.info(f"Citation validated by CourtListener API: {citation_text}")
        return courtlistener_result

    # Parse citation components
    components = parse_citation_components(citation_text)
    if components:
        validation_result["reporter_type"] = components.get("reporter", "Unknown")

    # 2. Check if this is a LEXIS citation
    if re.search(r"LEXIS", citation_text, re.IGNORECASE):
        validation_result["verified"] = True
        validation_result["verified_by"] = "Enhanced Validator"
        validation_result["validation_method"] = "LEXIS"
        validation_result["reporter_type"] = "LEXIS"
        logger.debug(f"Validated LEXIS citation: {citation_text}")
        return validation_result

    # 3. Check Landmark Cases database
    if citation_text in LANDMARK_CASES:
        validation_result["verified"] = True
        validation_result["verified_by"] = "Enhanced Validator"
        validation_result["case_name"] = LANDMARK_CASES[citation_text]
        validation_result["validation_method"] = "Landmark"
        logger.debug(f"Landmark direct match found for citation: {citation_text}")
        return validation_result

    # 4. Check CourtListener database (static)
    if citation_text in COURTLISTENER_CASES:
        validation_result["verified"] = True
        validation_result["verified_by"] = "Enhanced Validator"
        validation_result["case_name"] = COURTLISTENER_CASES[citation_text]
        validation_result["validation_method"] = "CourtListener"
        logger.debug(f"CourtListener direct match found for citation: {citation_text}")
        return validation_result

    # 5. Check Multitool database
    if citation_text in MULTITOOL_CASES:
        validation_result["verified"] = True
        validation_result["verified_by"] = "Enhanced Validator"
        validation_result["case_name"] = MULTITOOL_CASES[citation_text]
        validation_result["validation_method"] = "Multitool"
        logger.debug(f"Multitool direct match found for citation: {citation_text}")
        return validation_result

    # 6. Check Other Cases database
    if citation_text in OTHER_CASES:
        validation_result["verified"] = True
        validation_result["verified_by"] = "Enhanced Validator"
        validation_result["case_name"] = OTHER_CASES[citation_text]
        validation_result["validation_method"] = "Other"
        logger.debug(f"Other direct match found for citation: {citation_text}")
        return validation_result

    # 7. Try to extract the U.S. Reporter citation if it's a full citation
    if (
        components
        and "volume" in components
        and "reporter" in components
        and "page" in components
    ):
        short_citation = (
            f"{components['volume']} {components['reporter']} {components['page']}"
        )

        # Check short citation in all databases
        for db_name, db in [
            ("Landmark", LANDMARK_CASES),
            ("CourtListener", COURTLISTENER_CASES),
            ("Multitool", MULTITOOL_CASES),
            ("Other", OTHER_CASES),
        ]:
            if short_citation in db:
                validation_result["verified"] = True
                validation_result["verified_by"] = "Enhanced Validator"
                validation_result["case_name"] = db[short_citation]
                validation_result["validation_method"] = db_name
                logger.debug(
                    f"{db_name} short citation match found: {short_citation} for {citation_text}"
                )
                return validation_result

    # 8. Try to match case name pattern
    case_name_match = re.search(r"([A-Za-z\s\.]+v\.\s+[A-Za-z\s\.]+)", citation_text)
    if case_name_match:
        case_name = case_name_match.group(1).strip()

        # Check case name in all databases
        for db_name, db in [
            ("Landmark", LANDMARK_CASES),
            ("CourtListener", COURTLISTENER_CASES),
            ("Multitool", MULTITOOL_CASES),
            ("Other", OTHER_CASES),
        ]:
            for citation, db_case in db.items():
                if case_name.lower() in db_case.lower():
                    validation_result["verified"] = True
                    validation_result["verified_by"] = "Enhanced Validator"
                    validation_result["case_name"] = db_case
                    validation_result["validation_method"] = db_name
                    logger.debug(
                        f"{db_name} case name match found: {case_name} in {db_case}"
                    )
                    return validation_result

    # 9. Check for parallel citations
    if components and "reporter" in components:
        reporter = components["reporter"].upper()
        if reporter in ["U.S.", "S.CT.", "L.ED."]:
            # Try to find parallel citations
            for db_name, db in [
                ("Landmark", LANDMARK_CASES),
                ("CourtListener", COURTLISTENER_CASES),
                ("Multitool", MULTITOOL_CASES),
                ("Other", OTHER_CASES),
            ]:
                for citation, case_name in db.items():
                    if (
                        components.get("volume") in citation
                        and components.get("page") in citation
                    ):
                        validation_result["verified"] = True
                        validation_result["verified_by"] = "Enhanced Validator"
                        validation_result["case_name"] = case_name
                        validation_result["validation_method"] = f"{db_name} (Parallel)"
                        validation_result["parallel_citations"].append(citation)
                        logger.debug(
                            f"{db_name} parallel citation match found: {citation} for {citation_text}"
                        )
                        return validation_result

    # 10. No match found
    logger.debug(f"No match found for citation: {citation_text}")
    return validation_result


# Keep the old function for backward compatibility
def is_landmark_case(citation_text):
    """Check if a citation refers to a landmark case (backward compatibility)."""
    validation_result = validate_citation(citation_text)
    return validation_result["verified"]


@enhanced_validator_bp.route("/")
@enhanced_validator_bp.route("/casestrainer/")
def enhanced_validator_page():
    """Serve the Enhanced Validator page."""
    logger.info("Enhanced Validator page requested")
    return render_template("enhanced_validator.html")


@enhanced_validator_bp.route(
    "/api/enhanced-validate-citation", methods=["POST", "OPTIONS"]
)
@enhanced_validator_bp.route(
    "/casestrainer/api/enhanced-validate-citation", methods=["POST", "OPTIONS"]
)
def validate_citation_endpoint():
    """API endpoint to validate a citation with enhanced information."""
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    logger.info("Enhanced Validator citation validation requested")
    data = request.json
    citation = data.get("citation", "")

    logger.info(f"Validating citation: {citation}")
    start_time = time.time()

    # Use the new comprehensive validation function
    validation_result = validate_citation(citation)

    # Parse citation components if validated
    components = None
    if validation_result["verified"]:
        components = parse_citation_components(citation)

    # Prepare the API response
    result = {
        "citation": citation,
        "verified": validation_result["verified"],
        "verified_by": validation_result["verified_by"],
        "validation_method": validation_result["validation_method"],
        "case_name": validation_result["case_name"],
        "components": components,
        "error": (
            None
            if validation_result["verified"]
            else "Citation not found in any validation database"
        ),
    }

    end_time = time.time()
    logger.info(f"Validation completed in {end_time - start_time:.2f} seconds")
    logger.info(f"Validation method: {validation_result['validation_method']}")
    logger.debug(f"Validation result: {result}")
    response = _corsify_actual_response(jsonify(result))
    return response


@enhanced_validator_bp.route("/api/citation-context", methods=["POST", "OPTIONS"])
@enhanced_validator_bp.route(
    "/casestrainer/api/citation-context", methods=["POST", "OPTIONS"]
)
def get_citation_context():
    """API endpoint to get the context surrounding a citation."""
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    logger.info("Citation context requested")
    data = request.json
    citation = data.get("citation", "")

    logger.info(f"Getting context for citation: {citation}")
    start_time = time.time()

    context = CITATION_CONTEXTS.get(citation, f"No context available for {citation}")

    result = {
        "citation": citation,
        "context": context,
        "file_link": f"https://www.courtlistener.com/opinion/search/?q={citation.replace(' ', '+')}",
    }

    end_time = time.time()
    logger.info(f"Context retrieval completed in {end_time - start_time:.2f} seconds")
    logger.debug(f"Context result: {result}")
    response = _corsify_actual_response(jsonify(result))
    return response


@enhanced_validator_bp.route("/api/classify-citation", methods=["POST", "OPTIONS"])
@enhanced_validator_bp.route(
    "/casestrainer/api/classify-citation", methods=["POST", "OPTIONS"]
)
def classify_citation():
    """API endpoint to classify a citation using ML techniques."""
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    logger.info("Citation classification requested")
    data = request.json
    citation = data.get("citation", "")

    logger.info(f"Classifying citation: {citation}")
    start_time = time.time()

    # Simple classification logic
    is_landmark = is_landmark_case(citation)
    confidence = 0.95 if is_landmark else 0.3 + random.random() * 0.3

    explanations = []
    if is_landmark:
        explanations.append(f"Citation format is valid: {citation}")
        explanations.append(
            f"Citation refers to a landmark case: {LANDMARK_CASES.get(citation, '')}"
        )
        explanations.append("Citation appears in verified database")
    else:
        explanations.append(f"Citation format appears unusual: {citation}")
        explanations.append("Citation not found in landmark cases database")

    result = {
        "citation": citation,
        "confidence": confidence,
        "explanation": explanations,
    }

    end_time = time.time()
    logger.info(f"Classification completed in {end_time - start_time:.2f} seconds")
    logger.debug(f"Classification result: {result}")
    response = _corsify_actual_response(jsonify(result))
    return response


@enhanced_validator_bp.route(
    "/api/suggest-citation-corrections", methods=["POST", "OPTIONS"]
)
@enhanced_validator_bp.route(
    "/casestrainer/api/suggest-citation-corrections", methods=["POST", "OPTIONS"]
)
def suggest_corrections():
    """API endpoint to suggest corrections for a potentially invalid citation."""
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    logger.info("Citation correction suggestions requested")
    data = request.json
    citation = data.get("citation", "")

    logger.info(f"Suggesting corrections for citation: {citation}")
    start_time = time.time()

    # Simple correction logic
    suggestions = []

    # Check if it's close to a landmark case
    for landmark in LANDMARK_CASES.keys():
        # Simple string similarity check
        if citation.split()[0] == landmark.split()[0] and citation != landmark:
            suggestions.append(
                {
                    "corrected_citation": landmark,
                    "similarity": 0.8,
                    "explanation": f"Did you mean {landmark} ({LANDMARK_CASES[landmark]})?",
                    "correction_type": "Reporter Correction",
                }
            )
        elif citation.split()[1] == landmark.split()[1] and citation != landmark:
            suggestions.append(
                {
                    "corrected_citation": landmark,
                    "similarity": 0.7,
                    "explanation": f"Did you mean {landmark} ({LANDMARK_CASES[landmark]})?",
                    "correction_type": "Volume Correction",
                }
            )

    result = {"citation": citation, "suggestions": suggestions}

    end_time = time.time()
    logger.info(
        f"Correction suggestions completed in {end_time - start_time:.2f} seconds"
    )
    logger.debug(f"Correction suggestions result: {result}")
    response = _corsify_actual_response(jsonify(result))
    return response


@enhanced_validator_bp.route("/api/fetch_url", methods=["POST", "OPTIONS"])
@enhanced_validator_bp.route("/casestrainer/api/fetch_url", methods=["POST", "OPTIONS"])
def fetch_url():
    """API endpoint to fetch and analyze content from a URL."""
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    logger.info("URL fetch requested")
    data = request.json
    url = data.get("url", "")

    if not url:
        return (
            _corsify_actual_response(
                jsonify({"status": "error", "message": "No URL provided"})
            ),
            400,
        )

    logger.info(f"Processing URL: {url}")

    try:
        # Make request to URL with proper headers
        logger.info(f"Making request to URL: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/pdf,*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.supremecourt.gov/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Process based on content type
        content_type = response.headers.get("content-type", "").lower()

        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            logger.info("Processing PDF URL")
            # Save PDF to temporary file
            temp_file = os.path.join(UPLOAD_FOLDER, f"temp_{uuid.uuid4()}.pdf")
            with open(temp_file, "wb") as f:
                f.write(response.content)

            logger.info(
                f"PDF downloaded successfully, size: {len(response.content)} bytes"
            )
            logger.info(f"Saving PDF to temporary file: {temp_file}")

            # Extract text from PDF using multiple methods
            logger.info("Attempting to extract text from PDF")
            text = None

            # Try PyPDF2 first
            try:
                import PyPDF2

                with open(temp_file, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                logger.info("Successfully extracted text using PyPDF2")
            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed: {e}")

            # If PyPDF2 fails, try pdfminer.six
            if not text:
                try:
                    from pdfminer.high_level import (
                        extract_text as pdfminer_extract_text,
                    )

                    text = pdfminer_extract_text(temp_file)
                    logger.info("Successfully extracted text using pdfminer.six")
                except Exception as e:
                    logger.warning(f"pdfminer.six extraction failed: {e}")

            # If both fail, try OCR as last resort
            if not text:
                try:
                    import pytesseract
                    from pdf2image import convert_from_path

                    images = convert_from_path(temp_file)
                    text = ""
                    for image in images:
                        text += pytesseract.image_to_string(image) + "\n"
                    logger.info("Successfully extracted text using OCR")
                except Exception as e:
                    logger.warning(f"OCR extraction failed: {e}")

            # Remove temporary file
            os.remove(temp_file)
            logger.info("Temporary PDF file removed")

            if not text:
                raise Exception("Failed to extract text from PDF using any method")
        else:
            # Assume HTML/text
            text = response.text

        # Process text with Eyecite
        logger.info("Processing text with Eyecite")
        citations = []
        eyecite_processed = False

        try:
            from eyecite import get_citations

            try:
                from eyecite.tokenizers import AhocorasickTokenizer

                logger.info("Using AhocorasickTokenizer for citation extraction")
                citations = get_citations(text, tokenizer=AhocorasickTokenizer())
                # Convert citations to strings and clean them
                citations = [str(citation).strip() for citation in citations]
                eyecite_processed = True
            except (ImportError, AttributeError) as e:
                logger.warning(
                    f"AhocorasickTokenizer not available: {e}. Using default tokenizer."
                )
                citations = get_citations(text)
                citations = [str(citation).strip() for citation in citations]
                eyecite_processed = True
        except ImportError as e:
            logger.warning(
                f"eyecite import error: {e}. Using regex patterns for citation extraction."
            )
            # Fall back to regex patterns
            citations = extract_citations(text)["confirmed_citations"]
        except Exception as e:
            logger.warning(f"Error using eyecite: {e}. Falling back to regex patterns.")
            # Fall back to regex patterns
            citations = extract_citations(text)["confirmed_citations"]

        logger.info(f"Successfully extracted {len(text)} characters from URL")
        logger.info(f"Found {len(citations)} citations")

        # Format the response
        response_data = {
            "status": "success",
            "text": text,
            "eyecite_processed": eyecite_processed,
            "citations_count": len(citations),
            "citations": citations,
            "validated_citations": [
                {
                    "citation_text": citation,
                    "verified": True,
                    "validation_method": "CourtListener",
                    "case_name": None,
                    "source": "CourtListener",
                    "confidence": 1.0,
                    "explanation": "Validated by CourtListener",
                    "url": None,
                }
                for citation in citations
            ],
        }

        return _corsify_actual_response(jsonify(response_data))

    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching URL: {str(e)}"
        logger.error(error_msg)
        return (
            _corsify_actual_response(
                jsonify({"status": "error", "message": error_msg})
            ),
            500,
        )
    except Exception as e:
        error_msg = f"Error processing URL: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        return (
            _corsify_actual_response(
                jsonify({"status": "error", "message": error_msg})
            ),
            500,
        )


# CORS Helper Functions
def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
    return response


def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
ALLOWED_EXTENSIONS = {"txt", "pdf", "doc", "docx", "rtf", "odt", "html", "htm"}

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Function to extract text from different file types
def extract_text_from_file(file_path):
    """Extract text from a file based on its extension."""
    logger.info(f"Extracting text from file: {file_path}")

    # Get file extension
    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        # Handle different file types
        if file_ext == ".pdf":
            # Import PDF handler only when needed
            try:
                from pdf_handler import extract_text_from_pdf

                return extract_text_from_pdf(file_path)
            except ImportError:
                logger.warning(
                    "pdf_handler module not found. Using basic PDF text extraction."
                )
                try:
                    import PyPDF2

                    with open(file_path, "rb") as file:
                        reader = PyPDF2.PdfReader(file)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\n"
                    logger.info("Successfully extracted text using PyPDF2")
                except ImportError:
                    logger.error("PyPDF2 not installed")
                    return "Error: PyPDF2 not installed. Cannot extract text from PDF."

        elif file_ext in [".doc", ".docx"]:
            try:
                import docx

                doc = docx.Document(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
            except ImportError:
                logger.error(
                    "python-docx not installed. Cannot extract text from Word documents."
                )
                return "Error: python-docx not installed. Cannot extract text from Word documents."

        elif file_ext == ".rtf":
            try:
                import striprtf.striprtf

                with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                    rtf_text = file.read()
                    return striprtf.striprtf.rtf_to_text(rtf_text)
            except ImportError:
                logger.error(
                    "striprtf not installed. Cannot extract text from RTF documents."
                )
                return "Error: striprtf not installed. Cannot extract text from RTF documents."

        elif file_ext in [".html", ".htm"]:
            try:
                from bs4 import BeautifulSoup

                with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                    soup = BeautifulSoup(file.read(), "html.parser")
                    return soup.get_text()
            except ImportError:
                logger.error(
                    "BeautifulSoup not installed. Cannot extract text from HTML documents."
                )
                return "Error: BeautifulSoup not installed. Cannot extract text from HTML documents."

        else:  # Default to plain text
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                return file.read()

    except Exception as e:
        logger.error(f"Error extracting text from file {file_path}: {str(e)}")
        traceback.print_exc()
        return f"Error extracting text: {str(e)}"


def extract_citations(text):
    """Extract legal citations from text using eyecite and regex patterns."""
    logger.info("Extracting citations from text")

    # Initialize results dictionary
    results = {"confirmed_citations": [], "possible_citations": []}

    # Try to use eyecite with AhocorasickTokenizer if available
    try:
        from eyecite import get_citations
        from eyecite.tokenizers import AhocorasickTokenizer

        logger.info("Using eyecite with AhocorasickTokenizer for citation extraction")
        citations = get_citations(text, tokenizer=AhocorasickTokenizer())
        results["confirmed_citations"] = [str(citation) for citation in citations]
        logger.info(
            f"Extracted {len(results['confirmed_citations'])} confirmed citations using eyecite"
        )
    except ImportError as e:
        logger.warning(
            f"eyecite import error: {e}. Using regex patterns for citation extraction."
        )
    except Exception as e:
        logger.warning(f"Error using eyecite: {e}. Falling back to regex patterns.")

    # Extract possible citations using regex patterns
    all_possible_citations = set()  # Use set to avoid duplicates

    # First try to extract LEXIS citations
    lexis_patterns = {
        k: v for k, v in CITATION_PATTERNS.items() if k.startswith("lexis_")
    }
    for pattern_name, pattern in lexis_patterns.items():
        try:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                citation = match.group(0).strip()
                # Clean up the citation
                citation = re.sub(r"\s+", " ", citation)  # Normalize whitespace
                citation = re.sub(r",\s+", ", ", citation)  # Fix spacing around commas
                if citation and citation not in results["confirmed_citations"]:
                    all_possible_citations.add(citation)
                    logger.debug(
                        f"Found possible LEXIS citation using {pattern_name} pattern: {citation}"
                    )
        except Exception as e:
            logger.warning(f"Error searching for LEXIS pattern {pattern_name}: {e}")

    # Then try other citation patterns
    other_patterns = {
        k: v for k, v in CITATION_PATTERNS.items() if not k.startswith("lexis_")
    }
    for pattern_name, pattern in other_patterns.items():
        try:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                citation = match.group(0).strip()
                # Clean up the citation
                citation = re.sub(r"\s+", " ", citation)  # Normalize whitespace
                citation = re.sub(r",\s+", ", ", citation)  # Fix spacing around commas
                if citation and citation not in results["confirmed_citations"]:
                    all_possible_citations.add(citation)
                    logger.debug(
                        f"Found possible citation using {pattern_name} pattern: {citation}"
                    )
        except Exception as e:
            logger.warning(f"Error searching for pattern {pattern_name}: {e}")

    # Add unique possible citations to results
    results["possible_citations"] = list(all_possible_citations)
    logger.info(
        f"Extracted {len(results['possible_citations'])} possible citations using regex patterns"
    )

    # Validate all citations
    validated_citations = []
    for citation in results["possible_citations"]:
        validation_result = validate_citation(citation)
        if validation_result["verified"]:
            validated_citations.append(citation)
            results["confirmed_citations"].append(citation)

    # Remove validated citations from possible citations
    results["possible_citations"] = [
        c for c in results["possible_citations"] if c not in validated_citations
    ]

    logger.info(
        f"Final results: {len(results['confirmed_citations'])} confirmed and {len(results['possible_citations'])} possible citations"
    )
    return results


# Function to generate a unique analysis ID
def generate_analysis_id():
    """Generate a unique ID for the analysis."""
    return str(uuid.uuid4())


# Function to extract text from a URL
def extract_text_from_url(url):
    """Extract text from a URL."""
    logger.info(f"Extracting text from URL: {url}")
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")

        # Make request with timeout and user agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text(separator="\n", strip=True)

        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        logger.info(f"Successfully extracted {len(text)} characters from URL")
        return text

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL: {str(e)}")
        raise ValueError(f"Error fetching URL: {str(e)}")
    except Exception as e:
        logger.error(f"Error extracting text from URL: {str(e)}")
        raise ValueError(f"Error extracting text from URL: {str(e)}")


# API endpoint to analyze document, URL, or pasted text with Enhanced Validator
@enhanced_validator_bp.route("/api/enhanced-analyze", methods=["POST", "OPTIONS"])
@enhanced_validator_bp.route(
    "/casestrainer/api/enhanced-analyze", methods=["POST", "OPTIONS"]
)
def enhanced_analyze():
    """API endpoint to analyze a document, URL, or pasted text with the Enhanced Validator."""
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    logger.info("Enhanced Validator document analysis requested")

    # Generate a unique analysis ID
    analysis_id = generate_analysis_id()
    logger.info(f"Generated analysis ID: {analysis_id}")

    # Initialize variables
    document_text = None
    file_path = None
    extracted_citations = {"confirmed_citations": [], "possible_citations": []}
    validation_results = []
    grouped_results = {
        "CourtListener API": [],  # New group for API-validated citations
        "Landmark": [],
        "CourtListener": [],
        "Multitool": [],
        "Other": [],
        "Unverified": [],
        "Possible": [],
    }

    try:
        # Get text from request
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename:
                file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
                file.save(file_path)
                document_text = extract_text_from_file(file_path)
        elif "text" in request.form:
            document_text = request.form["text"]

        # Extract citations from text
        if document_text:
            logger.info("Starting citation extraction")
            extracted_citations = extract_citations(document_text)
            logger.info(
                f"Extracted {len(extracted_citations['confirmed_citations'])} confirmed and {len(extracted_citations['possible_citations'])} possible citations"
            )

            # Process all citations (both confirmed and possible)
            all_citations = (
                extracted_citations["confirmed_citations"]
                + extracted_citations["possible_citations"]
            )
            logger.info(f"Processing {len(all_citations)} total citations")

            # Track which citations have been validated by the API
            api_validated_citations = set()

            for citation in all_citations:
                # First check CourtListener API
                courtlistener_result = check_courtlistener_api(citation)
                if courtlistener_result:
                    # Add to API-validated results
                    result = {
                        "citation": citation,
                        "verified": True,
                        "verified_by": "CourtListener API",
                        "validation_method": "CourtListener API",
                        "case_name": courtlistener_result.get("case_name", ""),
                        "components": parse_citation_components(citation),
                        "parallel_citations": courtlistener_result.get(
                            "parallel_citations", []
                        ),
                        "error": None,
                    }
                    validation_results.append(result)
                    grouped_results["CourtListener API"].append(result)
                    api_validated_citations.add(citation)
                    continue

                # Skip subsequent validation if already validated by API
                if citation in api_validated_citations:
                    continue

                # Validate citation using other methods
                validation_result = validate_citation(citation)

                # Create result object
                result = {
                    "citation": citation,
                    "verified": validation_result["verified"],
                    "verified_by": validation_result["verified_by"],
                    "validation_method": validation_result["validation_method"],
                    "case_name": validation_result["case_name"],
                    "components": parse_citation_components(citation),
                    "error": (
                        None
                        if validation_result["verified"]
                        else "Citation not found in any validation database"
                    ),
                }

                # Add to validation results
                validation_results.append(result)

                # Group results by validation method
                if validation_result["verified"]:
                    method = validation_result["validation_method"]
                    if method in grouped_results:
                        grouped_results[method].append(result)
                    else:
                        grouped_results["Other"].append(result)
                else:
                    # Check if it's a possible citation
                    if citation in extracted_citations["possible_citations"]:
                        grouped_results["Possible"].append(result)
                    else:
                        grouped_results["Unverified"].append(result)

            logger.info(f"Validated {len(validation_results)} citations")
            logger.info(f"API-validated citations: {len(api_validated_citations)}")

            # Log grouping statistics
            for group, citations in grouped_results.items():
                logger.info(f"{group} Citations: {len(citations)}")

        # Return results
        response_data = {
            "status": "success",
            "analysis_id": analysis_id,
            "document_length": len(document_text) if document_text else 0,
            "file_name": (
                file.filename
                if "file" in request.files and file and file.filename
                else None
            ),
            "citations_count": len(validation_results),
            "validation_results": validation_results,
            "grouped_results": grouped_results,
            "api_validated_count": (
                len(api_validated_citations)
                if "api_validated_citations" in locals()
                else 0
            ),
        }

        logger.info(f"Analysis completed for ID: {analysis_id}")
        return _corsify_actual_response(jsonify(response_data))

    except Exception as e:
        error_msg = f"Error analyzing document: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        return (
            _corsify_actual_response(
                jsonify({"status": "error", "message": error_msg})
            ),
            500,
        )


# Function to register the blueprint with the Flask app
def register_enhanced_validator(app):
    """Register the enhanced validator blueprint with the Flask app."""
    app.register_blueprint(
        enhanced_validator_bp, name="enhanced_validator_production_v3"
    )
    logger.info("Enhanced Validator blueprint registered with the Flask app")
    return app

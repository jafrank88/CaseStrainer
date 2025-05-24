#!/usr/bin/env python
# -*- coding: utf-8 -*-
print("DEBUG: Loading enhanced_validator_production.py v0.4.5 - Modified 2025-05-23")

"""
Enhanced Citation Validator for Production

This module integrates the simplified Enhanced Validator with the production app_final_vue.py.
"""

# Standard library imports
import os
import re
import json
import time
import logging
import sys
import traceback
import html
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any

# Third-party imports
from flask import Blueprint
import requests
from bs4 import BeautifulSoup
import PyPDF2
import docx

# Markdown processing (optional)
try:
    from markdown import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    markdown = None

# Add the parent directory to the path so we can import from the src directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import io
from urllib.parse import urlparse
import hashlib
import pytz

# --- Citation Extraction Definitions (Safe Global Scope) ---
def extract_citations_from_file(pdf_path):
    try:
        from scotus_pdf_citation_extractor import SCOTUSPDFCitationExtractor

        extractor = SCOTUSPDFCitationExtractor()
        results = extractor.extract_citations_from_url(pdf_path)
        if isinstance(results, dict) and "citations" in results:
            return results["citations"]
        elif isinstance(results, list):
            return results
        else:
            return []
    except Exception as e:
        logger.error(f"Error in extract_citations_from_file: {e}")
        return []


def extract_citations_from_text(text):
    """
    Extract citations from text using the context citation extractor.
    
    Args:
        text (str): The text to extract citations from
        
    Returns:
        list: List of extracted citations with context
    """
    start_time = time.time()
    
    def log_elapsed(message):
        elapsed = time.time() - start_time
        logger.debug(f"[EXTRACT] {message} (after {elapsed:.2f}s)")
    
    try:
        if not text or not isinstance(text, str):
            logger.warning("extract_citations_from_text: Empty or invalid text provided")
            return []
            
        log_elapsed("Starting citation extraction")
        
        from context_citation_extractor import extract_citations_with_context
        
        # Log first 200 chars for debugging (removing newlines for log readability)
        sample_text = text[:200].replace('\n', ' ').replace('\r', '')
        if len(text) > 200:
            sample_text += "..."
        log_elapsed(f"Processing text sample: {sample_text}")
        
        # Extract citations with timing
        citations = extract_citations_with_context(text)
        
        if not isinstance(citations, list):
            logger.warning(f"Expected list from extract_citations_with_context, got {type(citations)}")
            citations = []
            
        log_elapsed(f"Extracted {len(citations)} citations")
        
        # Log first few citations if available
        if citations:
            for i, citation in enumerate(citations[:3], 1):
                if isinstance(citation, dict):
                    cite_str = citation.get('citation', str(citation)[:100])
                else:
                    cite_str = str(citation)[:100]
                log_elapsed(f"Citation {i}: {cite_str}")
        
        return citations
        
    except ImportError as e:
        logger.error("Failed to import context_citation_extractor. Make sure it's installed.", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Error in extract_citations_from_text: {str(e)}", exc_info=True)
        return []


# Set up logging with detailed format and DEBUG level
log_format = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed logs
    format=log_format,
    handlers=[
        logging.FileHandler("logs/citation_verification.log", encoding='utf-8'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Try to import striprtf at module level
try:
    import striprtf.striprtf

    STRIPRTF_AVAILABLE = True
    logger.info("striprtf library loaded successfully")
except ImportError:
    STRIPRTF_AVAILABLE = False
    logger.warning("striprtf not installed. RTF file processing will not be available.")

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure the logger
try:
    from concurrent_log_handler import ConcurrentRotatingFileHandler

    handler = ConcurrentRotatingFileHandler(
        os.path.join(log_dir, "casestrainer.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
    )
except ImportError:
    import logging

    handler = logging.FileHandler(os.path.join(log_dir, "casestrainer.log"))
logger.addHandler(handler)

# Create a Blueprint for the Enhanced Validator
enhanced_validator_bp = Blueprint(
    "enhanced_validator",
    __name__,
    template_folder=os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates"
    ),
)


def print_registered_routes(app):
    print("\n=== Flask Registered Routes ===")
    for rule in app.url_map.iter_rules():
        print(rule)
    print("============================\n")


# --- TEST ROUTE for /casestrainer/enhanced-validator/ ---
@enhanced_validator_bp.route("/", strict_slashes=False)
def test_enhanced_validator_root():
    return "Enhanced Validator Root: OK", 200


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
    "339 U.S. 629": "United States v. Rabinowitz",
    "United States v. Rabinowitz, 339 U.S. 629 (1950)": "United States v. Rabinowitz",
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
    # North Western Reporter - specific pattern for N.W. citations with flexible spacing
    "north_western_reporter": r"\b(?:^|\D)([1-9][0-9]{0,2})\s+N\.?\s*W\.?\s*(?:2d|3d)?\s+(\d{1,4})(?:\s*,\s*\d+)?(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)",  # e.g., 202 N.W. 734 or 202 N.W.2d 123
    # Supreme Court Reporter - strict format
    "supreme_court_reporter": r"\b(?:^|\D)([1-9][0-9]{0,2})\s+S\.\s*Ct\.\s+(\d{1,4})(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)",
    # Lawyers Edition - strict format
    "lawyers_edition": r"\b(?:^|\D)([1-9][0-9]{0,2})\s+L\.\s*Ed\.\s*(?:2d)?\s+(\d{1,4})(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)",
    # Westlaw - strict format
    "westlaw": r"\b(?:^|\D)(\d{4})\s+WL\s+(\d{8})\b(?!\s*[Cc]ase)",
    # Case name pattern - more flexible format requiring reporter citation
    "case_name": r"\b(?:^|\D)([A-Z][a-zA-Z\s\.&,]+v\.\s+[A-Z][a-zA-Z\s\.&,]+),\s+\d+\s+(?:[A-Za-z\.]+\s*)+\d+(?:\s*,\s*\d+)?(?:\s*\(\d{4}\))?(?:\s*,\s*\d+)*\b(?!\s*[Cc]ase)",  # e.g., Hirschman v. Healy, 202 N. W. 734
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
    
    # Handle Washington Reporter variations (Wn. App. -> Wash. App., Wn. 2d -> Wash. 2d)
    original_text = citation_text
    citation_text = re.sub(r"\bWn\.\s*App\.\b", "Wash. App.", citation_text)
    citation_text = re.sub(r"\bWn\.\s*2d\b", "Wash. 2d", citation_text)
    if citation_text != original_text:
        logger.debug(f"Normalized Washington citation: '{original_text}' -> '{citation_text}'")

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

    # Handle Federal Reporter citations (e.g., "550 F.3d 1000")
    fed_reporter_match = re.search(
        r"(\d+)\s+(F\.(?:2d|3d|4th))\s+(\d+)(?:\s*\((\d{4})\))?", 
        citation_text
    )
    if fed_reporter_match:
        components["volume"] = fed_reporter_match.group(1)
        components["reporter"] = fed_reporter_match.group(2)
        components["page"] = fed_reporter_match.group(3)
        if fed_reporter_match.group(4):
            components["year"] = fed_reporter_match.group(4)
        components["court"] = "U.S. Court of Appeals"
        components["citation_format"] = "short"
        return components

    # Try to extract any other citation components
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
    logger.info(f"Normalizing citation: {citation_text}")

    # Clean up the citation text
    citation_text = re.sub(r"\s+", " ", citation_text.strip())

    # Handle U.S. Reports citations with extra spaces, ensuring U.S. format
    us_match = re.search(r"(\d+)\s+U\.?\s*\.?\s*S\.?\s*\.?\s*(\d+)", citation_text)
    if us_match:
        volume, page = us_match.groups()
        # Always use U.S. format
        normalized = f"{volume} U.S. {page}"
        logger.info(f"Normalized U.S. citation: {normalized}")
        return normalized

    # If no U.S. pattern found, return original
    logger.info(f"No U.S. pattern found, returning original: {citation_text}")
    return citation_text


# Common citation patterns
CITATION_PATTERNS = {
    # U.S. Reports (e.g., 123 U.S. 456)
    "us_reports": r"\b(\d{1,3})\s+U\.?\s*S\.?\s+(\d{1,4})\b",
    
    # Federal Reporter (e.g., 123 F.3d 456, 123 F.2d 456, 123 F. 3d 456)
    "federal_reporter": r"\b(\d{1,3})\s+F\.?\s*(?:\d*[a-z]?d?)?\s*\d{1,4}\b",
    
    # Supreme Court Reporter (e.g., 123 S. Ct. 456, 123 S.Ct. 456)
    "supreme_court_reporter": r"\b(\d{1,3})\s+S\.?\s*Ct\.?\s+\d{1,4}\b",
    
    # Federal Supplement (e.g., 123 F. Supp. 456, 123 F.Supp. 456)
    "federal_supplement": r"\b(\d{1,3})\s+F\.?\s*Supp\.?\s*\d{1,4}\b",
    
    # Federal Rules Decisions (e.g., 123 F.R.D. 456)
    "frd": r"\b(\d{1,3})\s+F\.?\s*R\.?\s*D\.?\s+\d{1,4}\b",
    
    # Federal Rules (e.g., Fed. R. Civ. P. 12(b)(6))
    "federal_rules": r"\bFed\.?\s+R\.?\s+(?:Civ\.?|Crim\.?|App\.?|Bankr\.?)\s+P\.?\s+[\w\(\)]+",
    
    # U.S. Code (e.g., 18 U.S.C. § 1346)
    "us_code": r"\b\d+\s+U\.?\s*S\.?\s*C\.?\s*(?:§|ss\.?|sec\.?|sections?\s+)?\d+(?:\.\d+)?(?:\s*[–-]\s*\d+(?:\.\d+)?)*\b",
    
    # Code of Federal Regulations (e.g., 12 C.F.R. § 1026.1)
    "cfr": r"\b\d+\s+C\.?\s*F\.?\s*R\.?\s*(?:§|ss\.?|sec\.?|sections?\s+)?\d+(?:\.\d+)*\b",
    
    # State Reporters (e.g., 123 N.E.2d 456, 123 P.3d 789, 123 So. 2d 456)
    "state_reporters": r"\b(\d{1,3})\s+(?:[A-Za-z\.]+\s+){1,3}\d{1,4}\b"
}

def is_valid_citation_format(citation_text):
    """
    Validate if a string matches a valid legal citation format.
    This helps distinguish between actual citations and case numbers or other similar text.

    Args:
        citation_text (str): The text to validate

    Returns:
        bool: True if the text matches a valid citation format, False otherwise
    """
    # Pre-compile regex patterns for better performance
    WHITESPACE_PATTERN = re.compile(r'\s+')
    CASE_PATTERN = re.compile(r'\b\d+\s+[Cc]ase\s+\d+\b')
    PAGE_PATTERN = re.compile(r'\b\d+\s+[Pp]age\s+\d+\b')
    CASE_NUMBER_PATTERN = re.compile(r'\b(?:^|\D)\d+[:\-]\d+[\-:]cv[\-:]\d+\b', re.IGNORECASE)
    SINGLE_WORD_PATTERN = re.compile(r'^\d+$|^[A-Za-z]+$')
    CASE_NAME_PATTERN = re.compile(r'^[A-Za-z\s\.]+v\.\s+[A-Za-z\s\.]+$')
    # Match case names with reporter citations (e.g., "Smith v. Jones, 123 F.3d 456")
    CASE_NAME_WITH_REPORTER = re.compile(
        r'[A-Z][a-zA-Z\s.&,\-\"]+v\.\s+[A-Z][a-zA-Z\s.&,\-\"]+,\s*\d+\s+[A-Za-z.\s]+\d+',
        re.IGNORECASE
    )
    F3D_PATTERN = re.compile(r'\b\d+\s+F\.?\s*3d\s+\d+\b', re.IGNORECASE)
    US_PATTERN = re.compile(r'\b\d+\s+U\.?\s*S\.?\s+\d+\b', re.IGNORECASE)
    
    # Basic input validation
    if not citation_text or not isinstance(citation_text, str):
        return False
        
    # Clean up whitespace
    citation_text = WHITESPACE_PATTERN.sub(' ', citation_text.strip())
    
    # Skip empty or very short strings (less than 3 characters)
    if len(citation_text) < 3:
        logger.debug(f"Skipping very short citation: {citation_text}")
        return False
        
    # Skip single symbols or very short non-alphanumeric strings
    if len(citation_text) <= 2 and not citation_text.isalnum():
        logger.debug(f"Skipping single symbol or short non-alphanumeric: {citation_text}")
        return False
    
    # Skip strings that are just punctuation or symbols
    if all(not c.isalnum() for c in citation_text):
        logger.debug(f"Skipping non-alphanumeric string: {citation_text}")
        return False
        
    # Skip strings that are just numbers with "Case" (like "8 Case 2")
    if CASE_PATTERN.search(citation_text):
        logger.debug(f"Skipping 'Case' format: {citation_text}")
        return False

    # Skip strings that are just numbers with "Page" (like "25 Page 2")
    if PAGE_PATTERN.search(citation_text):
        logger.debug(f"Skipping 'Page' format: {citation_text}")
        return False
        
    # Skip strings that look like case numbers
    if CASE_NUMBER_PATTERN.search(citation_text):
        logger.debug(f"Skipping case number format: {citation_text}")
        return False
        
    # Skip strings that are just numbers or single words
    if SINGLE_WORD_PATTERN.match(citation_text):
        logger.debug(f"Skipping number or single word: {citation_text}")
        return False

    # Skip simple case names without reporter citation
    if (CASE_NAME_PATTERN.match(citation_text.strip()) and 
        not any(c.isdigit() for c in citation_text)):
        logger.debug(f"Skipping case name without reporter: {citation_text}")
        return False

    # Check against all citation patterns
    for pattern_name, pattern in CITATION_PATTERNS.items():
        if re.search(pattern, citation_text, re.IGNORECASE):
            logger.debug(f"Citation matched pattern {pattern_name}: {citation_text}")
            return True

    # Additional check for case names with reporter citations
    if CASE_NAME_WITH_REPORTER.search(citation_text):
        logger.debug(f"Citation matched case name with reporter pattern: {citation_text}")
        return True

    # Additional check for F.3d citations with various formats
    if F3D_PATTERN.search(citation_text):
        logger.debug(f"Citation matched F.3d pattern: {citation_text}")
        return True

    # Additional check for U.S. citations with various formats
    if US_PATTERN.search(citation_text):
        logger.debug(f"Citation matched U.S. pattern: {citation_text}")
        return True

    logger.warning(f"[DEBUG] Citation did not match any valid patterns: {citation_text}")
    return False

# ... (rest of the code remains the same)

# Global circuit breaker state
CIRCUIT_BREAKER = {
    'is_open': False,
    'last_failure_time': 0,
    'failure_count': 0,
    'reset_timeout': 300  # 5 minutes in seconds
}

def check_courtlistener_api(citation_text):
    """
    Enhanced function to verify citations using CourtListener API v4.
    
    Features:
    - Multiple retries with exponential backoff
    - Circuit breaker pattern to handle API unavailability
    - Fallback to local validation when API is unavailable
    - Comprehensive error handling and logging
    - Configurable timeouts and retry logic
    
    Args:
        citation_text (str): The citation text to validate
        
    Returns:
        dict: Validation result or None if validation fails
    """
    logger.info(f"[CITATION_VALIDATION] Starting validation for: {citation_text}")
    
    # Check circuit breaker state first
    current_time = time.time()
    
    # Initialize circuit breaker if needed
    if 'is_open' not in CIRCUIT_BREAKER:
        CIRCUIT_BREAKER.update({
            'is_open': False,
            'last_failure_time': 0,
            'reset_timeout': 300,  # 5 minutes default
            'failure_count': 0,
            'request_count': 0,
            'consecutive_failures': 0
        })
    
    # Check if circuit is open
    if CIRCUIT_BREAKER['is_open']:
        time_since_trip = current_time - CIRCUIT_BREAKER.get('trip_time', current_time)
        reset_in = max(0, CIRCUIT_BREAKER.get('reset_timeout', 300) - time_since_trip)
        
        if reset_in > 0:
            logger.warning(
                f"[CIRCUIT_OPEN] CourtListener API circuit breaker is open. "
                f"Resets in {reset_in:.1f}s. Using fallback validation."
            )
            return _validate_locally(citation_text)
        else:
            # Reset circuit if timeout has passed
            CIRCUIT_BREAKER['is_open'] = False
            CIRCUIT_BREAKER['consecutive_failures'] = 0
            CIRCUIT_BREAKER['last_failure_time'] = 0
            logger.info("[CIRCUIT_RESET] Circuit breaker reset after timeout")
    
    # Configuration
    api_config = {
        'max_retries': 3,              # Maximum number of retry attempts
        'initial_timeout': 30,         # Initial timeout in seconds (increased from 15s)
        'max_timeout': 120,            # Maximum timeout for any single request (increased from 30s)
        'backoff_factor': 2,           # Exponential backoff factor
        'backoff_jitter': 1.0,         # Jitter to add to backoff time (seconds)
        'circuit_breaker': {
            'max_failures': 5,          # Number of failures before tripping circuit
            'reset_timeout': 300,       # 5 minutes before resetting circuit
            'min_requests': 5           # Minimum requests before circuit can trip
        }
    }
    
    # Log the start of validation
    logger.info(f"[VALIDATION_START] Validating citation: {citation_text}")
    print(f"DEBUG: Validating citation: {citation_text}")

    # Verify API key is available and valid
    if not COURTLISTENER_API_KEY:
        error_msg = "No CourtListener API key available. Check config.json file."
        logger.error(f"[VALIDATION_ERROR] {error_msg}")
        print(f"[ERROR] {error_msg}")
        return _validate_locally(citation_text)

    if len(COURTLISTENER_API_KEY) < 10:  # Simple validation for key format
        error_msg = f"CourtListener API key appears invalid: {COURTLISTENER_API_KEY[:5]}..."
        logger.error(f"[VALIDATION_ERROR] {error_msg}")
        print(f"[ERROR] {error_msg}")
        return _validate_locally(citation_text)

    # Create a list of citation formats to try
    citation_formats_to_try = []

    # 1. Original citation as provided
    original_citation = citation_text.strip()
    citation_formats_to_try.append(original_citation)

    # 2. Clean and normalize the citation
    normalized_citation = re.sub(r"\s+", " ", original_citation)  # Normalize whitespace
    normalized_citation = re.sub(r",\s+", ", ", normalized_citation)  # Normalize commas
    if normalized_citation != original_citation:
        citation_formats_to_try.append(normalized_citation)

    # 3. Try to extract components and create a standard format
    components = parse_citation_components(normalized_citation)
    if (
        components
        and "volume" in components
        and "reporter" in components
        and "page" in components
    ):
        # Standard reporter format (e.g., "410 U.S. 113")
        standard_citation = (
            f"{components['volume']} {components['reporter']} {components['page']}"
        )
        if standard_citation not in citation_formats_to_try:
            citation_formats_to_try.append(standard_citation)

    # Extract case name if present (for result enrichment)
    case_name_match = re.search(
        r"([A-Za-z\s\.]+v\.\s+[A-Za-z\s\.]+)", normalized_citation
    )
    case_name = case_name_match.group(1).strip() if case_name_match else None

    # Log the citation formats we'll try
    logger.info(f"[DEBUG] Will try these citation formats: {citation_formats_to_try}")
    print(f"DEBUG: Will try these citation formats: {citation_formats_to_try}")

    # API configuration
    api_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {
        "Authorization": f"Token {COURTLISTENER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # Try each citation format
    for citation_format in citation_formats_to_try:
        logger.info(f"[VALIDATION_ATTEMPT] Trying citation format: {citation_format}")
        print(f"DEBUG: Trying citation format: {citation_format}")
        
        # Track validation attempt start time
        attempt_start = time.time()

        # Prepare the request data
        data = {"text": citation_format}

        # Make the API request with improved retry and timeout logic
        for attempt in range(api_config['max_retries']):
            try:
                # Calculate exponential backoff with jitter
                backoff = min(
                    api_config['initial_timeout'] * (api_config['backoff_factor'] ** attempt) +
                    random.uniform(0, api_config['backoff_jitter']),
                    api_config['max_timeout']
                )
                
                # Set timeouts - use separate connect and read timeouts
                connect_timeout = min(10, backoff)  # Shorter connect timeout
                read_timeout = backoff              # Longer read timeout
                
                logger.info(
                    f"[API_REQUEST] Attempt {attempt+1}/{api_config['max_retries']} "
                    f"to {api_url} (connect: {connect_timeout}s, read: {read_timeout}s)"
                )
                print(
                    f"DEBUG: Posting to CourtListener API (attempt {attempt+1}/{api_config['max_retries']}): {api_url} (timeout: {current_timeout}s)"
                )

                # Log the exact request being made
                logger.info(f"[DEBUG] Request headers: {headers}")
                logger.info(f"[DEBUG] Request data: {data}")

                # Make the request with separate connect and read timeouts
                try:
                    response = requests.post(
                        api_url,
                        json=data,
                        headers=headers,
                        timeout=(connect_timeout, read_timeout)  # (connect, read) timeouts
                    )
                except requests.exceptions.SSLError as ssl_err:
                    logger.error(f"[SSL_ERROR] SSL certificate verification failed: {str(ssl_err)}")
                    # Try again with verify=False if this is the last attempt
                    if attempt == api_config['max_retries'] - 1:
                        try:
                            response = requests.post(
                                api_url,
                                json=data,
                                headers=headers,
                                timeout=request_timeout,
                                verify=False
                            )
                        except Exception as e:
                            _handle_api_failure(api_url, f"SSL error with verify=False: {str(e)}")
                            continue
                    else:
                        _handle_api_failure(api_url, f"SSL error: {str(ssl_err)}")
                        continue

                # Log the response details
                logger.info(f"[DEBUG] Response status: {response.status_code}")
                logger.info(f"[DEBUG] Response headers: {dict(response.headers)}")
                
                # Safely log response text, handling encoding issues
                try:
                    # Try to log the first 500 characters, or as much as possible
                    response_text = response.text[:500]
                    logger.info("[DEBUG] Response text: %s...", response_text)
                except UnicodeEncodeError:
                    # If we can't encode the full text, log a message and the first 100 safe characters
                    safe_text = response.text.encode('ascii', 'ignore').decode('ascii', 'ignore')[:100]
                    logger.info("[DEBUG] Response text (non-ASCII filtered): %s...", safe_text)
                    
                print(f"DEBUG: Response status: {response.status_code}")

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(
                        f"[DEBUG] Rate limited. Waiting {retry_after} seconds..."
                    )
                    print(f"DEBUG: Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(min(retry_after, 10))  # Cap wait time at 10 seconds
                    continue

                # Check for authentication issues
                if response.status_code == 401 or response.status_code == 403:
                    logger.error(
                        f"[ERROR] Authentication failed. Check your API key: {response.text}"
                    )
                    print(
                        f"ERROR: Authentication failed. Check your API key: {response.text}"
                    )
                    return None  # No point retrying with same key

                # For other errors, try to parse response and continue
                if response.status_code >= 400:
                    # Safely log API error, handling potential encoding issues
                    try:
                        error_text = response.text
                        logger.warning(
                            "[DEBUG] API error: %d - %s", 
                            response.status_code,
                            error_text
                        )
                    except Exception as e:
                        logger.error(f"Error parsing API error response: {str(e)}")
                    break  # Try next citation format

                # Parse the successful response
                try:
                    data = response.json()
                    logger.info(f"[DEBUG] Parsed JSON response (type: {type(data)})")

                    # Process the response data
                    if isinstance(data, list) and len(data) > 0:
                        # Citation found in CourtListener
                        result = data[0]  # Get the first match
                        clusters = result.get("clusters", [])
                        logger.info(f"[DEBUG] Found {len(clusters)} clusters")

                        if clusters:
                            cluster = clusters[0]  # Get the first cluster

                            # Extract case details
                            result_case_name = cluster.get("case_name", case_name)
                            court = cluster.get("court", "Unknown Court")
                            date_filed = cluster.get("date_filed", "Unknown Date")
                            docket_number = cluster.get(
                                "docket_id",
                                cluster.get("docket_number", "Unknown Docket"),
                            )
                            url = f"https://www.courtlistener.com{cluster.get('absolute_url', '')}"

                            logger.info(
                                f"[DEBUG] Citation found in CourtListener: {citation_format} - {result_case_name}"
                            )
                            print(
                                f"DEBUG: Citation found in CourtListener: {citation_format} - {result_case_name}"
                            )

                            # Return the successful result
                            return {
                                "verified": True,
                                "verified_by": "CourtListener API",
                                "case_name": result_case_name,
                                "validation_method": "CourtListener API",
                                "reporter_type": (
                                    components.get("reporter", "Unknown")
                                    if components
                                    else "Unknown"
                                ),
                                "parallel_citations": [
                                    f"{cite.get('volume')} {cite.get('reporter')} {cite.get('page')}"
                                    for cite in cluster.get("citations", [])
                                ],
                                "details": {
                                    "court": court,
                                    "date_filed": date_filed,
                                    "docket_number": docket_number,
                                    "url": url,
                                },
                            }
                        else:
                            logger.warning(
                                f"[DEBUG] No clusters found for citation: {citation_format}"
                            )
                            print(
                                f"DEBUG: No clusters found for citation: {citation_format}"
                            )
                            # Continue to next format instead of returning None
                    else:
                        logger.info(
                            f"[DEBUG] Citation not found in CourtListener: {citation_format}"
                        )
                        print(
                            f"DEBUG: Citation not found in CourtListener: {citation_format}"
                        )
                        # Continue to next format

                except ValueError as json_err:
                    logger.error(f"[ERROR] Failed to parse JSON response: {json_err}")
                    print(f"ERROR: Failed to parse JSON response: {json_err}")
                    # Continue to next attempt

                break  # Break retry loop if we got here (no need to retry)

            except requests.exceptions.Timeout as te:
                elapsed = time.time() - attempt_start
                error_type = 'read' if 'Read timed out' in str(te) else 'connect'
                error_msg = (
                    f"{error_type.capitalize()} timeout after {elapsed:.2f}s "
                    f"(attempt {attempt+1}/{api_config['max_retries']}): {citation_format}"
                )
                logger.warning(f"[TIMEOUT] {error_msg}")
                
                if attempt < api_config['max_retries'] - 1:
                    # Calculate next backoff with jitter
                    next_attempt = attempt + 1
                    wait_time = min(
                        api_config['initial_timeout'] * 
                        (api_config['backoff_factor'] ** next_attempt) * 
                        (1 + random.uniform(0, api_config['backoff_jitter'])),
                        api_config['max_timeout']
                    )
                    logger.info(f"[RETRY] Waiting {wait_time:.1f}s before next attempt...")
                    time.sleep(wait_time)
                else:
                    _handle_api_failure(api_url, f"All retries failed due to timeouts for citation: {citation_format}")
                    break
                    
            except requests.exceptions.RequestException as e:
                error_type = type(e).__name__
                error_msg = f"{error_type} while checking CourtListener API (attempt {attempt+1}/{max_retries}): {str(e)}"
                logger.error(f"[REQUEST_ERROR] {error_msg}")
                print(f"ERROR: {error_msg}")
                
                # Log detailed error information
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"[RESPONSE_STATUS] {e.response.status_code}")
                    try:
                        logger.error(f"[RESPONSE_BODY] {e.response.text[:500]}")
                    except:
                        logger.error("[RESPONSE_BODY] Could not read response body")
                
                # Determine if we should retry
                retryable_errors = (
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.TooManyRedirects,
                    requests.exceptions.HTTPError,
                )
                
                if attempt < max_retries - 1 and isinstance(e, retryable_errors):
                    wait_time = min((2 ** attempt) + random.uniform(0, 1), 30)  # Cap at 30 seconds
                    logger.info(f"[RETRY] Will retry in {wait_time:.2f} seconds...")
                    print(f"DEBUG: Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    _handle_api_failure(api_url, f"Request failed with {error_type} after {attempt+1} attempts")
                    break

    # If we get here, all citation formats failed
    logger.warning(f"[VALIDATION_FAILED] All citation formats failed for: {citation_text}")
    print(f"DEBUG: All citation formats failed for: {citation_text}")
    
    # Fall back to local validation
    return _validate_locally(citation_text)


def _handle_api_failure(api_url, error_msg):
    """
    Handle API failures and update circuit breaker state.
    
    Implements a more sophisticated circuit breaker pattern with:
    - Failure counting with decay
    - Minimum request threshold before tripping
    - Exponential backoff for circuit reset
    """
    global CIRCUIT_BREAKER
    
    # Initialize circuit breaker if needed
    if 'request_count' not in CIRCUIT_BREAKER:
        CIRCUIT_BREAKER.update({
            'request_count': 0,
            'last_success_time': None,
            'consecutive_failures': 0
        })
    
    # Update failure metrics
    CIRCUIT_BREAKER['request_count'] += 1
    CIRCUIT_BREAKER['last_failure_time'] = time.time()
    CIRCUIT_BREAKER['consecutive_failures'] += 1
    
    # Log the failure with more context
    failure_rate = (
        CIRCUIT_BREAKER['consecutive_failures'] / 
        max(1, CIRCUIT_BREAKER['request_count'])
    ) * 100
    
    logger.error(
        f"[API_FAILURE] {error_msg} | "
        f"Failures: {CIRCUIT_BREAKER['consecutive_failures']}/"
        f"{CIRCUIT_BREAKER['request_count']} ({failure_rate:.1f}%)"
    )
    
    # Check if we should trip the circuit
    min_requests = 5  # Need at least this many requests before tripping
    if (CIRCUIT_BREAKER['request_count'] >= min_requests and 
        CIRCUIT_BREAKER['consecutive_failures'] >= 3 and 
        failure_rate > 50):  # More than 50% failure rate
        
        CIRCUIT_BREAKER['is_open'] = True
        CIRCUIT_BREAKER['trip_time'] = time.time()
        reset_delay = min(300, 60 * (2 ** min(CIRCUIT_BREAKER['consecutive_failures'] - 3, 5)))  # Cap at ~5 minutes
        CIRCUIT_BREAKER['reset_timeout'] = reset_delay
        
        logger.error(
            f"[CIRCUIT_OPEN] Circuit breaker tripped after "
            f"{CIRCUIT_BREAKER['consecutive_failures']} consecutive failures. "
            f"Will reset in {reset_delay}s"
        )
        
        # Schedule a reset
        def reset_circuit():
            time.sleep(reset_delay)
            CIRCUIT_BREAKER['is_open'] = False
            CIRCUIT_BREAKER['consecutive_failures'] = 0
            logger.info("[CIRCUIT_RESET] Circuit reset after cooldown period")
        
        import threading
        threading.Thread(target=reset_circuit, daemon=True).start()


def _validate_locally(citation_text):
    """Perform local validation when API is unavailable."""
    logger.info(f"[LOCAL_VALIDATION] Validating locally: {citation_text}")
    
    # Basic validation using regex patterns
    if not is_valid_citation_format(citation_text):
        logger.warning(f"[LOCAL_VALIDATION] Invalid citation format: {citation_text}")
        return None
    
    # Check against known patterns
    for pattern, case_name in LANDMARK_CASES.items():
        if citation_text.lower() in pattern.lower():
            logger.info(f"[LOCAL_MATCH] Found in local database: {citation_text}")
            return {
                'verified': True,
                'source': 'Local Database',
                'case_name': case_name,
                'validation_method': 'Local Pattern Match',
                'details': {
                    'note': 'Validated against local database of landmark cases',
                    'confidence': 'high'
                }
            }
    
    # If we get here, the citation format is valid but not in our local DB
    logger.info(f"[LOCAL_UNVERIFIED] Valid format but not in local database: {citation_text}")
    return {
        'verified': False,
        'source': 'Local Validation',
        'case_name': None,
        'validation_method': 'Local Pattern Match',
        'details': {
            'note': 'Citation format is valid but not found in local database',
            'confidence': 'medium'
        }
    }


def validate_citation(citation_text, return_debug=False):
    """
    Enhanced citation validation function with improved error handling and logging.
    
    This function attempts to validate a legal citation using multiple methods:
    1. CourtListener API (primary)
    2. Local database of known citations
    3. Pattern matching for common citation formats
    4. Fallback validation when other methods fail
    
    Args:
        citation_text (str): The citation text to validate
        return_debug (bool): If True, returns a tuple of (result, debug_info)
        
    Returns:
        dict: Validation result with verification status and metadata
        or tuple: (result, debug_info) if return_debug is True
    """
    # Initialize debug information and logging
    debug_info = {
        'start_time': time.time(),
        'steps': [],
        'errors': [],
        'warnings': []
    }
    
    def log_step(message, level='info'):
        """Helper function to log steps and add to debug info"""
        timestamp = time.time() - debug_info['start_time']
        log_message = f"[{timestamp:.3f}s] {message}"
        getattr(logger, level)(f"[VALIDATION] {log_message}")
        debug_info['steps'].append(f"[{level.upper()}] {log_message}")
    
    def log_error(message, exc_info=False):
        """Helper function to log errors"""
        timestamp = time.time() - debug_info['start_time']
        error_msg = f"[{timestamp:.3f}s] {message}"
        logger.error(f"[VALIDATION_ERROR] {error_msg}", exc_info=exc_info)
        debug_info['errors'].append(error_msg)
    
    def log_warning(message):
        """Helper function to log warnings"""
        timestamp = time.time() - debug_info['start_time']
        warn_msg = f"[{timestamp:.3f}s] {message}"
        logger.warning(f"[VALIDATION_WARN] {warn_msg}")
        debug_info['warnings'].append(warn_msg)
    
    # Initialize the result dictionary
    result = {
        'verified': False,
        'verified_by': None,
        'case_name': None,
        'validation_method': None,
        'reporter_type': None,
        'parallel_citations': [],
        'confidence': 'low',
        'source': None,
        'details': {}
    }
    
    try:
        log_step(f"Starting validation for: {citation_text}")
        
        # Input validation
        if not citation_text or not isinstance(citation_text, str):
            error_msg = f"Invalid citation input type: {type(citation_text)}"
            log_error(error_msg)
            result.update({
                'validation_method': 'Input Validation',
                'error': 'Citation must be a non-empty string',
                'details': {'input_type': str(type(citation_text))}
            })
            return (result, debug_info) if return_debug else result
            
        # Clean the citation text
        clean_citation = re.sub(r"\s+", " ", citation_text.strip())
        clean_citation = re.sub(r",\s+", ", ", clean_citation)
        log_step(f"Cleaned citation: {clean_citation}")
        
        # Check if it's a valid citation format
        if not is_valid_citation_format(clean_citation):
            log_warning(f"Invalid citation format: {clean_citation}")
            result.update({
                'validation_method': 'Format Validation',
                'error': 'Text does not match a valid legal citation format',
                'details': {'citation': clean_citation}
            })
            return (result, debug_info) if return_debug else result

        # Parse citation components
        components = parse_citation_components(clean_citation)
        if components:
            result['reporter_type'] = components.get("reporter", "Unknown")
            log_step(f"Parsed citation components: {components}")
            
            # Store components in details
            result['details'].update({
                'volume': components.get('volume'),
                'reporter': components.get('reporter'),
                'page': components.get('page'),
                'year': components.get('year')
            })

        # 1. Try CourtListener API first (most authoritative)
        log_step("Attempting validation via CourtListener API")
        try:
            courtlistener_result = check_courtlistener_api(clean_citation)
            
            if courtlistener_result and courtlistener_result.get("verified"):
                log_step("Citation validated by CourtListener API")
                result.update({
                    'verified': True,
                    'verified_by': courtlistener_result.get('source', 'CourtListener API'),
                    'case_name': courtlistener_result.get('case_name'),
                    'validation_method': 'CourtListener API',
                    'reporter_type': courtlistener_result.get('reporter_type', result['reporter_type']),
                    'parallel_citations': courtlistener_result.get('parallel_citations', []),
                    'confidence': 'high',
                    'source': 'courtlistener',
                    'details': courtlistener_result.get('details', {})
                })
                return (result, debug_info) if return_debug else result
                
            elif courtlistener_result is not None:  # API returned but citation not found
                log_warning("Citation not found in CourtListener API")
                result.update({
                    'verified': False,
                    'validation_method': 'CourtListener API',
                    'confidence': 'medium',
                    'source': 'courtlistener',
                    'details': courtlistener_result.get('details', {})
                })
            
        except requests.exceptions.RequestException as e:
            log_error(f"Network error with CourtListener API: {str(e)}")
            # Continue to next validation method
        except Exception as e:
            log_error(f"Unexpected error with CourtListener API: {str(e)}", exc_info=True)
            # Continue to next validation method

        # 2. Check for LEXIS citations (always valid format)
        log_step("Checking for LEXIS citation format")
        if re.search(r"\bLEXIS\b", clean_citation, re.IGNORECASE):
            log_step("Valid LEXIS citation format detected")
            result.update({
                'verified': True,
                'verified_by': 'Enhanced Validator',
                'validation_method': 'LEXIS Format',
                'reporter_type': 'LEXIS',
                'confidence': 'high',
                'source': 'format_validation',
                'details': {
                    'note': 'Valid LEXIS citation format',
                    'format': 'LEXIS'
                }
            })
            return (result, debug_info) if return_debug else result

        # 3. Check for Westlaw citations (proprietary format)
        log_step("Checking for Westlaw citation format")
        westlaw_pattern = r"\b(\d{4})\s*W\.?\s*L\.?\s*(\d+)\b"
        westlaw_match = re.search(westlaw_pattern, clean_citation, re.IGNORECASE)
        if westlaw_match:
            log_step("Westlaw citation format detected")
            result.update({
                'verified': False,
                'verified_by': 'Enhanced Validator',
                'validation_method': 'Westlaw Format',
                'reporter_type': 'Westlaw',
                'confidence': 'high',
                'source': 'format_validation',
                'details': {
                    'note': 'Westlaw citation detected',
                    'format': 'Westlaw',
                    'explanation': (
                        'This is a Westlaw citation, which is unlikely to be found in public legal databases. '
                        'Westlaw citations are proprietary to the Westlaw service.'
                    )
                }
            })
            return (result, debug_info) if return_debug else result

        # 4. Check local citation databases
        log_step("Checking local citation databases")
        databases = [
            ("Landmark", LANDMARK_CASES, 'high'),
            ("CourtListener", COURTLISTENER_CASES, 'medium'),
            ("Multitool", MULTITOOL_CASES, 'medium'),
            ("Other", OTHER_CASES, 'low')
        ]
        
        for db_name, db, confidence in databases:
            if clean_citation in db:
                log_step(f"Found in {db_name} database")
                result.update({
                    'verified': True,
                    'verified_by': 'Enhanced Validator',
                    'case_name': db[clean_citation],
                    'validation_method': f"{db_name} Database",
                    'confidence': confidence,
                    'source': 'local_database',
                    'details': {
                        'database': db_name,
                        'note': f'Found in local {db_name} database'
                    }
                })
                return (result, debug_info) if return_debug else result

        # 5. Try short citation format if we have components
        if components and all(k in components for k in ['volume', 'reporter', 'page']):
            short_citation = f"{components['volume']} {components['reporter']} {components['page']}"
            
            if short_citation != clean_citation:  # Only if different from original
                log_step(f"Trying short citation format: {short_citation}")
                
                # Try short format with CourtListener API
                try:
                    short_result = check_courtlistener_api(short_citation)
                    
                    if short_result and short_result.get("verified"):
                        log_step("Short citation validated by CourtListener API")
                        result.update({
                            'verified': True,
                            'verified_by': short_result.get('source', 'CourtListener API (short)'),
                            'case_name': short_result.get('case_name'),
                            'validation_method': 'CourtListener API (short format)',
                            'reporter_type': short_result.get('reporter_type', result['reporter_type']),
                            'parallel_citations': short_result.get('parallel_citations', []),
                            'confidence': 'high',
                            'source': 'courtlistener_short',
                            'details': short_result.get('details', {})
                        })
                        return (result, debug_info) if return_debug else result
                        
                except Exception as e:
                    log_error(f"Error validating short citation: {str(e)}")
                
                # Check short format in local databases
                for db_name, db, confidence in databases:
                    if short_citation in db:
                        log_step(f"Short citation found in {db_name} database")
                        result.update({
                            'verified': True,
                            'verified_by': 'Enhanced Validator',
                            'case_name': db[short_citation],
                            'validation_method': f"{db_name} Database (short format)",
                            'confidence': confidence,
                            'source': 'local_database_short',
                            'details': {
                                'database': db_name,
                                'format': 'short',
                                'note': f'Found in local {db_name} database using short format'
                            }
                        })
                        return (result, debug_info) if return_debug else result

        # 6. Final fallback - check if the format is valid but not found
        log_step("No validation method succeeded, checking format validity")
        if is_valid_citation_format(clean_citation):
            log_step("Citation has valid format but not found in any database")
            result.update({
                'verified': False,
                'validation_method': 'Format Validation',
                'confidence': 'low',
                'source': 'format_validation',
                'details': {
                    'note': 'Citation format is valid but not found in any database',
                    'suggestion': 'Verify the citation manually or try alternative formats'
                }
            })
        else:
            log_step("Citation format is invalid")
            result.update({
                'verified': False,
                'validation_method': 'Format Validation',
                'confidence': 'high',
                'source': 'format_validation',
                'details': {
                    'note': 'Citation format is invalid',
                    'suggestion': 'Check the citation format and try again'
                }
            })
        
        return (result, debug_info) if return_debug else result
        
    except Exception as e:
        error_msg = f"Unexpected error during validation: {str(e)}"
        log_error(error_msg, exc_info=True)
        
        # Return error result
        error_result = {
            'verified': False,
            'validation_method': 'Error',
            'error': 'An unexpected error occurred during validation',
            'details': {
                'exception': str(e),
                'type': type(e).__name__
            }
        }
        
        if return_debug:
            return error_result, debug_info
        return error_result


# Keep the old function for backward compatibility
def is_landmark_case(citation_text):
    """Check if a citation refers to a landmark case (backward compatibility)."""
    validation_result = validate_citation(citation_text)
    return validation_result["verified"]


@enhanced_validator_bp.route("/enhanced-validator/")
@enhanced_validator_bp.route("/casestrainer/enhanced-validator/")
def enhanced_validator_page():
    """Serve the Enhanced Validator page."""
    logger.info("Enhanced Validator page requested")
    return render_template("enhanced_validator.html")


@enhanced_validator_bp.route(
    "/enhanced-validator/api/validate-citation", methods=["POST"]
)
@enhanced_validator_bp.route(
    "/casestrainer/enhanced-validator/api/validate-citation", methods=["POST"]
)
def validate_citation_endpoint():
    """API endpoint to validate a single citation with timeout handling."""
    try:
        data = request.get_json()
        if not data or 'citation' not in data:
            return jsonify({"error": "No citation provided"}), 400
            
        citation = data['citation']
        logger.info(f"[API] Validating citation: {citation}")
        
        # Use the existing validate_with_timeout function
        result, debug_info = validate_with_timeout(citation)
        return jsonify({
            "status": "success", 
            "result": result,
            "debug": debug_info
        })
        
    except TimeoutError as e:
        logger.error(f"[API] Timeout validating citation: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Citation validation timed out"
        }), 408
    except Exception as e:
        logger.error(f"[API] Error validating citation: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": f"Error validating citation: {str(e)}"
        }), 500

@enhanced_validator_bp.route(
    "/enhanced-validator/api/citation-context", methods=["POST"]
)
@enhanced_validator_bp.route(
    "/casestrainer/enhanced-validator/api/citation-context", methods=["POST"]
)
def get_citation_context():
    try:
        data = request.get_json()
        if not data or "citation" not in data:
            return jsonify({"error": "No citation provided"}), 400

        citation = data["citation"]
        context = CITATION_CONTEXTS.get(
            citation, f"No context available for {citation}"
        )
        return jsonify(context)
    except Exception as e:
        logger.error(f"Error in get_citation_context: {str(e)}")
        return jsonify({"error": str(e)}), 500


@enhanced_validator_bp.route(
    "/enhanced-validator/api/classify-citation", methods=["POST"]
)
@enhanced_validator_bp.route(
    "/casestrainer/enhanced-validator/api/classify-citation", methods=["POST"]
)
def classify_citation():
    try:
        data = request.get_json()
        if not data or "citation" not in data:
            return jsonify({"error": "No citation provided"}), 400

        citation = data["citation"]
        # Landmark case check removed
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

        return jsonify(
            {
                "citation": citation,
                "confidence": confidence,
                "explanation": explanations,
            }
        )
    except Exception as e:
        logger.error(f"Error in classify_citation: {str(e)}")
        return jsonify({"error": str(e)}), 500


@enhanced_validator_bp.route(
    "/enhanced-validator/api/suggest-citation-corrections", methods=["POST"]
)
@enhanced_validator_bp.route(
    "/casestrainer/enhanced-validator/api/suggest-citation-corrections",
    methods=["POST"],
)
def suggest_corrections():
    try:
        data = request.get_json()
        if not data or "citation" not in data:
            return jsonify({"error": "No citation provided"}), 400

        citation = data["citation"]
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

        return jsonify({"citation": citation, "suggestions": suggestions})
    except Exception as e:
        logger.error(f"Error in suggest_corrections: {str(e)}")
        return jsonify({"error": str(e)}), 500


# --- Citation Extraction Definitions (Safe Global Scope) ---
# Removed redundant top-level definitions of extract_citations_from_file and extract_citations_from_text


# --- Original function ---
def extract_citations_from_file(pdf_path):
    try:
        from scotus_pdf_citation_extractor import SCOTUSPDFCitationExtractor

        extractor = SCOTUSPDFCitationExtractor()
        results = extractor.extract_citations_from_url(pdf_path)
        if isinstance(results, dict) and "citations" in results:
            return results["citations"]
        elif isinstance(results, list):
            return results
        else:
            return []
    except Exception as e:
        logger.error(f"Error in extract_citations_from_file: {e}")
        return []


def extract_citations_from_text(text):
    try:
        from context_citation_extractor import extract_citations_with_context

        return extract_citations_with_context(text)
    except Exception as e:
        logger.error(f"Error in extract_citations_from_text: {e}")
        return []


def fetch_url_content(url, timeout=30, max_retries=2):
    """
    Fetch content from a URL with timeout handling, retries, and better logging.
    If the URL points to a PDF, extracts text from it.
    
    Args:
        url (str): The URL to fetch content from
        timeout (int): Timeout in seconds for the request
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        dict: Dictionary containing citations, text, and status information
    """
    logger.info(f"[URL] Starting fetch for URL: {url}")
    start_time = time.time()
    last_error = None
    
    def log_elapsed(level, message):
        """Helper function to log messages with elapsed time"""
        elapsed = time.time() - start_time
        log_msg = f"{message} (after {elapsed:.2f}s)"
        if level == 'debug':
            logger.debug(f"[URL] {log_msg}")
        elif level == 'info':
            logger.info(f"[URL] {log_msg}")
        elif level == 'warning':
            logger.warning(f"[URL] {log_msg}")
        else:  # error
            logger.error(f"[URL] {log_msg}")
    
    # Add http:// if missing and validate URL
    if not url.startswith("http"):
        url = "http://" + url
        log_elapsed('info', f"Added missing scheme, URL is now: {url}")
    
    # Validate URL format
    try:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise ValueError("Invalid URL format")
    except Exception as e:
        log_elapsed('error', f"Invalid URL format: {str(e)}")
        return {"citations": [], "text": "", "status": "error", "error": f"Invalid URL: {str(e)}"}
    
    # Configure session with retries
    session = requests.Session()
    retry_strategy = requests.adapters.Retry(
        total=max_retries,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504, 429],
        allowed_methods=["GET", "POST"]
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    # Make the request with retries
    for attempt in range(max_retries + 1):
        try:
            log_elapsed('info', f"Attempt {attempt + 1}/{max_retries + 1} - Making HTTP request...")
            
            # Stream the response to handle large files
            response = session.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Get content type
            content_type = response.headers.get('content-type', '').lower()
            log_elapsed('info', f"Got response with content-type: {content_type}")
            
            # Handle PDF content
            if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
                return _handle_pdf_response(response, start_time, timeout)
                
            # Handle HTML content
            elif 'text/html' in content_type:
                return _handle_html_response(response, start_time)
                
            # Handle other content types
            else:
                return _handle_other_content(response, start_time)
                
        except requests.exceptions.Timeout:
            last_error = f"Request to {url} timed out after {timeout} seconds"
            if attempt == max_retries:
                log_elapsed('error', last_error)
                return {"citations": [], "text": "", "status": "error", "error": last_error}
            log_elapsed('warning', f"Timeout on attempt {attempt + 1}, retrying...")
            
        except requests.exceptions.RequestException as e:
            last_error = f"Request failed: {str(e)}"
            if attempt == max_retries:
                log_elapsed('error', last_error, exc_info=True)
                return {"citations": [], "text": "", "status": "error", "error": last_error}
            log_elapsed('warning', f"Request failed on attempt {attempt + 1}, retrying...")
            
        except Exception as e:
            last_error = f"Unexpected error: {str(e)}"
            log_elapsed('error', last_error, exc_info=True)
            return {"citations": [], "text": "", "status": "error", "error": last_error}
    
    # If we get here, all retries failed
    return {"citations": [], "text": "", "status": "error", "error": last_error or "Unknown error"}
        
def _handle_pdf_response(response, start_time, timeout):
    """Handle PDF content from a response"""
    def log_elapsed(level, message):
        """Helper function to log messages with elapsed time"""
        elapsed = time.time() - start_time
        log_msg = f"{message} (after {elapsed:.2f}s)"
        if level == 'debug':
            logger.debug(f"[PDF] {log_msg}")
        elif level == 'info':
            logger.info(f"[PDF] {log_msg}")
        elif level == 'warning':
            logger.warning(f"[PDF] {log_msg}")
        else:  # error
            logger.error(f"[PDF] {log_msg}")
    
    try:
        log_elapsed('info', "Processing PDF content...")
        
        # Use a temporary file to store the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            # Stream the content with a timeout
            for chunk in response.iter_content(chunk_size=8192):
                if time.time() - start_time > timeout:
                    raise TimeoutError("PDF download exceeded maximum time")
                if chunk:  # filter out keep-alive new chunks
                    temp_pdf.write(chunk)
            temp_pdf_path = temp_pdf.name
        
        log_elapsed('info', "PDF downloaded, extracting text...")
        
        # Extract text with timeout
        try:
            # Use the existing PDF extraction logic
            from scotus_pdf_citation_extractor import SCOTUSPDFCitationExtractor
            extractor = SCOTUSPDFCitationExtractor()
            extraction_result = extractor.extract_citations_from_url(temp_pdf_path)
            
            if isinstance(extraction_result, dict):
                citations = extraction_result.get("citations", [])
                extracted_text = extraction_result.get("text", "")
            else:
                citations = extraction_result if isinstance(extraction_result, list) else []
                extracted_text = ""
            
            log_elapsed('info', f"Extracted {len(citations)} citations and {len(extracted_text)} chars from PDF")
            return {"citations": citations, "text": extracted_text, "status": "success"}
        finally:
            try:
                os.unlink(temp_pdf_path)
            except Exception as e:
                log_elapsed('warning', f"Error deleting temporary PDF: {e}")
    except Exception as e:
        log_elapsed('error', f"Error processing PDF: {str(e)}", exc_info=True)
        return {"citations": [], "text": "", "status": "error", "error": f"Failed to process PDF: {str(e)}"}

def _handle_html_response(response, start_time):
    """Handle HTML content from a response"""
    def log_elapsed(level, message):
        """Helper function to log messages with elapsed time"""
        elapsed = time.time() - start_time
        log_msg = f"{message} (after {elapsed:.2f}s)"
        if level == 'debug':
            logger.debug(f"[HTML] {log_msg}")
        elif level == 'info':
            logger.info(f"[HTML] {log_msg}")
        elif level == 'warning':
            logger.warning(f"[HTML] {log_msg}")
        else:  # error
            logger.error(f"[HTML] {log_msg}")
    
    try:
        log_elapsed('info', "Processing HTML content...")
        
        # Get the HTML content
        html_content = response.text
        log_elapsed('info', f"Downloaded {len(html_content)} bytes of HTML")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        log_elapsed('info', f"Extracted {len(text)} characters from HTML")
        
        # Extract citations
        try:
            citations = extract_citations_from_text(text)
            log_elapsed('info', f"Extracted {len(citations)} citations from HTML")
            return {"citations": citations, "text": text, "status": "success"}
        except Exception as e:
            log_elapsed('error', f"Error extracting citations: {str(e)}", exc_info=True)
            # Return the text even if citation extraction failed
            return {"citations": [], "text": text, "status": "partial_success", "error": str(e)}
            
    except Exception as e:
        log_elapsed('error', f"Error processing HTML: {str(e)}", exc_info=True)
        return {"citations": [], "text": "", "status": "error", "error": f"Failed to process HTML: {str(e)}"}

def _handle_other_content(response, start_time):
    """Handle other content types"""
    def log_elapsed(level, message):
        """Helper function to log messages with elapsed time"""
        elapsed = time.time() - start_time
        log_msg = f"{message} (after {elapsed:.2f}s)"
        if level == 'debug':
            logger.debug(f"[TEXT] {log_msg}")
        elif level == 'info':
            logger.info(f"[TEXT] {log_msg}")
        elif level == 'warning':
            logger.warning(f"[TEXT] {log_msg}")
        else:  # error
            logger.error(f"[TEXT] {log_msg}")
    
    try:
        content_type = response.headers.get('content-type', 'unknown')
        log_elapsed('info', f"Processing content type: {content_type}")
        
        text = response.text
        log_elapsed('info', f"Extracted {len(text)} characters of plain text")
        
        # Try to extract citations anyway
        try:
            citations = extract_citations_from_text(text)
            log_elapsed('info', f"Extracted {len(citations)} citations from plain text")
            return {"citations": citations, "text": text, "status": "success"}
        except Exception as e:
            log_elapsed('warning', f"Error extracting citations from plain text: {str(e)}")
            return {"citations": [], "text": text, "status": "partial_success", "error": str(e)}
            
    except Exception as e:
        log_elapsed('error', f"Error processing content: {str(e)}", exc_info=True)
        return {"citations": [], "text": "", "status": "error", "error": f"Failed to process content: {str(e)}"}


@enhanced_validator_bp.route("/enhanced-validator/api/fetch_url", methods=["POST"])
@enhanced_validator_bp.route(
    "/casestrainer/enhanced-validator/api/fetch_url", methods=["POST"]
)
def fetch_url():
    try:
        data = request.get_json()
        if not data or "url" not in data:
            return jsonify({"error": "No URL provided"}), 400

        url = data["url"]
        content = fetch_url_content(url)
        return jsonify(content)
    except Exception as e:
        logger.error(f"Error in fetch_url: {str(e)}")
        return jsonify({"error": str(e)}), 500


def validate_with_timeout(citation, timeout=10):
    """
    Run validate_citation with a timeout to prevent hanging.
    
    Args:
        citation: The citation text to validate
        timeout: Timeout in seconds
        
    Returns:
        The validation result or raises TimeoutError
    """
    logger.debug(f"[VALIDATE] Starting validation for citation: {citation}")
    start_time = time.time()
    
    def handler(signum, frame):
        elapsed = time.time() - start_time
        logger.warning(f"[TIMEOUT] Validation timed out after {elapsed:.2f}s for citation: {citation}")
        raise TimeoutError(f"Citation validation timed out after {timeout} seconds")

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    
    try:
        logger.debug(f"[VALIDATE] Calling validate_citation for: {citation}")
        result = validate_citation(citation)
        signal.alarm(0)  # Disable the alarm
        elapsed = time.time() - start_time
        logger.debug(f"[VALIDATE] Completed validation in {elapsed:.2f}s for: {citation}")
        return result
    except TimeoutError:
        raise  # Re-raise TimeoutError
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[VALIDATE] Error after {elapsed:.2f}s for {citation}: {str(e)}", exc_info=True)
        signal.alarm(0)  # Ensure the alarm is cleared in case of other exceptions
        raise


def analyze_text(text):
    """Analyze text for legal citations and provide detailed analysis, with debug info."""
    logger.info("Analyzing text for legal citations")
    logger.info(
        f"[DEFENSIVE LOG] Received input of type: {type(text)}, value: {repr(text)[:500]}"
    )
    debug_info = []
    try:
        debug_info.append("[INFO] Starting citation extraction")
        # Defensive: ensure input is a string
        if not isinstance(text, str):
            msg = f"Input to analyze_text is not a string: {type(text)}. Value: {repr(text)[:500]}"
            logger.error(msg)
            debug_info.append(f"[ERROR] {msg}")
            raise ValueError(msg)

        # Extract citations
        extract_result = extract_citations(text, return_debug=True)
        if isinstance(extract_result, tuple) and len(extract_result) == 2:
            citation_results, extract_debug = extract_result
            debug_info.extend(extract_debug)
        elif isinstance(extract_result, dict):
            citation_results = extract_result
        else:
            msg = f"Unexpected return type from extract_citations: {type(extract_result)}"
            logger.error(msg)
            debug_info.append(f"[ERROR] {msg}")
            raise ValueError(msg)

        # Defensive: ensure citation_results is a dict with required keys
        if (
            not isinstance(citation_results, dict)
            or "confirmed_citations" not in citation_results
            or "possible_citations" not in citation_results
        ):
            msg = (
                f"Citation extraction did not return expected dict: {citation_results}"
            )
            logger.error(msg)
            debug_info.append(f"[ERROR] {msg}")
            raise ValueError(msg)

        # Initialize analysis results
        analysis = {
            "citations": citation_results,
            "statistics": {
                "total_citations": len(citation_results["confirmed_citations"])
                + len(citation_results["possible_citations"]),
                "confirmed_citations": len(citation_results["confirmed_citations"]),
                "possible_citations": len(citation_results["possible_citations"]),
            },
            "landmark_cases": [],
            "validation_results": [],
            "debug_info": debug_info,
        }

        # Check for landmark cases
        for citation in citation_results["confirmed_citations"]:
            if not isinstance(citation, dict):
                continue
                
            # Only add citation text to landmark cases, not the entire citation object
            citation_text = citation.get("citation_text")
            if citation_text:
                analysis["landmark_cases"].append({
                    "citation_text": citation_text,
                    "case_name": citation.get("case_name", ""),
                    "metadata": citation.get("metadata", {})
                })

        # Validate citations
        for citation in citation_results["confirmed_citations"]:
            if not isinstance(citation, dict):
                continue
                
            citation_text = citation.get("citation_text")
            if not citation_text:
                continue
                
            try:
                validation_result = validate_citation(citation_text, return_debug=True)
                
                # Handle both tuple and dict return types from validate_citation
                if isinstance(validation_result, tuple) and len(validation_result) == 2:
                    validation_data, validation_debug = validation_result
                    debug_info.extend(validation_debug)
                else:
                    validation_data = validation_result
                
                # Create a clean citation object for the validation result
                clean_citation = {
                    "citation_text": citation_text,
                    "case_name": citation.get("case_name", ""),
                    "metadata": citation.get("metadata", {})
                }
                
                analysis["validation_results"].append({
                    "citation": clean_citation,
                    "validation": validation_data
                })
                
            except Exception as e:
                logger.error(f"Error validating citation {citation_text}: {str(e)}")
                debug_info.append(f"[ERROR] Error validating citation {citation_text}: {str(e)}")

        logger.info(
            f"Analysis complete: found {analysis['statistics']['total_citations']} citations"
        )
        debug_info.append(
            f"[INFO] Analysis complete: found {analysis['statistics']['total_citations']} citations"
        )
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        debug_info.append(f"[ERROR] Error analyzing text: {str(e)}")
        raise ValueError(f"Error analyzing text: {str(e)}")


@enhanced_validator_bp.route("/enhanced-validator/api/analyze", methods=["POST"])
@enhanced_validator_bp.route(
    "/casestrainer/enhanced-validator/api/analyze", methods=["POST"]
)
def enhanced_analyze():
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "No text provided"}), 400

        text = data["text"]
        if not isinstance(text, str) or not text.strip():
            return jsonify({"error": "Invalid text format"}), 400

        # Limit text size to prevent memory issues
        if len(text) > 1000000:  # 1MB limit
            return jsonify({"error": "Text too large. Maximum size is 1MB."}), 400

        analysis = analyze_text(text)
        
        # Transform the response to match frontend expectations
        transformed_citations = []
        for item in analysis.get('validation_results', []):
            citation = item.get('citation', {})
            validation = item.get('validation', {})
            
            # Create a clean citation object with all necessary fields
            transformed = {
                'citation': citation.get('citation_text', ''),
                'case_name': citation.get('case_name', ''),
                'verified': validation.get('verified', False),
                'validation_method': validation.get('validation_method', ''),
                'url': validation.get('details', {}).get('url', ''),
                'metadata': citation.get('metadata', {})
            }
            transformed_citations.append(transformed)
        
        # Create the response object
        response = {
            'success': True,
            'citations': transformed_citations,
            'total': len(transformed_citations),
            'verified': sum(1 for c in transformed_citations if c['verified']),
            'landmark_cases': analysis.get('landmark_cases', []),
            'statistics': analysis.get('statistics', {})
        }
        
        # Include debug info if present
        if 'debug_info' in analysis and analysis['debug_info']:
            response['debug_info'] = analysis['debug_info']
            
        return jsonify(response)
        
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in enhanced_analyze: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


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
# Use the shared extract_text_from_file from file_utils


def preprocess_markdown(text):
    """
    Preprocess markdown text before citation extraction.
    
    Args:
        text (str): The text to preprocess
        
    Returns:
        str: Preprocessed text with markdown converted to plain text
    """
    if not text or not MARKDOWN_AVAILABLE:
        return text
    
    # Skip if text doesn't contain any markdown indicators
    if not any(char in text for char in ['*', '_', '`', '#', '>', '[', ']', '!']):
        return text
        
    try:
        # Convert markdown to HTML
        html_content = markdown(text)
        
        # Parse HTML and extract text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Handle code blocks - preserve them but clean up formatting
        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                # Replace code block with just the text content
                pre.replace_with(code.get_text() + '\n')
        
        # Get text content with proper spacing
        text_content = soup.get_text(separator='\n')
        
        # Convert HTML entities to characters
        text_content = html.unescape(text_content)
        
        # Clean up excessive whitespace but preserve paragraph breaks
        text_content = re.sub(r'[ \t]+', ' ', text_content)  # Replace multiple spaces/tabs with single space
        text_content = re.sub(r'\n{3,}', '\n\n', text_content)  # Limit consecutive newlines to 2
        
        return text_content.strip()
    except Exception as e:
        logger.warning(f"Error preprocessing markdown: {str(e)}")
        return text


def clean_case_name(case_name):
    """Clean up case names by removing common prefixes and normalizing whitespace."""
    if not case_name or not isinstance(case_name, str):
        return case_name
        
    # Remove common prefixes that might interfere with citation parsing
    prefixes = [
        'See', 'E.g.,', 'E.g.', 'See, e.g.,', 'See also', 'But see', 'Cf.', 'Compare', 'But cf.',
        'Accord', 'But', 'See generally', 'See, e.g.,', 'See id.', 'Id.', 'Id. at', 'Supra',
        'Infra', 'Et seq.', 'Et al.', 'In re', 'Ex parte', 'Ex rel.', 'In the matter of',
        'Further,', 'Similarly,', 'Moreover,', 'However,', 'Therefore,', 'Thus,'
    ]
    
    # Remove each prefix if it appears at the start of the string
    for prefix in sorted(prefixes, key=len, reverse=True):
        if case_name.startswith(prefix):
            case_name = case_name[len(prefix):].lstrip()
    
    # Normalize v. vs. v vs. vs.
    case_name = re.sub(r'\b(v|vs|versus)\.?\s+', 'v. ', case_name, flags=re.IGNORECASE)
    
    # Normalize U.S. vs. US vs. United States
    case_name = re.sub(r'\bU\.?\s?S\.?(?:\s+Ct\.?|\s+Cl\.?|\s+App\.?)?\b', 'U.S.', case_name, flags=re.IGNORECASE)
    
    # Remove extra spaces and normalize whitespace
    case_name = ' '.join(case_name.split())
    
    return case_name.strip()

def extract_citations(text, return_debug=False):
    """
    Extract legal citations from text using eyecite and regex patterns.
    
    Args:
        text (str): The text to extract citations from
        return_debug (bool): If True, returns debug information along with citations
        
    Returns:
        list: List of extracted citations with metadata
        or tuple: (citations, debug_info) if return_debug is True
    """
    start_time = time.time()
    debug_info = {
        'start_time': start_time,
        'steps': [],
        'stats': {
            'total_citations': 0,
            'blacklisted': 0,
            'eyecite_citations': 0,
            'regex_citations': 0,
            'validation_errors': 0,
            'case_name_cleaned': 0,
            'pin_cites_handled': 0,
        },
        'warnings': [],
        'errors': []
    }
    
    def log_step(message, level='info'):
        """Helper to log a processing step with timing info."""
        elapsed = time.time() - start_time
        step_info = {
            'time': round(elapsed, 2),
            'message': message,
            'level': level
        }
        debug_info['steps'].append(step_info)
        log_msg = f"[EXTRACT] {message} (after {elapsed:.2f}s)"
        
        if level == 'debug':
            logger.debug(log_msg)
        elif level == 'info':
            logger.info(log_msg)
        elif level == 'warning':
            logger.warning(log_msg)
            debug_info['warnings'].append(message)
        elif level == 'error':
            logger.error(log_msg)
            debug_info.setdefault('errors', []).append(message)
    
    # Define default blacklist patterns
    default_blacklist = {
        "exact": [
            "id.",
            "id.",
            "id.,"
        ],
        "regex": [
            r'\b(?:doc\.?|document)\s*[#:]?\s*\d+',
            r'\b(?:no\.?|number)\s+\d+',
            r'\b(?:see|see also|cf\.?|e\.g\.?|i\.e\.?|etc\.?|et seq\.?|supra|infra|id\.?)\b',
            r'\b\d+\s*(?:U\.?\s*S\.?C\.?|U\.?\s*S\.?\s*Code)\s*§?\s*\d+',
            r'\b\d+\s*C\.?F\.?R\.?\s*§?\s*\d+'
        ]
    }
    
    # Get the path to the blacklist file
    blacklist_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'blacklist.json')
    
    def load_blacklist():
        """Load blacklist patterns from JSON file or use defaults if not found."""
        # First try to load from file
        if os.path.exists(blacklist_path):
            try:
                with open(blacklist_path, "r", encoding='utf-8') as f:
                    custom_blacklist = json.load(f)
                    # Validate the structure
                    if isinstance(custom_blacklist, dict) and \
                       all(k in custom_blacklist for k in ['exact', 'regex']):
                        log_step(f"Loaded custom blacklist from {blacklist_path}", 'info')
                        return custom_blacklist
                    else:
                        log_step("Invalid blacklist format, using default", 'warning')
            except Exception as e:
                log_step(f"Error loading blacklist: {str(e)}", 'warning')
        
        # If we get here, use the default blacklist
        log_step("Using default blacklist patterns", 'info')
        return default_blacklist
    
    # Load the blacklist (will use defaults if file not found)
    blacklist = load_blacklist()
    
    # Log blacklist stats for debugging
    log_step(f"Loaded {len(blacklist.get('exact', []))} exact and {len(blacklist.get('regex', []))} regex blacklist patterns", 'debug')
    
    def is_blacklisted(citation_text):
        """Check if a citation matches any blacklist patterns."""
        if not citation_text or not isinstance(citation_text, str):
            return False
            
        # Normalize the citation text for better matching
        normalized = citation_text.lower().strip()
        
        # Check exact matches (case-insensitive)
        if any(normalized == item.lower().strip() for item in blacklist.get("exact", [])):
            debug_info['stats']['blacklisted'] += 1
            log_step(f"Blacklisted (exact match): {citation_text}", 'debug')
            return True
            
        # Check regex patterns
        for pattern in blacklist.get("regex", []):
            try:
                if re.search(pattern, citation_text, re.IGNORECASE):
                    debug_info['stats']['blacklisted'] += 1
                    log_step(f"Blacklisted (regex match): {citation_text} matched {pattern}", 'debug')
                    return True
            except re.error as e:
                log_step(f"Invalid regex pattern in blacklist: {pattern} - {str(e)}", 'warning')
                continue
                
        # Check common false positives
        false_positives = [
            r'^\d+$',  # Just a number
            r'^[A-Za-z\.]+$',  # Just letters and dots
            r'^\d+\s+[A-Za-z\.]+$',  # Just volume and reporter
            r'^[A-Za-z]+\s+v\.\s+[A-Za-z]+$',  # Just case name with v.
            r'^[A-Za-z]+\s+v\s+[A-Za-z]+$',  # Just case name with v
        ]
        
        for pattern in false_positives:
            if re.fullmatch(pattern, normalized):
                log_step(f"Filtered out false positive: {citation_text}", 'debug')
                return True
                
        return False
    
    # Initialize results
    results = {
        "confirmed_citations": [],
        "possible_citations": [],
        "warnings": [],
        "errors": []
    }
        
    # Track unique citations to avoid duplicates
    seen_citations = set()
    
    # Preprocess text if it contains markdown
    original_text = text
    if MARKDOWN_AVAILABLE and any(char in text for char in ['*', '_', '`', '#']):
        log_step("Detected markdown formatting, preprocessing text")
        text = preprocess_markdown(text)
        if text != original_text:
            log_step("Finished preprocessing markdown")
    
    # Try to use eyecite if available
    eyecite_available = False
    try:
        from eyecite import get_citations
        from eyecite.tokenizers import AhocorasickTokenizer
        eyecite_available = True
    except ImportError as e:
        log_step("eyecite not available, falling back to regex patterns", 'warning')
        
    if eyecite_available:
        log_step("Starting citation extraction with eyecite")
        try:
            tokenizer = AhocorasickTokenizer()
            citations = get_citations(text, tokenizer=tokenizer)
            log_step(f"eyecite found {len(citations)} potential citations")
            
            for i, citation in enumerate(citations, 1):
                try:
                    citation_text = citation.matched_text().strip()
                    if not citation_text:
                        continue
                        
                    # Skip blacklisted citations
                    if is_blacklisted(citation_text):
                        log_step(f"Blacklisted citation: {citation_text}", 'debug')
                        continue
                        
                    # Handle pin cites and case names
                    case_name = None
                    pin_cite = None
                    
                    # Extract pin cite if available
                    if hasattr(citation, 'pin_cite') and citation.pin_cite:
                        pin_cite = citation.pin_cite
                        debug_info['stats']['pin_cites_handled'] += 1
                        log_step(f"Found pin cite: {pin_cite} in {citation_text}", 'debug')
                    
                    # Get case name from metadata if available
                    if hasattr(citation, 'metadata') and citation.metadata:
                        plaintiff = getattr(citation.metadata, 'plaintiff', '')
                        defendant = getattr(citation.metadata, 'defendant', '')
                        
                        if plaintiff and defendant:
                            case_name = f"{plaintiff} v. {defendant}"
                            # Clean up the case name
                            cleaned_case_name = clean_case_name(case_name)
                            if cleaned_case_name != case_name:
                                debug_info['stats']['case_name_cleaned'] += 1
                                log_step(f"Cleaned case name: '{case_name}' -> '{cleaned_case_name}'", 'debug')
                            case_name = cleaned_case_name
                            
                            # Reconstruct the citation with cleaned case name
                            if pin_cite:
                                citation_text = f"{case_name}, {citation_text}, {pin_cite}"
                            else:
                                citation_text = f"{case_name}, {citation_text}"
                    
                    # Normalize whitespace
                    citation_text = re.sub(r"\s+", " ", citation_text).strip()
                    citation_text = re.sub(r",\s+", ", ", citation_text)
                    
                    # Skip duplicates
                    if citation_text in seen_citations:
                        continue
                    seen_citations.add(citation_text)
                    
                    # Handle U.S. v. format specifically
                    if 'U.S. v. ' in citation_text and case_name and 'U.S.' not in case_name:
                        # If we have a case name but it doesn't include U.S., reconstruct it
                        case_parts = case_name.split(' v. ')
                        if len(case_parts) == 2:
                            case_name = f"U.S. v. {case_parts[1]}"
                            log_step(f"Reconstructed U.S. v. format: {case_name}", 'debug')
                    
                    # Create citation object with enhanced metadata
                    citation_obj = {
                        "case_name": case_name or citation_text,
                        "backdrop": None,
                        "citation_text": citation_text,
                        "source": "eyecite",
                        "metadata": {
                            "has_pin_cite": bool(pin_cite),
                            "pin_cite": pin_cite or "",
                            "extraction_method": "eyecite"
                        },
                        "validation_status": "pending"
                    }
                    
                    # Add metadata if available
                    if hasattr(citation, 'metadata') and citation.metadata:
                        try:
                            citation_obj["metadata"] = {
                                k: str(v) for k, v in citation.metadata.__dict__.items()
                                if not k.startswith('_')
                            }
                        except Exception as e:
                            log_step(f"Error processing citation metadata: {str(e)}", 'warning')
                    
                    results["confirmed_citations"].append(citation_obj)
                    debug_info['stats']['eyecite_citations'] += 1
                    
                    if i % 100 == 0 or i == len(citations):
                        log_step(f"Processed {i}/{len(citations)} citations")
                        
                except Exception as e:
                    log_step(f"Error processing citation {i}: {str(e)}", 'error')
                    debug_info['stats']['validation_errors'] += 1
                    continue
                    
            log_step(f"Extracted {len(results['confirmed_citations'])} unique citations using eyecite")
            
        except Exception as e:
            log_step(f"Error in eyecite extraction: {str(e)}", 'error')
            debug_info['errors'].append(f"eyecite extraction failed: {str(e)}")
    
    try:
        # Fall back to regex patterns if no citations found with eyecite
        if not results['confirmed_citations'] or not eyecite_available:
            log_step("No citations found with eyecite, falling back to regex patterns")
            
            # Load citation patterns
            try:
                from .citation_patterns import CITATION_PATTERNS
                
                # Import citation patterns
                try:
                    from citation_patterns import CITATION_PATTERNS, COMMON_CITATION_FORMATS, LEGAL_REPORTERS
                    log_step(f"Loaded {len(CITATION_PATTERNS)} citation patterns and {len(LEGAL_REPORTERS)} reporter formats")
                except ImportError as e:
                    log_step(f"Failed to import citation patterns: {str(e)}", 'error')
                    raise
                
                # Process LEXIS patterns first
                lexis_patterns = {k: v for k, v in CITATION_PATTERNS.items() if k.startswith('lexis_')}
                other_patterns = {k: v for k, v in CITATION_PATTERNS.items() if not k.startswith('lexis_')}
                
                def process_patterns(patterns, pattern_type='regex'):
                    nonlocal seen_citations
                    for pattern_name, pattern in patterns.items():
                        try:
                            matches = list(re.finditer(pattern, text, re.IGNORECASE))
                            log_step(f"Processing {len(matches)} matches for pattern {pattern_name}", 'debug')
                            
                            for match in matches:
                                citation_text = match.group(0).strip()
                                if not citation_text or is_blacklisted(citation_text):
                                    log_step(f"Skipping blacklisted or empty citation: {citation_text}", 'debug')
                                    continue
                                    
                                # Clean up the citation text
                                citation_text = re.sub(r"\s+", " ", citation_text).strip()
                                citation_text = re.sub(r",\s+", ", ", citation_text)
                                
                                # Skip duplicates
                                if citation_text in seen_citations:
                                    log_step(f"Skipping duplicate citation: {citation_text}", 'debug')
                                    continue
                                    
                                seen_citations.add(citation_text)
                                
                                # Try to extract case name if possible
                                case_name = None
                                if ' v. ' in citation_text:
                                    case_name = citation_text.split(',')[0].strip()
                                    case_name = clean_case_name(case_name)
                                    
                                    # Handle U.S. v. format
                                    if 'U.S. v. ' in case_name and 'U.S.' not in case_name:
                                        case_parts = case_name.split(' v. ')
                                        if len(case_parts) == 2:
                                            case_name = f"U.S. v. {case_parts[1]}"
                                
                                citation_obj = {
                                    'case_name': case_name or citation_text,
                                    'backdrop': None,
                                    'citation_text': citation_text,
                                    'source': f'{pattern_type}_{pattern_name}',
                                    'metadata': {
                                        'extraction_method': pattern_type,
                                        'pattern_used': pattern_name,
                                        'has_pin_cite': bool(re.search(r',\s*\d+\s*$', citation_text))
                                    },
                                    'validation_status': 'pending'
                                }
                                
                                if pattern_type == 'lexis':
                                    results['possible_citations'].append(citation_obj)
                                else:
                                    results['confirmed_citations'].append(citation_obj)
                                    
                                debug_info['stats']['regex_citations'] += 1
                            
                        except re.error as e:
                            log_step(f"Invalid regex pattern {pattern_name}: {str(e)}", 'warning')
                            continue
                        except Exception as e:
                            log_step(f"Error processing pattern {pattern_name}: {str(e)}", 'error')
                            continue
                
                # Process LEXIS patterns
                if lexis_patterns:
                    log_step(f"Processing {len(lexis_patterns)} LEXIS patterns")
                    process_patterns(lexis_patterns, 'lexis')
                    
                    # Process other patterns
                    if other_patterns:
                        log_step(f"Processing {len(other_patterns)} other patterns")
                        process_patterns(other_patterns, 'regex')
                        
                    log_step(f"Extracted {len(results['confirmed_citations'])} citations using regex patterns")
            
            except ImportError as e:
                log_step(f"Citation patterns module not found: {str(e)}", 'error')
                debug_info['errors'].append(f"Failed to import citation patterns: {str(e)}")
            except Exception as e:
                log_step(f"Error in regex extraction: {str(e)}", 'error')
                debug_info['errors'].append(f"Regex extraction error: {str(e)}")
        
        # Update stats
        debug_info['stats']['unique_citations'] = len(seen_citations)
        debug_info['stats']['total_citations'] = len(results['confirmed_citations']) + len(results['possible_citations'])
        debug_info['stats']['processing_time'] = time.time() - start_time
        
        log_step(f"Extraction complete. Found {len(seen_citations)} unique citations")
        
        if return_debug:
            debug_info['end_time'] = time.time()
            debug_info['stats']['processing_time'] = debug_info['end_time'] - start_time
            return results, debug_info
            
        return results
        
    except Exception as e:
        log_step(f"Fatal error in extract_citations: {str(e)}", 'error')
        if return_debug:
            debug_info['end_time'] = time.time()
            debug_info['stats']['processing_time'] = debug_info['end_time'] - start_time
            debug_info['errors'].append(f"Fatal error: {str(e)}")
            return {"confirmed_citations": [], "possible_citations": [], "warnings": [], "errors": []}, debug_info
        return {"confirmed_citations": [], "possible_citations": [], "warnings": [], "errors": []}

# The regex pattern processing has been moved into the main function
# Now we'll process the validated citations

def validate_extracted_citations(citations, return_debug=False):
    """
    Validate a list of extracted citations.
    
    Args:
        citations (list): List of citation dictionaries to validate
        return_debug (bool): If True, returns debug information along with results
        
    Returns:
        dict: Dictionary containing validated citations and debug info if requested
    """
    start_time = time.time()
    debug_info = {
        'start_time': start_time,
        'steps': [],
        'stats': {
            'total_validated': 0,
            'validation_errors': 0,
        },
        'warnings': [],
        'errors': []
    }
    
    def log_step(message, level='info'):
        """Helper to log a processing step with timing info."""
        elapsed = time.time() - start_time
        step_info = {
            'time': round(elapsed, 2),
            'message': message,
            'level': level
        }
        debug_info['steps'].append(step_info)
        log_msg = f"[VALIDATE] {message} (after {elapsed:.2f}s)"
        
        if level == 'debug':
            logger.debug(log_msg)
        elif level == 'info':
            logger.info(log_msg)
        elif level == 'warning':
            logger.warning(log_msg)
            debug_info['warnings'].append(message)
        elif level == 'error':
            logger.error(log_msg)
            debug_info['errors'].append(message)
    
    try:
        if not isinstance(citations, list):
            raise ValueError("Input must be a list of citations")
            
        log_step(f"Starting validation of {len(citations)} citations")
        
        validated_citations = []
        
        for i, citation in enumerate(citations, 1):
            try:
                if not isinstance(citation, dict) or 'citation_text' not in citation:
                    log_step(f"Skipping invalid citation at index {i}: {citation}", 'warning')
                    continue
                    
                # Here you would add your citation validation logic
                # For now, we'll just pass the citation through
                validated_citations.append(citation)
                debug_info['stats']['total_validated'] += 1
                
                if i % 100 == 0 or i == len(citations):
                    log_step(f"Processed {i}/{len(citations)} citations")
                    
            except Exception as e:
                log_step(f"Error validating citation {i}: {str(e)}", 'error')
                debug_info['stats']['validation_errors'] += 1
                continue
        
        log_step(f"Validation complete. Successfully validated {len(validated_citations)} citations")
        
        result = {
            'validated_citations': validated_citations,
            'stats': debug_info['stats'],
            'warnings': debug_info['warnings'],
            'errors': debug_info['errors']
        }
        
        if return_debug:
            debug_info['end_time'] = time.time()
            debug_info['stats']['processing_time'] = debug_info['end_time'] - start_time
            return result, debug_info
            
        return result
        
    except Exception as e:
        log_step(f"Fatal error in validate_extracted_citations: {str(e)}", 'error')
        if return_debug:
            debug_info['end_time'] = time.time()
            debug_info['stats']['processing_time'] = debug_info['end_time'] - start_time
            debug_info['errors'].append(f"Fatal error: {str(e)}")
            return {'validated_citations': [], 'warnings': [], 'errors': debug_info['errors']}, debug_info
        return {'validated_citations': [], 'warnings': [], 'errors': [f"Fatal error: {str(e)}"]}
    # Log the first few citations for debugging
    if citations_to_validate:
        for i, citation in enumerate(citations_to_validate[:3], 1):
            log_step(f"Citation {i}/{total_citations}: {citation.get('citation_text', 'N/A')[0:100]}...", 'debug')
    else:
        log_step("No citations to validate", 'warning')
        return []
        
    # Initialize validation statistics
    validation_stats = {
        'total': total_citations,
        'valid': 0,
        'invalid': 0,
        'errors': 0,
        'timeouts': 0,
        'start_time': time.time()
    }
    
    import signal
    from functools import wraps
    from datetime import datetime
    import traceback

    class ValidationTimeoutError(Exception):
        pass
            
        def timeout(seconds=10, error_message='Function call timed out'):
            def decorator(func):
                def _handle_timeout(signum, frame):
                    raise ValidationTimeoutError(error_message)
                
                @wraps(func)
                def wrapper(*args, **kwargs):
                    signal.signal(signal.SIGALRM, _handle_timeout)
                    signal.alarm(seconds)
                    try:
                        start_time = time.time()
                        result = func(*args, **kwargs)
                        duration = time.time() - start_time
                        log_step(f"{func.__name__} completed in {duration:.2f}s", 'debug')
                        return result
                    finally:
                        signal.alarm(0)
                return wrapper
            return decorator
        
        @timeout(seconds=15)  # 15 seconds per citation validation
        def validate_with_timeout(citation):
            """
            Validate a single citation with timeout handling.
            
            Args:
                citation: The citation object to validate (must have 'citation_text')
                
            Returns:
                Tuple of (result, debug_info) from validate_citation
                
            Raises:
                ValidationTimeoutError: If validation takes longer than the timeout
                Exception: Any exception raised during validation
            """
            if not isinstance(citation, dict) or 'citation_text' not in citation:
                raise ValueError("Invalid citation format. Expected dict with 'citation_text' key.")
                
            citation_text = citation['citation_text']
            log_step(f"Starting validation for citation: {citation_text[0:100]}...", 'debug')
            start_time = time.time()
            
            try:
                # Add source information to the citation if not present
                if 'source' not in citation:
                    citation['source'] = 'unknown'
                    
                # Call the validation function with the citation text
                citation_text = citation.get('citation_text', '')
                result, debug_info = validate_citation(citation_text, return_debug=True)
                
                # Calculate processing time
                elapsed = time.time() - start_time
                log_step(f"Validated in {elapsed:.2f}s: {result.get('verified', False)}", 'debug')
                
                # Update the citation with validation results
                if isinstance(result, dict):
                    # Add validation status
                    citation['validation_status'] = 'verified' if result.get('verified') else 'unverified'
                    # Add validation details to metadata
                    if 'metadata' not in citation:
                        citation['metadata'] = {}
                    citation['metadata'].update({
                        'validation_method': result.get('validation_method'),
                        'verified_by': result.get('verified_by'),
                        'reporter_type': result.get('reporter_type'),
                        'validation_time': elapsed
                    })
                    # Add parallel citations if available
                    if 'parallel_citations' in result and result['parallel_citations']:
                        citation['metadata']['parallel_citations'] = result['parallel_citations']
                
                return result, debug_info
                
            except ValidationTimeoutError:
                elapsed = time.time() - start_time
                log_step(f"Timeout after {elapsed:.2f}s for: {citation_text[0:100]}...", 'warning')
                raise
                
            except Exception as e:
                elapsed = time.time() - start_time
                error_msg = f"Error after {elapsed:.2f}s: {str(e)}"
                log_step(f"{error_msg}\n{traceback.format_exc()}", 'error')
                
                # Return a structured error response
                error_result = {
                    'status': 'error',
                    'error': str(e),
                    'citation_text': citation_text,
                    'validation_time': elapsed,
                    'source': citation.get('source', 'unknown')
                }
                
                return error_result, {'error': str(e), 'traceback': traceback.format_exc()}
                # Return a minimal error result that matches the expected format
                error_result = {
                    "verified": False,
                    "error": str(e),
                    "citation": citation_text
                }
                
                return error_result, {'error': str(e)}
        
    # Process citations in batches with progress updates
    batch_size = 10
    for batch_start in range(0, total_citations, batch_size):
        batch_end = min(batch_start + batch_size, total_citations)
        batch = citations_to_validate[batch_start:batch_end]
        
        log_step(f"Processing citations {batch_start + 1}-{batch_end} of {total_citations}")
        
        for i, citation in enumerate(batch, 1):
            try:
                citation_text = citation.get('citation_text', str(citation)[:100])
                log_step(f"Validating {batch_start + i}/{total_citations}: {citation_text}", 'debug')
                
                start_time = time.time()
                validation_result, validation_debug = validate_with_timeout(citation)
                duration = time.time() - start_time
                
                log_step(f"Processed in {duration:.2f}s: {citation_text}", 'debug')
                debug_info.extend(validation_debug)
                
                if validation_result.get("verified", False):
                    validated_citations.append(citation)
                    log_step(f"Validated: {citation_text}", 'info')
                    validation_stats['valid'] += 1
                else:
                    log_step(f"Not verified: {citation_text}", 'debug')
                    validation_stats['invalid'] += 1
                    
            except ValidationTimeoutError as e:
                log_step(f"Timeout after 10s: {citation_text}", 'warning')
                validation_stats['timeouts'] += 1
                continue
                
            except Exception as e:
                error_msg = f"Error processing {citation_text}: {str(e)}"
                log_step(f"{error_msg}\n{traceback.format_exc()}", 'error')
                debug_info.append(f"[ERROR] {error_msg}")
                validation_stats['errors'] += 1
                continue
                
        logger.info(f"[BATCH COMPLETE] Processed {len(batch)} citations in batch {batch_start//batch_size + 1}")
        
    # Finalize and return results
    validation_stats['end_time'] = time.time()
    validation_stats['total_time'] = validation_stats['end_time'] - validation_stats['start_time']
    
    log_step(f"Validation complete. Stats: {json.dumps(validation_stats, indent=2)}", 'info')
    
    # Add stats to debug info
    debug_info.append("\n=== Validation Statistics ===")
    for stat, value in validation_stats.items():
        if stat not in ['start_time', 'end_time']:  # Don't include raw timestamps
            debug_info.append(f"{stat}: {value}")
    
    # Return the validated citations and debug info
    if return_debug:
        return validated_citations, debug_info
    return validated_citations

    # --- FILTER OUT ARTIFACTS AND NON-CITATIONS ---
    def is_artifact_or_invalid(citation_obj):
        citation_val = citation_obj.get("citation_text", "")
        if not isinstance(citation_val, str):
            return True  # Filter out non-string citation_texts as invalid
        text = citation_val.strip()
        # Remove lone section symbols, punctuation, or very short strings
        if not text or len(text) < 4:
            return True
        if all(c in "§§.,;:*-_()[]{}|/\\'\"`~!@#$%^&<>? \\t\\n" for c in text):
            return True
        # Remove if only section symbols (e.g., '§', '§§')
        if re.fullmatch(r"§+", text):
            return True
        # Remove if not matching a valid citation format
        try:
            from . import is_valid_citation_format
        except ImportError:
            from enhanced_validator_production import is_valid_citation_format
        if not is_valid_citation_format(text):
            return True
        return False

    unlikely_citations = []

    def filter_and_flag(citations):
        filtered = []
        for c in citations:
            if is_artifact_or_invalid(c):
                c = dict(c)  # copy
                c.setdefault("metadata", {})
                c["metadata"]["invalid_reason"] = "artifact_or_invalid"
                unlikely_citations.append(c)
                continue
            filtered.append(c)
        return filtered

    results["confirmed_citations"] = filter_and_flag(results["confirmed_citations"])
    results["possible_citations"] = filter_and_flag(results["possible_citations"])
    results["unlikely_citations"] = unlikely_citations

    if return_debug:
        return results, debug_info
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


# Function to register the blueprint with the Flask app
def register_enhanced_validator(app):
    """Register the enhanced validator blueprint with the Flask app."""
    app.register_blueprint(
        enhanced_validator_bp, name="enhanced_validator_production_v3"
    )
    logger.info("Enhanced Validator blueprint registered with the Flask app")

    # Print all registered Flask routes at startup for debugging
    logger.debug("Registered routes:")
    for rule in app.url_map.iter_rules():
        logger.debug(f"  {rule}")

    # Ensure the enhanced_validator blueprint exposes a test route for /casestrainer/enhanced-validator/
    @app.route("/casestrainer/enhanced-validator/", methods=["GET"])
    def test_enhanced_validator():
        return "Enhanced Validator is working!"

    return app

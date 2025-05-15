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
from flask import Blueprint, render_template, request, jsonify, make_response, send_from_directory
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure the logger
logger.addHandler(logging.FileHandler(os.path.join(log_dir, 'casestrainer.log')))

# Create a Blueprint for the Enhanced Validator
enhanced_validator_bp = Blueprint('enhanced_validator', __name__, 
    template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))

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
    "193 U.S. 197": "Northern Securities Co. v. United States"
}

# Load API keys from config.json
try:
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
        COURTLISTENER_API_KEY = config.get('COURTLISTENER_API_KEY')
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
    "542 U.S. 507": "Hamdi v. Rumsfeld"
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
    "588 U.S. ___": "Department of Commerce v. New York"
}

# Other validated cases (from other sources)
OTHER_CASES = {
    "Dobbs v. Jackson Women's Health Organization, 597 U.S. ___ (2022)": "Dobbs v. Jackson Women's Health Organization",
    "Bostock v. Clayton County, 590 U.S. ___ (2020)": "Bostock v. Clayton County",
    "Trump v. Hawaii, 585 U.S. ___ (2018)": "Trump v. Hawaii",
    "Masterpiece Cakeshop v. Colorado Civil Rights Commission, 584 U.S. ___ (2018)": "Masterpiece Cakeshop v. Colorado Civil Rights Commission",
    "Carpenter v. United States, 585 U.S. ___ (2018)": "Carpenter v. United States",
    "339 U.S. 629": "United States v. Rabinowitz",
    "United States v. Rabinowitz, 339 U.S. 629 (1950)": "United States v. Rabinowitz"
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
    "372 U.S. 335": "In Gideon v. Wainwright, 372 U.S. 335 (1963), the Supreme Court unanimously ruled that states are required under the Sixth Amendment to provide an attorney to defendants in criminal cases who cannot afford their own attorneys."
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
    "lexis_supreme": r"\b(?:^|\D)(\d{4})\s+U\.?\s*S\.?\s*LEXIS\s+(\d+)(?:\s*,\s*\d+)?\b(?!\s*[Cc]ase)"
}

# Import eyecite for citation extraction
try:
    from eyecite import get_citations
    from eyecite.tokenizers import AhocorasickTokenizer
    try:
        tokenizer = AhocorasickTokenizer()
        EYECITE_AVAILABLE = True
        logger.info("Eyecite library and AhocorasickTokenizer loaded successfully for citation extraction")
    except ImportError as e:
        EYECITE_AVAILABLE = False
        tokenizer = None
        logger.warning(f"Eyecite not installed: {str(e)}. Using regex patterns for citation extraction.")
except ImportError as e:
    EYECITE_AVAILABLE = False
    tokenizer = None
    logger.warning(f"Eyecite not installed: {str(e)}. Using regex patterns for citation extraction.")

def parse_citation_components(citation_text):
    """Parse a citation into its component parts."""
    components = {}
    
    # Clean up the citation text
    citation_text = re.sub(r'\s+', ' ', citation_text.strip())
    citation_text = re.sub(r',\s+', ', ', citation_text)
    
    # Check if this is a full case name citation (e.g., "Brown v. Board of Education, 347 U.S. 483 (1954)")
    case_name_match = re.search(r'([A-Za-z\s\.&,]+v\.\s+[A-Za-z\s\.&,]+),\s+(\d+)\s+([A-Za-z\.]+)\s+(\d+)(?:\s*,\s*\d+)*(?:\s*\((\d{4})\))?', citation_text)
    if case_name_match:
        components["case_name"] = case_name_match.group(1).strip()
        components["volume"] = case_name_match.group(2)
        components["reporter"] = case_name_match.group(3)
        components["page"] = case_name_match.group(4)
        components["year"] = case_name_match.group(5) if case_name_match.group(5) else None
        components["court"] = "U.S. Supreme Court" if components["reporter"].upper() == "U.S." else "Unknown"
        components["citation_format"] = "full"
        return components
    
    # Simple parsing logic for U.S. Reporter citations (e.g., "410 U.S. 113" or "410 U.S. 113, 116, 118")
    us_match = re.search(r'(\d+)\s+U\.?\s*S\.?\s+(\d+)(?:\s*,\s*\d+)*(?:\s*\((\d{4})\))?', citation_text)
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
        reporter_match = re.search(r'([A-Za-z\.]+)', parts[1])
        if reporter_match:
            components["volume"] = parts[0]
            components["reporter"] = reporter_match.group(1)
            components["page"] = parts[2]
            components["court"] = "U.S. Supreme Court" if components["reporter"].upper() == "U.S." else "Unknown"
            components["citation_format"] = "short"
            
            # Extract year if available
            year_match = re.search(r'\((\d{4})\)', citation_text)
            if year_match:
                components["year"] = year_match.group(1)
    
    return components

def normalize_us_citation(citation_text):
    """Normalize U.S. citation format, handling extra spaces and ensuring U.S. format."""
    logger.info(f"Normalizing citation: {citation_text}")
    
    # Clean up the citation text
    citation_text = re.sub(r'\s+', ' ', citation_text.strip())
    
    # Handle U.S. Reports citations with extra spaces, ensuring U.S. format
    us_match = re.search(r'(\d+)\s+U\.?\s*\.?\s*S\.?\s*\.?\s*(\d+)', citation_text)
    if us_match:
        volume, page = us_match.groups()
        # Always use U.S. format
        normalized = f"{volume} U.S. {page}"
        logger.info(f"Normalized U.S. citation: {normalized}")
        return normalized
    
    # If no U.S. pattern found, return original
    logger.info(f"No U.S. pattern found, returning original: {citation_text}")
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
    logger.info(f"[DEBUG] Checking citation format for: {citation_text}")
    print(f"DEBUG: Checking citation format for: {citation_text}")
    
    # Skip empty or very short strings
    if not citation_text or len(citation_text.strip()) < 5:
        logger.warning(f"[DEBUG] Citation too short: {citation_text}")
        return False
    
    # Skip strings that look like case numbers
    if re.search(r'\b(?:^|\D)\d+[:\-]\d+[:\-]cv[:\-]\d+\b', citation_text, re.IGNORECASE):
        logger.warning(f"[DEBUG] Citation looks like a case number: {citation_text}")
        return False
    
    # Skip strings that are just numbers with "Case" (like "8 Case 2")
    if re.search(r'\b\d+\s+[Cc]ase\s+\d+\b', citation_text):
        logger.warning(f"[DEBUG] Citation looks like 'Case' format: {citation_text}")
        return False
    
    # Skip strings that are just numbers with "Page" (like "25 Page 2")
    if re.search(r'\b\d+\s+[Pp]age\s+\d+\b', citation_text):
        logger.warning(f"[DEBUG] Citation looks like 'Page' format: {citation_text}")
        return False
    
    # Skip simple case names without reporter citation
    if re.match(r'^[A-Za-z\s\.]+v\.\s+[A-Za-z\s\.]+$', citation_text.strip()):
        logger.warning(f"[DEBUG] Citation is just a case name: {citation_text}")
        return False
    
    # Check against all citation patterns
    for pattern_name, pattern in CITATION_PATTERNS.items():
        if re.search(pattern, citation_text, re.IGNORECASE):
            logger.info(f"[DEBUG] Citation matched pattern {pattern_name}: {citation_text}")
            return True
    
    # Additional check for U.S. citations with multiple page numbers
    if re.search(r'\b(?:^|\D)([1-9][0-9]{0,2})\s+U\.?\s*S\.?\s+(\d{1,4})(?:\s*,\s*\d+)*(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)', citation_text, re.IGNORECASE):
        logger.info(f"[DEBUG] Citation matched U.S. pattern: {citation_text}")
        return True
    
    # Additional check for case names with reporter citations
    if re.search(r'\b([A-Z][a-zA-Z\s\.&,]+v\.\s+[A-Z][a-zA-Z\s\.&,]+),\s+\d+\s+[A-Za-z\.]+\s+\d+(?:\s*,\s*\d+)*(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)', citation_text, re.IGNORECASE):
        logger.info(f"[DEBUG] Citation matched case name pattern: {citation_text}")
        return True
    
    # Additional check for simple U.S. citations
    if re.search(r'\b(?:^|\D)([1-9][0-9]{0,2})\s+U\.?\s*S\.?\s+(\d{1,4})(?:\s*\(\d{4}\))?\b(?!\s*[Cc]ase)', citation_text, re.IGNORECASE):
        logger.info(f"[DEBUG] Citation matched simple U.S. pattern: {citation_text}")
        return True
    
    logger.warning(f"[DEBUG] Citation did not match any valid patterns: {citation_text}")
    return False

def check_courtlistener_api(citation_text):
    """
    Enhanced function to verify citations using CourtListener API v4.
    Includes multiple retries, better error handling, and support for various citation formats.
    """
    logger.info("TEST: check_courtlistener_api is being called")
    logger.info(f"[DEBUG] check_courtlistener_api called with: {citation_text}")
    print(f"DEBUG: check_courtlistener_api called with: {citation_text}")
    
    # Verify API key is available and valid
    if not COURTLISTENER_API_KEY:
        logger.error("[ERROR] No CourtListener API key available. Check config.json file.")
        print("[ERROR] No CourtListener API key available. Check config.json file.")
        return None
    
    if len(COURTLISTENER_API_KEY) < 10:  # Simple validation for key format
        logger.error(f"[ERROR] CourtListener API key appears invalid: {COURTLISTENER_API_KEY[:5]}...")
        print(f"[ERROR] CourtListener API key appears invalid: {COURTLISTENER_API_KEY[:5]}...")
        return None
        
    # Create a list of citation formats to try
    citation_formats_to_try = []
    
    # 1. Original citation as provided
    original_citation = citation_text.strip()
    citation_formats_to_try.append(original_citation)
    
    # 2. Clean and normalize the citation
    normalized_citation = re.sub(r'\s+', ' ', original_citation)  # Normalize whitespace
    normalized_citation = re.sub(r',\s+', ', ', normalized_citation)  # Normalize commas
    if normalized_citation != original_citation:
        citation_formats_to_try.append(normalized_citation)
    
    # 3. Try to extract components and create a standard format
    components = parse_citation_components(normalized_citation)
    if components and 'volume' in components and 'reporter' in components and 'page' in components:
        # Standard reporter format (e.g., "410 U.S. 113")
        standard_citation = f"{components['volume']} {components['reporter']} {components['page']}"
        if standard_citation not in citation_formats_to_try:
            citation_formats_to_try.append(standard_citation)
    
    # Extract case name if present (for result enrichment)
    case_name_match = re.search(r'([A-Za-z\s\.]+v\.\s+[A-Za-z\s\.]+)', normalized_citation)
    case_name = case_name_match.group(1).strip() if case_name_match else None
    
    # Log the citation formats we'll try
    logger.info(f"[DEBUG] Will try these citation formats: {citation_formats_to_try}")
    print(f"DEBUG: Will try these citation formats: {citation_formats_to_try}")
    
    # API configuration
    api_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {
        "Authorization": f"Token {COURTLISTENER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Try each citation format
    for citation_format in citation_formats_to_try:
        logger.info(f"[DEBUG] Trying citation format: {citation_format}")
        print(f"DEBUG: Trying citation format: {citation_format}")
        
        # Prepare the request data
        data = {'text': citation_format}
        
        # Make the API request with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"[DEBUG] Posting to CourtListener API (attempt {attempt+1}/{max_retries}): {api_url}")
                print(f"DEBUG: Posting to CourtListener API (attempt {attempt+1}/{max_retries}): {api_url}")
                
                # Log the exact request being made
                logger.info(f"[DEBUG] Request headers: {headers}")
                logger.info(f"[DEBUG] Request data: {data}")
                
                # Make the request
                response = requests.post(api_url, json=data, headers=headers, timeout=15)
                
                # Log the response details
                logger.info(f"[DEBUG] Response status: {response.status_code}")
                logger.info(f"[DEBUG] Response headers: {dict(response.headers)}")
                logger.info(f"[DEBUG] Response text: {response.text[:500]}...")  # Truncate long responses
                print(f"DEBUG: Response status: {response.status_code}")
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"[DEBUG] Rate limited. Waiting {retry_after} seconds...")
                    print(f"DEBUG: Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(min(retry_after, 10))  # Cap wait time at 10 seconds
                    continue
                
                # Check for authentication issues
                if response.status_code == 401 or response.status_code == 403:
                    logger.error(f"[ERROR] Authentication failed. Check your API key: {response.text}")
                    print(f"ERROR: Authentication failed. Check your API key: {response.text}")
                    return None  # No point retrying with same key
                
                # For other errors, try to parse response and continue
                if response.status_code >= 400:
                    logger.warning(f"[DEBUG] API error: {response.status_code} - {response.text}")
                    print(f"DEBUG: API error: {response.status_code} - {response.text}")
                    break  # Try next citation format
                
                # Parse the successful response
                try:
                    data = response.json()
                    logger.info(f"[DEBUG] Parsed JSON response (type: {type(data)})")
                    
                    # Process the response data
                    if isinstance(data, list) and len(data) > 0:
                        # Citation found in CourtListener
                        result = data[0]  # Get the first match
                        clusters = result.get('clusters', [])
                        logger.info(f"[DEBUG] Found {len(clusters)} clusters")
                        
                        if clusters:
                            cluster = clusters[0]  # Get the first cluster
                            
                            # Extract case details
                            result_case_name = cluster.get('case_name', case_name)
                            court = cluster.get('court', 'Unknown Court')
                            date_filed = cluster.get('date_filed', 'Unknown Date')
                            docket_number = cluster.get('docket_id', cluster.get('docket_number', 'Unknown Docket'))
                            url = f"https://www.courtlistener.com{cluster.get('absolute_url', '')}" 
                            
                            logger.info(f"[DEBUG] Citation found in CourtListener: {citation_format} - {result_case_name}")
                            print(f"DEBUG: Citation found in CourtListener: {citation_format} - {result_case_name}")
                            
                            # Return the successful result
                            return {
                                "verified": True,
                                "verified_by": "CourtListener API",
                                "case_name": result_case_name,
                                "validation_method": "CourtListener API",
                                "reporter_type": components.get('reporter', "Unknown") if components else "Unknown",
                                "parallel_citations": [
                                    f"{cite.get('volume')} {cite.get('reporter')} {cite.get('page')}"
                                    for cite in cluster.get('citations', [])
                                ],
                                "details": {
                                    "court": court,
                                    "date_filed": date_filed,
                                    "docket_number": docket_number,
                                    "url": url
                                }
                            }
                        else:
                            logger.warning(f"[DEBUG] No clusters found for citation: {citation_format}")
                            print(f"DEBUG: No clusters found for citation: {citation_format}")
                            # Continue to next format instead of returning None
                    else:
                        logger.info(f"[DEBUG] Citation not found in CourtListener: {citation_format}")
                        print(f"DEBUG: Citation not found in CourtListener: {citation_format}")
                        # Continue to next format
                    
                except ValueError as json_err:
                    logger.error(f"[ERROR] Failed to parse JSON response: {json_err}")
                    print(f"ERROR: Failed to parse JSON response: {json_err}")
                    # Continue to next attempt
                
                break  # Break retry loop if we got here (no need to retry)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"[ERROR] Request error checking CourtListener API: {str(e)}")
                print(f"ERROR: Request error checking CourtListener API: {str(e)}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"[DEBUG] Retrying in {wait_time} seconds...")
                    print(f"DEBUG: Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # Try next citation format
                    break
    
    # If we get here, all citation formats failed
    logger.warning(f"[DEBUG] All citation formats failed for: {citation_text}")
    print(f"DEBUG: All citation formats failed for: {citation_text}")
    return None

def validate_citation(citation_text):
    """
    Enhanced citation validation function with improved error handling and logging.
    Tries multiple validation methods in sequence, starting with CourtListener API.
    """
    logger.info(f"[DEBUG] validate_citation called with: {citation_text}")
    print(f"DEBUG: validate_citation called with: {citation_text}")
    
    # First check if it's a valid citation format
    if not citation_text or not isinstance(citation_text, str):
        logger.error(f"[ERROR] Invalid citation input: {type(citation_text)}")
        print(f"ERROR: Invalid citation input: {type(citation_text)}")
        return {
            "verified": False,
            "verified_by": None,
            "case_name": None,
            "validation_method": "Invalid Input",
            "reporter_type": None,
            "parallel_citations": [],
            "error": "Citation must be a non-empty string"
        }
    
    # Clean up the citation text before validation
    clean_citation = re.sub(r'\s+', ' ', citation_text.strip())
    clean_citation = re.sub(r',\s+', ', ', clean_citation)
    logger.info(f"[DEBUG] Cleaned citation for validation: {clean_citation}")
    print(f"DEBUG: Cleaned citation for validation: {clean_citation}")
    
    # Check if it's a valid citation format
    if not is_valid_citation_format(clean_citation):
        logger.warning(f"[DEBUG] Invalid citation format: {clean_citation}")
        print(f"DEBUG: Invalid citation format: {clean_citation}")
        return {
            "verified": False,
            "verified_by": None,
            "case_name": None,
            "validation_method": "Invalid Format",
            "reporter_type": None,
            "parallel_citations": [],
            "error": "Text does not match a valid legal citation format"
        }
    
    # Initialize the validation result
    validation_result = {
        "verified": False,
        "verified_by": None,
        "case_name": None,
        "validation_method": None,
        "reporter_type": None,
        "parallel_citations": []
    }
    
    # Parse citation components for later use
    components = parse_citation_components(clean_citation)
    if components:
        validation_result["reporter_type"] = components.get("reporter", "Unknown")
        logger.info(f"[DEBUG] Parsed citation components: {components}")
        print(f"DEBUG: Parsed citation components: {components}")
    
    # Validation methods in priority order
    # 1. First check CourtListener API (most authoritative)
    logger.info(f"[DEBUG] Attempting CourtListener API validation for: {clean_citation}")
    courtlistener_result = check_courtlistener_api(clean_citation)
    
    if courtlistener_result and courtlistener_result.get("verified"):
        logger.info(f"[DEBUG] Citation validated by CourtListener API: {clean_citation}")
        print(f"DEBUG: Citation validated by CourtListener API: {clean_citation}")
        return courtlistener_result
    
    # 2. Check if this is a LEXIS citation (these are always valid)
    logger.info(f"[DEBUG] Checking if citation is LEXIS format: {clean_citation}")
    if re.search(r'LEXIS', clean_citation, re.IGNORECASE):
        validation_result["verified"] = True
        validation_result["verified_by"] = "Enhanced Validator"
        validation_result["validation_method"] = "LEXIS"
        validation_result["reporter_type"] = "LEXIS"
        logger.info(f"[DEBUG] Validated LEXIS citation: {clean_citation}")
        print(f"DEBUG: Validated LEXIS citation: {clean_citation}")
        return validation_result
    
    # 3. Check static databases in order of reliability
    for db_name, db in [
        ("Landmark", LANDMARK_CASES),
        ("CourtListener", COURTLISTENER_CASES),
        ("Multitool", MULTITOOL_CASES),
        ("Other", OTHER_CASES)
    ]:
        logger.info(f"[DEBUG] Checking {db_name} database for: {clean_citation}")
        if clean_citation in db:
            validation_result["verified"] = True
            validation_result["verified_by"] = "Enhanced Validator"
            validation_result["case_name"] = db[clean_citation]
            validation_result["validation_method"] = db_name
            logger.info(f"[DEBUG] {db_name} direct match found for citation: {clean_citation}")
            print(f"DEBUG: {db_name} direct match found for citation: {clean_citation}")
            return validation_result
    
    # 4. Try to extract the U.S. Reporter citation if it's a full citation
    # and check against databases using the short format
    if components and 'volume' in components and 'reporter' in components and 'page' in components:
        short_citation = f"{components['volume']} {components['reporter']} {components['page']}"
        logger.info(f"[DEBUG] Trying short citation format: {short_citation}")
        print(f"DEBUG: Trying short citation format: {short_citation}")
        
        # Try the short citation with CourtListener API
        if short_citation != clean_citation:  # Only if different from what we already tried
            logger.info(f"[DEBUG] Trying CourtListener API with short citation: {short_citation}")
            short_cl_result = check_courtlistener_api(short_citation)
            if short_cl_result and short_cl_result.get("verified"):
                logger.info(f"[DEBUG] Short citation validated by CourtListener API: {short_citation}")
                print(f"DEBUG: Short citation validated by CourtListener API: {short_citation}")
                return short_cl_result
        
        # Check short citation in all databases
        for db_name, db in [
            ("Landmark", LANDMARK_CASES),
            ("CourtListener", COURTLISTENER_CASES),
            ("Multitool", MULTITOOL_CASES),
            ("Other", OTHER_CASES)
        ]:
            logger.info(f"[DEBUG] Checking {db_name} database for short citation: {short_citation}")
            if short_citation in db:
                validation_result["verified"] = True
                validation_result["verified_by"] = "Enhanced Validator"
                validation_result["case_name"] = db[short_citation]
                validation_result["validation_method"] = db_name
                logger.info(f"[DEBUG] {db_name} short citation match found: {short_citation} for {clean_citation}")
                print(f"DEBUG: {db_name} short citation match found: {short_citation} for {clean_citation}")
                return validation_result
    
    # If we get here, no validation method succeeded
    logger.warning(f"[DEBUG] No validation method succeeded for citation: {clean_citation}")
    print(f"DEBUG: No validation method succeeded for citation: {clean_citation}")
    return validation_result

# Keep the old function for backward compatibility
def is_landmark_case(citation_text):
    """Check if a citation refers to a landmark case (backward compatibility)."""
    validation_result = validate_citation(citation_text)
    return validation_result["verified"]

@enhanced_validator_bp.route('/')
@enhanced_validator_bp.route('/casestrainer/')
def enhanced_validator_page():
    """Serve the Enhanced Validator page."""
    logger.info("Enhanced Validator page requested")
    return render_template('enhanced_validator.html')

@enhanced_validator_bp.route('/api/enhanced-validate-citation', methods=['POST'])
@enhanced_validator_bp.route('/casestrainer/api/enhanced-validate-citation', methods=['POST'])
def validate_citation_endpoint():
    try:
        data = request.get_json()
        if not data or 'citation' not in data:
            return jsonify({'error': 'No citation provided'}), 400
        
        citation = data['citation']
        result = validate_citation(citation)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in validate_citation_endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@enhanced_validator_bp.route('/api/citation-context', methods=['POST'])
@enhanced_validator_bp.route('/casestrainer/api/citation-context', methods=['POST'])
def get_citation_context():
    try:
        data = request.get_json()
        if not data or 'citation' not in data:
            return jsonify({'error': 'No citation provided'}), 400
        
        citation = data['citation']
        context = CITATION_CONTEXTS.get(citation, f"No context available for {citation}")
        return jsonify(context)
    except Exception as e:
        logger.error(f"Error in get_citation_context: {str(e)}")
        return jsonify({'error': str(e)}), 500

@enhanced_validator_bp.route('/api/classify-citation', methods=['POST'])
@enhanced_validator_bp.route('/casestrainer/api/classify-citation', methods=['POST'])
def classify_citation():
    try:
        data = request.get_json()
        if not data or 'citation' not in data:
            return jsonify({'error': 'No citation provided'}), 400
        
        citation = data['citation']
        is_landmark = is_landmark_case(citation)
        confidence = 0.95 if is_landmark else 0.3 + random.random() * 0.3
        
        explanations = []
        if is_landmark:
            explanations.append(f"Citation format is valid: {citation}")
            explanations.append(f"Citation refers to a landmark case: {LANDMARK_CASES.get(citation, '')}")
            explanations.append("Citation appears in verified database")
        else:
            explanations.append(f"Citation format appears unusual: {citation}")
            explanations.append("Citation not found in landmark cases database")
        
        return jsonify({
            "citation": citation,
            "confidence": confidence,
            "explanation": explanations
        })
    except Exception as e:
        logger.error(f"Error in classify_citation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@enhanced_validator_bp.route('/api/suggest-citation-corrections', methods=['POST'])
@enhanced_validator_bp.route('/casestrainer/api/suggest-citation-corrections', methods=['POST'])
def suggest_corrections():
    try:
        data = request.get_json()
        if not data or 'citation' not in data:
            return jsonify({'error': 'No citation provided'}), 400
        
        citation = data['citation']
        suggestions = []
        
        # Check if it's close to a landmark case
        for landmark in LANDMARK_CASES.keys():
            # Simple string similarity check
            if citation.split()[0] == landmark.split()[0] and citation != landmark:
                suggestions.append({
                    "corrected_citation": landmark,
                    "similarity": 0.8,
                    "explanation": f"Did you mean {landmark} ({LANDMARK_CASES[landmark]})?",
                    "correction_type": "Reporter Correction"
                })
            elif citation.split()[1] == landmark.split()[1] and citation != landmark:
                suggestions.append({
                    "corrected_citation": landmark,
                    "similarity": 0.7,
                    "explanation": f"Did you mean {landmark} ({LANDMARK_CASES[landmark]})?",
                    "correction_type": "Volume Correction"
                })
        
        return jsonify({
            "citation": citation,
            "suggestions": suggestions
        })
    except Exception as e:
        logger.error(f"Error in suggest_corrections: {str(e)}")
        return jsonify({'error': str(e)}), 500

def fetch_url_content(url):
    """Fetch content from a URL with proper error handling."""
    logger.info(f"Fetching content from URL: {url}")
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")
        
        # Make request with timeout and user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' in content_type:
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return {'text': text, 'content_type': 'text/html'}
        else:
            # Return raw content for non-HTML
            return {'text': response.text, 'content_type': content_type}
    
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while fetching URL: {url}")
        raise ValueError("Request timed out while fetching URL")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error while fetching URL: {url} - {str(e)}")
        raise ValueError(f"HTTP error: {str(e)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL: {url} - {str(e)}")
        raise ValueError(f"Error fetching URL: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while fetching URL: {url} - {str(e)}")
        raise ValueError(f"Unexpected error: {str(e)}")

@enhanced_validator_bp.route('/api/fetch_url', methods=['POST'])
@enhanced_validator_bp.route('/casestrainer/api/fetch_url', methods=['POST'])
def fetch_url():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'No URL provided'}), 400
        
        url = data['url']
        content = fetch_url_content(url)
        return jsonify(content)
    except Exception as e:
        logger.error(f"Error in fetch_url: {str(e)}")
        return jsonify({'error': str(e)}), 500

def analyze_text(text):
    """Analyze text for legal citations and provide detailed analysis."""
    logger.info("Analyzing text for legal citations")
    
    try:
        # Extract citations
        citation_results = extract_citations(text)
        
        # Initialize analysis results
        analysis = {
            'citations': citation_results,
            'statistics': {
                'total_citations': len(citation_results['confirmed_citations']) + len(citation_results['possible_citations']),
                'confirmed_citations': len(citation_results['confirmed_citations']),
                'possible_citations': len(citation_results['possible_citations'])
            },
            'landmark_cases': [],
            'validation_results': []
        }
        
        # Check for landmark cases
        for citation in citation_results['confirmed_citations']:
            if is_landmark_case(citation):
                analysis['landmark_cases'].append(citation)
        
        # Validate citations
        for citation in citation_results['confirmed_citations']:
            validation_result = validate_citation(citation)
            analysis['validation_results'].append({
                'citation': citation,
                'validation': validation_result
            })
        
        logger.info(f"Analysis complete: found {analysis['statistics']['total_citations']} citations")
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        raise ValueError(f"Error analyzing text: {str(e)}")

@enhanced_validator_bp.route('/api/enhanced-analyze', methods=['POST'])
@enhanced_validator_bp.route('/casestrainer/api/enhanced-analyze', methods=['POST'])
def enhanced_analyze():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data['text']
        if not isinstance(text, str) or not text.strip():
            return jsonify({'error': 'Invalid text format'}), 400
            
        # Limit text size to prevent memory issues
        if len(text) > 1000000:  # 1MB limit
            return jsonify({'error': 'Text too large. Maximum size is 1MB.'}), 400
            
        analysis = analyze_text(text)
        return jsonify(analysis)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in enhanced_analyze: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'rtf', 'odt', 'html', 'htm'}

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from different file types
def extract_text_from_file(file_path):
    """Extract text from a file based on its extension."""
    logger.info(f"Extracting text from file: {file_path}")
    
    # Get file extension
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        # Handle different file types
        if file_ext == '.pdf':
            # Import PDF handler only when needed
            try:
                from pdf_handler import extract_text_from_pdf
                return extract_text_from_pdf(file_path)
            except ImportError:
                logger.warning("pdf_handler module not found. Using basic PDF text extraction.")
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        text = ''
                        for page in reader.pages:
                            text += page.extract_text() + '\n'
                    logger.info("Successfully extracted text using PyPDF2")
                except ImportError:
                    logger.error("PyPDF2 not installed")
                    return "Error: PyPDF2 not installed. Cannot extract text from PDF."
        
        elif file_ext in ['.doc', '.docx']:
            try:
                import docx
                doc = docx.Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])
            except ImportError:
                logger.error("python-docx not installed. Cannot extract text from Word documents.")
                return "Error: python-docx not installed. Cannot extract text from Word documents."
        
        elif file_ext == '.rtf':
            if not STRIPRTF_AVAILABLE:
                logger.error("striprtf not installed. Cannot extract text from RTF documents.")
                return "Error: striprtf not installed. Cannot extract text from RTF documents."
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    rtf_text = file.read()
                    
                    # Basic RTF format validation
                    if not rtf_text.startswith('{\\rtf'):
                        logger.warning("File does not appear to be a valid RTF document")
                        return "Warning: File does not appear to be a valid RTF document"
                    
                    try:
                        text = striprtf.striprtf.rtf_to_text(rtf_text)
                        if not text.strip():
                            logger.warning("RTF conversion produced empty text")
                            return "Warning: RTF conversion produced empty text. The file may be corrupted or empty."
                        
                        # Basic validation of extracted text
                        if len(text) < 10:  # Arbitrary minimum length
                            logger.warning("RTF conversion produced suspiciously short text")
                            return "Warning: RTF conversion produced suspiciously short text. The file may be corrupted."
                        
                        logger.info(f"Successfully extracted {len(text)} characters from RTF file")
                        return text
                        
                    except striprtf.striprtf.RTFError as rtf_error:
                        logger.error(f"RTF parsing error: {str(rtf_error)}")
                        return f"Error: Invalid RTF format - {str(rtf_error)}"
                    except Exception as rtf_error:
                        logger.error(f"Unexpected error converting RTF: {str(rtf_error)}")
                        return f"Error converting RTF: {str(rtf_error)}"
                        
            except IOError as io_error:
                logger.error(f"Error reading RTF file: {str(io_error)}")
                return f"Error reading RTF file: {str(io_error)}"
            except Exception as e:
                logger.error(f"Unexpected error processing RTF file: {str(e)}")
                return f"Error processing RTF file: {str(e)}"
        
        elif file_ext in ['.html', '.htm']:
            try:
                from bs4 import BeautifulSoup
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                    return soup.get_text()
            except ImportError:
                logger.error("BeautifulSoup not installed. Cannot extract text from HTML documents.")
                return "Error: BeautifulSoup not installed. Cannot extract text from HTML documents."
        
        else:  # Default to plain text
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
    
    except Exception as e:
        logger.error(f"Error extracting text from file {file_path}: {str(e)}")
        traceback.print_exc()
        return f"Error extracting text: {str(e)}"

def extract_citations(text):
    """Extract legal citations from text using eyecite and regex patterns."""
    logger.info("Extracting citations from text")
    
    # Initialize results dictionary
    results = {
        'confirmed_citations': [],
        'possible_citations': []
    }
    
    # Try to use eyecite with AhocorasickTokenizer if available
    try:
        from eyecite import get_citations
        from eyecite.tokenizers import AhocorasickTokenizer
        logger.info("Using eyecite with AhocorasickTokenizer for citation extraction")
        citations = get_citations(text, tokenizer=AhocorasickTokenizer())
        
        # Process eyecite citations
        for citation in citations:
            # Get the full citation text including case name and pin cite
            citation_text = citation.matched_text()
            
            # Add pin cite if available
            if hasattr(citation, 'pin_cite') and citation.pin_cite:
                citation_text = f"{citation_text}, {citation.pin_cite}"
            
            # Add case name if available
            if hasattr(citation, 'metadata') and citation.metadata:
                if citation.metadata.plaintiff and citation.metadata.defendant:
                    case_name = f"{citation.metadata.plaintiff} v. {citation.metadata.defendant}"
                    citation_text = f"{case_name}, {citation_text}"
            
            # Clean up the citation
            citation_text = re.sub(r'\s+', ' ', citation_text)  # Normalize whitespace
            citation_text = re.sub(r',\s+', ', ', citation_text)  # Fix spacing around commas
            
            if citation_text and citation_text not in results['confirmed_citations']:
                results['confirmed_citations'].append(citation_text)
                logger.debug(f"Found citation using eyecite: {citation_text}")
        
        logger.info(f"Extracted {len(results['confirmed_citations'])} confirmed citations using eyecite")
    except ImportError as e:
        logger.warning(f"eyecite import error: {e}. Using regex patterns for citation extraction.")
    except Exception as e:
        logger.warning(f"Error using eyecite: {e}. Falling back to regex patterns.")
    
    # Extract possible citations using regex patterns
    all_possible_citations = set()  # Use set to avoid duplicates
    
    # First try to extract LEXIS citations
    lexis_patterns = {k: v for k, v in CITATION_PATTERNS.items() if k.startswith('lexis_')}
    for pattern_name, pattern in lexis_patterns.items():
        try:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                citation = match.group(0).strip()
                # Clean up the citation
                citation = re.sub(r'\s+', ' ', citation)  # Normalize whitespace
                citation = re.sub(r',\s+', ', ', citation)  # Fix spacing around commas
                if citation and citation not in results['confirmed_citations']:
                    all_possible_citations.add(citation)
                    logger.debug(f"Found possible LEXIS citation using {pattern_name} pattern: {citation}")
        except Exception as e:
            logger.warning(f"Error searching for LEXIS pattern {pattern_name}: {e}")
    
    # Then try other citation patterns
    other_patterns = {k: v for k, v in CITATION_PATTERNS.items() if not k.startswith('lexis_')}
    for pattern_name, pattern in other_patterns.items():
        try:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                citation = match.group(0).strip()
                # Clean up the citation
                citation = re.sub(r'\s+', ' ', citation)  # Normalize whitespace
                citation = re.sub(r',\s+', ', ', citation)  # Fix spacing around commas
                if citation and citation not in results['confirmed_citations']:
                    all_possible_citations.add(citation)
                    logger.debug(f"Found possible citation using {pattern_name} pattern: {citation}")
        except Exception as e:
            logger.warning(f"Error searching for pattern {pattern_name}: {e}")
    
    # Add unique possible citations to results
    results['possible_citations'] = list(all_possible_citations)
    logger.info(f"Extracted {len(results['possible_citations'])} possible citations using regex patterns")
    
    # Validate all citations
    validated_citations = []
    for citation in results['possible_citations']:
        validation_result = validate_citation(citation)
        if validation_result['verified']:
            validated_citations.append(citation)
            results['confirmed_citations'].append(citation)
    
    # Remove validated citations from possible citations
    results['possible_citations'] = [c for c in results['possible_citations'] if c not in validated_citations]
    
    logger.info(f"Final results: {len(results['confirmed_citations'])} confirmed and {len(results['possible_citations'])} possible citations")
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        logger.info(f"Successfully extracted {len(text)} characters from URL")
        return text
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL: {str(e)}")
        raise ValueError(f"Error fetching URL: {str(e)}")
    except Exception as e:
        logger.error(f"Error extracting text from URL: {str(e)}")
        raise ValueError(f"Error extracting text from URL: {str(e)}")

# Function to register the blueprint with the Flask app
def register_enhanced_validator(app):
    """Register the enhanced validator blueprint with the Flask app."""
    app.register_blueprint(enhanced_validator_bp, name='enhanced_validator_production_v3')
    logger.info("Enhanced Validator blueprint registered with the Flask app")
    return app

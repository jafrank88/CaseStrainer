"""
Enhanced Multi-Source Verifier

This module provides an enhanced citation verification system that uses multiple sources
and advanced techniques to validate legal citations.
"""

import os
import json
import logging
import requests
import re
import time
import sqlite3
import datetime
import importlib.util
import concurrent.futures
from typing import Dict, Any, Optional, List, Tuple, Union
from src.citation_format_utils import apply_washington_spacing_rules, normalize_washington_synonyms
from src.cache_manager import get_cache_manager
from urllib.parse import quote, quote_plus, urljoin, urlparse
from bs4 import BeautifulSoup
import redis
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.enhanced_legal_scraper import EnhancedLegalScraper
import random
from src.database_manager import get_database_manager
import threading
import httpx
import parsel
from src.extract_case_name import (
    extract_case_name_by_site,
    extract_case_name_from_page,
    extract_case_name_from_url_content,
    extract_metadata_from_google_snippet,
    extract_case_name_unified,
    extract_case_name_from_context_unified,
    clean_case_name,
    is_valid_case_name,
    identify_site_type,
    extract_case_name_courtlistener,
    extract_case_name_justia,
    extract_case_name_findlaw,
    extract_case_name_casetext,
    extract_case_name_leagle,
    extract_case_name_supreme_court,
    extract_case_name_cornell,
    identify_site_type
)
from src.citation_normalizer import normalize_citation
import asyncio

# Import the optimized web searcher
try:
    from .optimized_web_searcher import OptimizedWebSearcher
    OPTIMIZED_SEARCHER_AVAILABLE = True
except ImportError:
    OptimizedWebSearcher = None
    OPTIMIZED_SEARCHER_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# Add at the top with other imports
try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DDGS = None
    DUCKDUCKGO_AVAILABLE = False

# Landmark cases database for quick verification
LANDMARK_CASES = {
    # Format: 'citation': {'name': 'Case Name', 'year': YYYY, 'court': 'Court Name', 'significance': 'Brief description'}
    # Supreme Court Reporter (U.S.) citations
    "410 U.S. 113": {
        "name": "Roe v. Wade",
        "year": 1973,
        "court": "Supreme Court of the United States",
        "significance": "Established a woman's legal right to abortion",
    },
    "347 U.S. 483": {
        "name": "Brown v. Board of Education",
        "year": 1954,
        "court": "Supreme Court of the United States",
        "significance": "Declared racial segregation in public schools unconstitutional",
    },
    "5 U.S. 137": {
        "name": "Marbury v. Madison",
        "year": 1803,
        "court": "Supreme Court of the United States",
        "significance": "Established judicial review",
    },
    "384 U.S. 436": {
        "name": "Miranda v. Arizona",
        "year": 1966,
        "court": "Supreme Court of the United States",
        "significance": "Required police to inform suspects of their rights",
    },
    "381 U.S. 479": {
        "name": "Griswold v. Connecticut",
        "year": 1965,
        "court": "Supreme Court of the United States",
        "significance": "Established right to privacy in marital relationships",
    },
    "198 U.S. 45": {
        "name": "Lochner v. New York",
        "year": 1905,
        "court": "Supreme Court of the United States",
        "significance": "Limited government regulation of labor conditions",
    },
    "17 U.S. 316": {
        "name": "McCulloch v. Maryland",
        "year": 1819,
        "court": "Supreme Court of the United States",
        "significance": "Established federal authority over states",
    },
    "376 U.S. 254": {
        "name": "New York Times Co. v. Sullivan",
        "year": 1964,
        "court": "Supreme Court of the United States",
        "significance": 'Established "actual malice" standard for defamation of public figures',
    },
    "163 U.S. 537": {
        "name": "Plessy v. Ferguson",
        "year": 1896,
        "court": "Supreme Court of the United States",
        "significance": 'Upheld "separate but equal" racial segregation',
    },
    "531 U.S. 98": {
        "name": "Bush v. Gore",
        "year": 2000,
        "court": "Supreme Court of the United States",
        "significance": "Resolved the 2000 presidential election dispute",
    },
    "558 U.S. 310": {
        "name": "Citizens United v. Federal Election Commission",
        "year": 2010,
        "court": "Supreme Court of the United States",
        "significance": "Removed restrictions on political campaign spending by organizations",
    },
    "576 U.S. 644": {
        "name": "Obergefell v. Hodges",
        "year": 2015,
        "court": "Supreme Court of the United States",
        "significance": "Legalized same-sex marriage nationwide",
    },
    # Supreme Court Reporter (S.Ct.) citations
    "93 S.Ct. 705": {
        "name": "Roe v. Wade",
        "year": 1973,
        "court": "Supreme Court of the United States",
        "significance": "Established a woman's legal right to abortion",
    },
    "74 S.Ct. 686": {
        "name": "Brown v. Board of Education",
        "year": 1954,
        "court": "Supreme Court of the United States",
        "significance": "Declared racial segregation in public schools unconstitutional",
    },
}

# Valid volume ranges for different reporters - with generous upper bounds for future growth
VALID_VOLUME_RANGES = {
    "us_reports": (1, 1000),  # U.S. Reports volumes (currently ~600, but allow for future)
    "federal_reporter_1": (1, 500),  # F.1d volumes (currently ~300, but allow for future)
    "federal_reporter_2": (1, 1500),  # F.2d volumes (currently ~1000, but allow for future)
    "federal_reporter_3": (1, 1500),  # F.3d volumes (currently ~1000, but allow for future)
    "federal_reporter_4": (1, 1000),  # F.4d volumes (future series)
    "federal_reporter_5": (1, 1000),  # F.5d volumes (future series)
    "federal_reporter_6": (1, 1000),  # F.6d volumes (future series)
    "federal_supplement_1": (1, 1500),  # F. Supp. volumes (allow for future)
    "federal_supplement_2": (1, 1500),  # F. Supp. 2d volumes (allow for future)
    "federal_supplement_3": (1, 1000),  # F. Supp. 3d volumes (allow for future)
    "federal_supplement_4": (1, 1000),  # F. Supp. 4d volumes (future series)
    "supreme_court_reporter": (1, 1000),  # S.Ct. volumes
}

# Citation patterns for format analysis
CITATION_PATTERNS = {
    # U.S. Reports - more flexible with spacing and punctuation
    "us_reports": r"(\d+)\s*U\.?\s*S\.?\s+(\d+)\s*\(\d{4}\)",  # e.g., 410 U.S. 113 (1973), 410US113(1973)
    # Federal Reporter - allow for future series (F.4th, F.5th, etc.)
    "federal_reporter": r"(\d+)\s*F\.?\s*(\d)[\w]*\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 123 F.3d 456, 123 F.4th 456
    # Federal Supplement - more flexible with spacing and series
    "federal_supplement": r"(\d+)\s*F\.?\s*Supp\.?\s*(\d*)[\w]*\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 456 F.Supp.2d 789
    # State reporter - more flexible
    "state_reporter": r"(\d+)\s*([A-Za-z\.]+)\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 123 Cal. App. 4th 456
    # Regional reporter - more flexible with spacing and series
    "regional_reporter": r"(\d+)\s*([A-Za-z\.]+)(\d*)[\w]*\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 456 N.E.2d 789, 456 N.E.3d 789
    # Supreme Court Reporter - more flexible
    "supreme_court_reporter": r"(\d+)\s*S\.?\s*Ct\.?\s+(\d+)\s*\(\d{4}\)",
    # Lawyers Edition - more flexible
    "lawyers_edition": r"(\d+)\s*L\.?\s*Ed\.?\s*(\d+)[\w]*\s+(\d+)\s*\(\d{4}\)",
    # Westlaw - standard format
    "westlaw": r"(\d{4})\s*WL\s*(\d+)",
}

class RateLimitError(Exception):
    pass

class EnhancedMultiSourceVerifier:
    """
    An enhanced citation verifier that uses multiple sources and techniques
    to validate legal citations with higher accuracy.
    """

    # Class-level global rate limiting counter
    _global_consecutive_failures = 0
    _global_max_consecutive_failures = 3
    _global_rate_limit_lock = threading.Lock()

    def __init__(self):
        """Initialize the enhanced multi-source verifier."""
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        self.db_path = self.config.get("database_path", "data/citations.db")
        self.courtlistener_api_key = self.config.get("courtlistener_api_key")
        self.cache_manager = get_cache_manager()
        
        # Initialize CourtListener API settings
        self.courtlistener_base_url = "https://www.courtlistener.com/api/rest/v4"
        self.headers = {
            "Authorization": (
                f"Token {self.courtlistener_api_key}"
                if self.courtlistener_api_key
                else ""
            ),
            "Content-Type": "application/json",
        }
        
        # Initialize database connection pool
        self._init_database()
        
        # Initialize connection pool for HTTP requests
        self.session = self._create_session()
        
        # Request cache for API calls
        self.request_cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        
        # Set cache reference for compatibility
        self.cache = self.cache_manager.cache if hasattr(self.cache_manager, 'cache') else None
        
        # Performance tracking
        self.stats = {
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_time': 0
        }
        self.enhanced_legal_scraper = EnhancedLegalScraper()
        self.citations_checked_cl = []
        self.citations_checked_google = []
        self.citations_checked_bing = []
        self.citation_paths = {}  # citation -> ["CL", "Google", "Bing"]
        
        # Initialize optimized web searcher if available
        self.optimized_searcher = None
        if OPTIMIZED_SEARCHER_AVAILABLE:
            try:
                self.optimized_searcher = OptimizedWebSearcher()
                self.logger.info("Optimized web searcher initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize optimized web searcher: {e}")
                self.optimized_searcher = None

    def _load_config(self):
        """Load configuration from config.json."""
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.json"
        )
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def _init_database(self):
        """Initialize SQLite database with proper schema."""
        try:
            db_manager = get_database_manager()
            # Check if citations table exists
            tables = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='citations'")
            table_exists = bool(tables)
            if not table_exists:
                # Create citations table with the existing schema
                db_manager.execute_query('''
                    CREATE TABLE citations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        citation_text TEXT UNIQUE NOT NULL,
                        case_name TEXT,
                        year INTEGER,
                        parallel_citations TEXT,
                        verification_result TEXT,
                        found BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

    def _extract_citation_components(self, citation):
        """Extract components from a citation for flexible matching.

        Handles various citation formats including:
        - Standard: 123 Wn.2d 456
        - Pinpoint: 123 Wn.2d 456, 459
        - Parallel: 123 Wn.2d 456, 789 P.2d 123
        - Short form: Id. at 459
        - International: [2020] UKSC 1, [2019] SCC 1
        - Regional: 123 Cal. App. 4th 456, 123 N.Y. App. Div. 456
        - Federal: 123 F.3d 456, 123 F.Supp.2d 456
        - State: 123 P.3d 456, 123 A.3d 456

        Args:
            citation (str): The citation to parse

        Returns:
            dict: Dictionary containing citation components
        """
        if not citation or not isinstance(citation, str):
            return {"volume": "", "reporter": "", "page": "", "court": "", "year": ""}

        components = {
            "volume": "",
            "reporter": "",
            "page": "",
            "court": "",
            "year": "",
            "pinpoint": "",
            "parallel_citations": [],
        }

        try:
            # Handle short form citations (e.g., "Id. at 459")
            if citation.lower().startswith(("id.", "idem")):
                components["short_form"] = True
                # Extract pinpoint reference if present
                pinpoint_match = re.search(r"(?:at\s+)(\d+)", citation, re.IGNORECASE)
                if pinpoint_match:
                    components["pinpoint"] = pinpoint_match.group(1)
                return components

            # Handle international citations with brackets [2020] UKSC 1
            international_match = re.search(r"\[(\d{4})\]\s+([A-Z]{2,4})\s+(\d+)", citation)
            if international_match:
                components["year"] = international_match.group(1)
                components["reporter"] = international_match.group(2)
                components["page"] = international_match.group(3)
                # Determine court based on international reporter
                reporter = components["reporter"].upper()
                if reporter == "UKSC":
                    components["court"] = "UK Supreme Court"
                elif reporter == "EWCA":
                    components["court"] = "England and Wales Court of Appeal"
                elif reporter == "EWHC":
                    components["court"] = "England and Wales High Court"
                elif reporter == "SCC":
                    components["court"] = "Supreme Court of Canada"
                elif reporter == "FCA":
                    components["court"] = "Federal Court of Appeal (Canada)"
                elif reporter == "FC":
                    components["court"] = "Federal Court (Canada)"
                elif reporter == "HCA":
                    components["court"] = "High Court of Australia"
                return components

            # Handle parallel citations (e.g., "123 Wn.2d 456, 789 P.2d 123") and distinguish from pinpoint pages
            if "," in citation:
                parts = [p.strip() for p in citation.split(",")]
                if len(parts) > 1:
                    parallel_parts = []
                    last_was_pinpoint = False
                    for i, p in enumerate(parts[1:], start=1):
                        # Check if the part likely represents a new citation (contains reporter or volume-reporter-page structure)
                        if p and p[0].isdigit() and (" " in p or any(r in p.lower() for r in ["p.", "f.", "wn.", "wash.", "cal.", "n.y.", "tex.", "a."])):
                            parallel_parts.append(p)
                            last_was_pinpoint = False
                        elif p and p[0].isdigit() and len(p.split()) == 1 and not last_was_pinpoint:
                            # Single number after comma is likely a pinpoint page, not a new citation
                            components["pinpoint"] = p
                            last_was_pinpoint = True
                        else:
                            # If it's a number after a pinpoint or doesn't match citation pattern, ignore or treat as additional info
                            last_was_pinpoint = False
                    if parallel_parts:
                        components["parallel_citations"] = parallel_parts
                    citation = parts[0]  # Process the first citation normally

            # Enhanced volume, reporter, and page extraction
            # Handle various formats including regional reporters
            patterns = [
                # Washington specific formats first
                r"(\d+)\s+(Wn\.\s*App\.)\s+(\d+)",  # 123 Wn. App. 456
                r"(\d+)\s+(Wn\.\s*2d)\s+(\d+)",     # 123 Wn.2d 456
                r"(\d+)\s+(Wn\.\s*3d)\s+(\d+)",     # 123 Wn.3d 456
                r"(\d+)\s+(Wash\.\s*App\.)\s+(\d+)", # 123 Wash. App. 456
                r"(\d+)\s+(Wash\.\s*2d)\s+(\d+)",   # 123 Wash. 2d 456
                r"(\d+)\s+(Wash\.\s*3d)\s+(\d+)",   # 123 Wash. 3d 456
                # Federal format: 123 F.3d 456
                r"(\d+)\s+(F\.\d+[a-z]?)\s+(\d+)",
                # State format: 123 P.3d 456
                r"(\d+)\s+([A-Z]\.\d+[a-z]?)\s+(\d+)",
                # Regional format: 123 Cal. App. 4th 456
                r"(\d+)\s+([A-Za-z\.\s]+?)\s+(\d+[a-z]+)\s+(\d+)",
                # Standard format: 123 Wn.2d 456 (fallback)
                r"(\d+)\s+([A-Za-z\.\s]+?)(?:\s+(\d+))?(?:\s*,\s*(\d+))?",
            ]

            for pattern in patterns:
                volume_reporter_page = re.search(pattern, citation)
                if volume_reporter_page:
                    components["volume"] = volume_reporter_page.group(1)
                    components["reporter"] = volume_reporter_page.group(2).strip()

                    # Handle both main page and pinpoint (e.g., "123 Wn.2d 456, 459")
                    if len(volume_reporter_page.groups()) >= 4 and volume_reporter_page.group(4):  # Has pinpoint
                        components["page"] = volume_reporter_page.group(3)
                        components["pinpoint"] = volume_reporter_page.group(4)
                    elif len(volume_reporter_page.groups()) >= 3 and volume_reporter_page.group(3):  # Just page number
                        components["page"] = volume_reporter_page.group(3)
                    break

            # Extract year if present (e.g., "(1999)" or ", 1999")
            year_match = re.search(r"\((\d{4})\)|,\s*(\d{4})\b", citation)
            if year_match:
                components["year"] = year_match.group(1) or year_match.group(2)

            # Enhanced court determination based on reporter
            reporter = components["reporter"].lower()
            
            # Washington courts
            if "wn. app" in reporter or "wash. app" in reporter:
                components["court"] = "Washington Court of Appeals"
            elif "wn." in reporter or "wash." in reporter:
                components["court"] = "Washington Supreme Court"
            
            # Federal courts
            elif "u.s." in reporter:
                components["court"] = "United States Supreme Court"
            elif "f.supp" in reporter:
                components["court"] = "United States District Court"
            elif "f." in reporter:
                components["court"] = "United States Court of Appeals"
            
            # Regional courts
            elif "cal. app" in reporter:
                components["court"] = "California Court of Appeal"
            elif "cal. rptr" in reporter:
                components["court"] = "California Reporter"
            elif "n.y. app" in reporter:
                components["court"] = "New York Appellate Division"
            elif "tex. app" in reporter:
                components["court"] = "Texas Court of Appeals"
            elif "fla. app" in reporter:
                components["court"] = "Florida Court of Appeal"
            elif "ill. app" in reporter:
                components["court"] = "Illinois Appellate Court"
            elif "ohio app" in reporter:
                components["court"] = "Ohio Court of Appeals"
            elif "mich. app" in reporter:
                components["court"] = "Michigan Court of Appeals"
            elif "pa. super" in reporter:
                components["court"] = "Pennsylvania Superior Court"
            elif "mass. app" in reporter:
                components["court"] = "Massachusetts Appeals Court"
            
            # State courts by reporter
            elif "p." in reporter and "d" in reporter:
                components["court"] = "Pacific Reporter"
            elif "a." in reporter and "d" in reporter:
                components["court"] = "Atlantic Reporter"
            elif "s." in reporter and "e" in reporter:
                components["court"] = "Southeast Reporter"
            elif "s." in reporter and "w" in reporter:
                components["court"] = "Southwest Reporter"
            elif "n." in reporter and "e" in reporter:
                components["court"] = "Northeast Reporter"
            elif "n." in reporter and "w" in reporter:
                components["court"] = "Northwest Reporter"

            # Clean up reporter abbreviation - preserve proper spacing
            # Only fix double periods, don't remove spaces
            components["reporter"] = components["reporter"].replace("..", ".")

        except Exception as e:
            logger.warning(
                f"Error extracting citation components from '{citation}': {e}"
            )

        return components

    def _check_cache(self, citation):
        """Check if the citation is in the cache."""
        cache_file = os.path.join(
            self.cache_dir,
            f"{normalize_citation(citation).replace(' ', '_')}.json",
        )
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache for citation '{citation}': {e}")
        return None

    def _save_to_cache(self, citation, result):
        """Save the verification result to the cache."""
        cache_file = os.path.join(
            self.cache_dir,
            f"{normalize_citation(citation).replace(' ', '_')}.json",
        )
        try:
            with open(cache_file, "w") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache for citation '{citation}': {e}")

    def _save_to_database(self, citation, result):
        """
        Save the verification result to the database, including parallel citations and year metadata.
        Ensures that case name and date are propagated to parallel citations.

        Args:
            citation (str): The original citation
            result (dict): Verification result with optional parallel_citations list and metadata
        """
        if not citation or not isinstance(citation, str):
            logger.error("Invalid citation provided to _save_to_database")
            return False

        try:
            db_manager = get_database_manager()
            # Create tables if they don't exist with the correct schema
            db_manager.execute_query('''
                CREATE TABLE IF NOT EXISTS citations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    citation_text TEXT NOT NULL UNIQUE,
                    case_name TEXT,
                    confidence REAL,
                    found BOOLEAN,
                    explanation TEXT,
                    source TEXT,
                    source_document TEXT,
                    url TEXT,
                    context TEXT,
                    year TEXT,
                    date_filed TEXT,
                    court TEXT,
                    docket_number TEXT,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            db_manager.execute_query('''
                CREATE TABLE IF NOT EXISTS parallel_citations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    citation_id INTEGER NOT NULL,
                    citation TEXT NOT NULL,
                    reporter TEXT,
                    category TEXT,
                    year TEXT,
                    url TEXT,
                    case_name TEXT,
                    date_filed TEXT,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (citation_id) REFERENCES citations(id) ON DELETE CASCADE,
                    UNIQUE(citation_id, citation, url)
                )
            ''')
            # Get current schema to handle any missing columns
            columns = db_manager.execute_query("PRAGMA table_info(citations)")
            columns = {column['name'].lower(): column['name'] for column in columns}

            # Add any missing columns with proper error handling
            columns_to_add = [
                ("case_name", "TEXT"),
                ("found", "BOOLEAN"),
                ("explanation", "TEXT"),
                ("source", "TEXT"),
                ("source_document", "TEXT"),
                ("url", "TEXT"),
                ("context", "TEXT"),
                ("year", "TEXT"),
                ("date_filed", "TEXT"),
                ("court", "TEXT"),
                ("docket_number", "TEXT"),
            ]

            for col_name, col_type in columns_to_add:
                if col_name not in columns:
                    try:
                        db_manager.execute_query(
                            f"ALTER TABLE citations ADD COLUMN {col_name} {col_type}"
                        )
                        logger.info(
                            f"Added missing column {col_name} to citations table"
                        )
                    except sqlite3.Error as e:
                        logger.warning(f"Error adding column {col_name}: {e}")

            parallel_columns = db_manager.execute_query("PRAGMA table_info(parallel_citations)")
            parallel_columns = {column['name'].lower(): column['name'] for column in parallel_columns}
            parallel_columns_to_add = [
                ("case_name", "TEXT"),
                ("date_filed", "TEXT"),
            ]

            for col_name, col_type in parallel_columns_to_add:
                if col_name not in parallel_columns:
                    try:
                        db_manager.execute_query(
                            f"ALTER TABLE parallel_citations ADD COLUMN {col_name} {col_type}"
                        )
                        logger.info(
                            f"Added missing column {col_name} to parallel_citations table"
                        )
                    except sqlite3.Error as e:
                        logger.warning(f"Error adding column {col_name} to parallel_citations: {e}")

            # Extract year from various sources
            year = ""
            date_filed = result.get("date_filed", "")
            
            # Try to extract year from date_filed first
            if date_filed:
                try:
                    # Handle various date formats
                    if isinstance(date_filed, str):
                        # Try to extract year from ISO format (YYYY-MM-DD)
                        year_match = re.search(r'(\d{4})', date_filed)
                        if year_match:
                            year = year_match.group(1)
                except Exception as e:
                    logger.warning(f"Error extracting year from date_filed '{date_filed}': {e}")
            
            # If no year from date_filed, try metadata
            if not year:
                metadata = result.get("metadata", {})
                if metadata.get("year"):
                    year = str(metadata["year"])
                elif metadata.get("date_filed"):
                    try:
                        year_match = re.search(r'(\d{4})', str(metadata["date_filed"]))
                        if year_match:
                            year = year_match.group(1)
                    except Exception as e:
                        logger.warning(f"Error extracting year from metadata: {e}")

            # Prepare the data for insertion/update
            case_name = result.get("case_name", "")
            found = bool(result.get("verified", False))
            explanation = f"Verified via {result.get('source', 'unknown')} on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            source = result.get("source", "")
            url = result.get("absolute_url", result.get("url", ""))
            source_doc = result.get("source_document", "")
            court = result.get("court", "")
            docket_number = result.get("docket_number", "")
            parallel_cites = result.get("parallel_citations", [])

            try:
                # First, insert or update the main citation
                db_manager.execute_query(
                    """
                    INSERT INTO citations (
                        citation_text, case_name, found, explanation, 
                        source, url, source_document, context, year, date_filed, court, docket_number
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(citation_text) DO UPDATE SET
                        case_name = excluded.case_name,
                        found = excluded.found,
                        explanation = excluded.explanation,
                        source = excluded.source,
                        url = excluded.url,
                        source_document = excluded.source_document,
                        context = excluded.context,
                        year = excluded.year,
                        date_filed = excluded.date_filed,
                        court = excluded.court,
                        docket_number = excluded.docket_number
                    RETURNING id
                """,
                    (
                        citation,
                        case_name,
                        found,
                        explanation,
                        source,
                        url,
                        source_doc,
                        result.get("context", ""),
                        year,
                        date_filed,
                        court,
                        docket_number,
                    ),
                )

                # Get the citation ID
                row = db_manager.execute_query("SELECT id FROM citations WHERE citation_text = ?", (citation,))
                if not row:
                    raise Exception("Failed to get citation ID after insert/update")

                citation_id = row[0]['id']

                # Handle parallel citations if they exist
                if parallel_cites and isinstance(parallel_cites, list):
                    # First, get existing parallel citations to determine what needs to be updated/inserted/deleted
                    rows = db_manager.execute_query(
                        """
                        SELECT citation, reporter, category, year, url 
                        FROM parallel_citations 
                        WHERE citation_id = ?
                        """,
                        (citation_id,),
                    )
                    existing_parallels = {row['citation'] for row in rows}

                    # Process each parallel citation
                    seen = set()
                    for parallel in parallel_cites:
                        if not isinstance(parallel, dict):
                            continue
                        cite = parallel.get("citation", "").strip()
                        url = parallel.get("url", "").strip()
                        if not cite:
                            continue
                        key = (cite, url)
                        if key in seen:
                            continue
                        seen.add(key)
                        # Extract year from parallel citation if available, otherwise use the primary citation's year
                        parallel_year = ""
                        if parallel.get("year"):
                            parallel_year = str(parallel["year"])
                        elif parallel.get("date_filed"):
                            try:
                                year_match = re.search(r'(\d{4})', str(parallel["date_filed"]))
                                if year_match:
                                    parallel_year = year_match.group(1)
                            except Exception as e:
                                logger.warning(f"Error extracting year from parallel citation: {e}")
                        if not parallel_year:
                            parallel_year = year
                        # Use primary citation's date_filed if available
                        parallel_date_filed = parallel.get("date_filed", date_filed)
                        # Use primary citation's case_name if available
                        parallel_case_name = parallel.get("case_name", case_name)
                        # Insert or update the parallel citation with url and metadata
                        db_manager.execute_query(
                            """
                            INSERT INTO parallel_citations (
                                citation_id, citation, reporter, category, year, url, case_name, date_filed
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(citation_id, citation, url) DO UPDATE SET
                                reporter = excluded.reporter,
                                category = excluded.category,
                                year = excluded.year,
                                url = excluded.url,
                                case_name = excluded.case_name,
                                date_filed = excluded.date_filed
                            """,
                            (
                                citation_id,
                                cite,
                                parallel.get("reporter", ""),
                                parallel.get("category", ""),
                                parallel_year,
                                url,
                                parallel_case_name,
                                parallel_date_filed,
                            ),
                        )

                    # Delete any remaining parallel citations that weren't in the new list
                    if existing_parallels:
                        placeholders = ",".join(["?"] * len(existing_parallels))
                        db_manager.execute_query(
                            f"""
                            DELETE FROM parallel_citations 
                            WHERE citation_id = ? 
                            AND citation IN ({placeholders})
                            """,
                            tuple([citation_id] + list(existing_parallels)),
                        )

                # Commit the transaction
                db_manager.commit()
                logger.debug(
                    f"Successfully saved verification result for citation '{citation}' to database with year '{year}' and {len(parallel_cites)} parallel citations"
                )
                return True

            except sqlite3.Error as e:
                db_manager.rollback()
                logger.error(f"Database error saving citation '{citation}': {e}")
                return False
            except Exception as e:
                db_manager.rollback()
                logger.error(f"Unexpected error saving citation '{citation}': {e}")
                return False

        except sqlite3.Error as e:
            logger.error(f"Database error saving citation '{citation}': {e}")
            if db_manager:
                db_manager.rollback()
            return False
        except Exception as e:
            logger.error(
                f"Error saving verification result for citation '{citation}': {e}"
            )
            if db_manager:
                db_manager.rollback()
            return False
        finally:
            if db_manager:
                db_manager.close()

    def _get_parallel_citations(self, case_data):
        """Extract parallel citations from case data.

        Handles CourtListener API v4 response format where citations might be in different fields.
        """
        parallel_cites = []
        if not case_data:
            return parallel_cites

        try:
            # Try to get citations from the case data
            citations = case_data.get("citations", [])

            # If no citations array, try to get from the opinion_cites field
            if not citations and "opinion_cites" in case_data:
                citations = [
                    cite
                    for cite in case_data["opinion_cites"]
                    if isinstance(cite, dict) and "cite" in cite
                ]

            # Process all found citations
            for cite in citations:
                # Skip if it's not a dictionary
                if not isinstance(cite, dict):
                    continue

                # Handle CourtListener API v4 format where citations have volume, reporter, page fields
                if "volume" in cite and "reporter" in cite and "page" in cite:
                    # Construct the full citation from components
                    volume = cite.get("volume", "")
                    reporter = cite.get("reporter", "")
                    page = cite.get("page", "")
                    
                    # Create the citation string
                    citation_text = f"{volume} {reporter} {page}"
                    
                    # Add to parallel citations with available metadata
                    parallel_cites.append(
                        {
                            "citation": citation_text,
                            "reporter": reporter,
                            "category": cite.get("type", ""),
                            "volume": str(volume),
                            "page": str(page),
                            "url": cite.get("resource_uri") or cite.get("url", ""),
                        }
                    )
                else:
                    # Handle legacy format with pre-constructed citation text
                    citation_text = cite.get("cite") or cite.get("citation")
                    if not citation_text:
                        continue

                    # Add to parallel citations with available metadata
                    parallel_cites.append(
                        {
                            "citation": citation_text,
                            # Try to get reporter from various possible fields
                            "reporter": cite.get("reporter")
                            or cite.get("reporter_name", ""),
                            # Try to get category or type
                            "category": cite.get("category") or cite.get("type", ""),
                            # Include any additional metadata that might be useful
                            "url": cite.get("resource_uri") or cite.get("url", ""),
                        }
                    )

        except Exception as e:
            logger.error(f"Error extracting parallel citations: {e}")

        return parallel_cites

    def _clean_citation_for_lookup(self, citation: str) -> str:
        """
        Clean and standardize a citation for the lookup API.

        Args:
            citation (str): The citation to clean

        Returns:
            str: Cleaned citation string
        """
        if not citation:
            return ""

        # Remove any surrounding quotes and extra whitespace
        clean = citation.strip("\"'").strip()

        # Normalize whitespace (replace multiple spaces with single space)
        clean = re.sub(r'\s+', ' ', clean)

        # Remove any trailing punctuation that's not part of the citation
        clean = re.sub(r'[.,;]+$', '', clean)

        # Handle common citation formats while preserving structure
        # Split into parts and clean each part individually
        parts = clean.split()
        cleaned_parts = []
        
        i = 0
        while i < len(parts):
            part = parts[i]
            
            # Skip common connecting words, but preserve reporter abbreviations
            if part.lower() in ['at']:
                i += 1
                continue
                
            # Handle reporter abbreviations like P.3d, F.3d, etc.
            if part.lower() in ['p.', 'f.'] and i + 1 < len(parts):
                next_part = parts[i + 1]
                # Check if next part is a number or starts with a number (like '3d', '2d')
                if next_part[0].isdigit() or next_part.lower() in ['2d', '3d', '4th']:
                    # This is part of a reporter abbreviation, combine them
                    combined = part + next_part
                    cleaned_part = "".join(c for c in combined if c.isalnum() or c in ".-")
                    if cleaned_part:
                        cleaned_parts.append(cleaned_part)
                    i += 2  # Skip both parts
                    continue
            
            # Clean the part but preserve periods and hyphens
            cleaned_part = "".join(c for c in part if c.isalnum() or c in ".-")
            
            # Only add non-empty parts
            if cleaned_part:
                cleaned_parts.append(cleaned_part)
            
            i += 1

        # Rejoin with single spaces to preserve citation structure
        result = " ".join(cleaned_parts)
        
        # Ensure proper spacing for common reporter patterns
        # Only add spaces if they don't already exist and avoid breaking reporter abbreviations
        result = re.sub(r'(\d+)([A-Za-z]+\.)', r'\1 \2', result)  # Add space between volume and reporter
        # Don't add space between reporter and page if it's a reporter abbreviation like P.3d, F.3d
        result = re.sub(r'([A-Za-z]+\.)(\d+)(?!d)', r'\1 \2', result)  # Add space between reporter and page, but not if followed by 'd'
        
        return result

    def _lookup_citation(self, citation: str) -> dict:
        """
        Look up a citation using the CourtListener Citation Lookup API.

        Args:
            citation (str): The citation to look up

        Returns:
            dict: Result with case information if found, or None if not found

        The API endpoint expects a POST request to /api/rest/v4/citation-lookup/
        with the citation in the request body as form data with key 'text'.

        Authentication is done via the Authorization header with a token.
        """
        if not citation:
            logger.debug("No citation provided for lookup")
            return None

        try:
            # Clean and prepare the citation for the API
            clean_citation = self._clean_citation_for_lookup(citation)
            if not clean_citation:
                logger.warning(f"Could not clean citation for lookup: {citation}")
                return None

            # Set up headers with authentication and JSON content type
            headers = {
                "Authorization": (
                    f"Token {self.courtlistener_api_key}"
                    if self.courtlistener_api_key
                    else ""
                ),
                "Content-Type": "application/json"
            }
            headers = {k: v for k, v in headers.items() if v}

            # Build the API URL
            base_url = "https://www.courtlistener.com/api/rest/v4"
            endpoint = f"{base_url}/citation-lookup/"

            logger.info(f"Looking up citation with CourtListener API: {clean_citation}")

            try:
                # Make the API request to the citation lookup endpoint using POST with JSON data
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json={"text": clean_citation},
                    timeout=15,  # 15 second timeout
                )

                # Log the response status and headers for debugging
                logger.debug(f"Lookup status: {response.status_code}")

                # Handle rate limiting (429 Too Many Requests)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after + 1)
                    return self._lookup_citation(citation)  # Retry once

                # Handle other error status codes
                response.raise_for_status()

                # Parse the JSON response
                try:
                    data = response.json()
                    # Log the response data structure for debugging
                    logger.debug(
                        f"API Response: {json.dumps(data, indent=2)[:1000]}..."
                    )
                except json.JSONDecodeError as e:
                    error_msg = f"Failed to parse JSON response: {str(e)}"
                    # Safely log the response text to avoid Unicode encoding errors
                    try:
                        logger.error(f"{error_msg}. Response text: {response.text[:500]}")
                    except UnicodeEncodeError:
                        # If Unicode fails, log a safe version
                        safe_text = response.text[:500].encode('cp1252', errors='replace').decode('cp1252')
                        logger.error(f"{error_msg}. Response text (safe): {safe_text}")
                    return {
                        "verified": "false",
                        "citation": clean_citation,
                        "error": error_msg,
                        "source": "CourtListener API",
                    }

                # Process the response based on the API version and structure
                if not data:
                    error_msg = "Empty response from API"
                    logger.warning(f"{error_msg} for citation: {clean_citation}")
                    return {
                        "verified": "false",
                        "citation": clean_citation,
                        "error": error_msg,
                        "source": "CourtListener API",
                    }
                
                # The API returns a list of citation objects
                if isinstance(data, list) and len(data) > 0:
                    # Take the first result
                    citation_data = data[0]
                    if citation_data.get("status") == 200 and citation_data.get("clusters"):
                        # Process the first cluster
                        cluster = citation_data["clusters"][0]
                        result = self._process_courtlistener_result(clean_citation, cluster)
                        
                        if result and result.get("verified") == "true":
                            logger.info(f"Successfully verified citation via lookup: {clean_citation}")
                            return result
                        else:
                            error_msg = result.get("error", "Citation not found in CourtListener") if result else "No valid clusters found"
                            logger.info(f"Citation not found via lookup: {clean_citation} - {error_msg}")
                            return {
                                "verified": "false",
                                "citation": clean_citation,
                                "error": error_msg,
                                "source": "CourtListener API",
                            }
                    else:
                        error_msg = citation_data.get("error_message", "Citation lookup failed")
                        logger.info(f"Citation lookup failed: {clean_citation} - {error_msg}")
                        return {
                            "verified": "false",
                            "citation": clean_citation,
                            "error": error_msg,
                            "source": "CourtListener API",
                        }
                else:
                    error_msg = "No citation results found in API response"
                    logger.warning(f"{error_msg} for citation: {clean_citation}")
                    logger.debug(f"API Response type: {type(data)}")
                    logger.debug(f"API Response content: {data}")
                    return {
                        "verified": "false",
                        "citation": clean_citation,
                        "error": error_msg,
                        "source": "CourtListener API",
                    }

            except requests.exceptions.HTTPError as e:
                status_code = (
                    int(e.response.status_code)
                    if hasattr(e, "response") and e.response
                    else 0
                )
                error_msg = f"HTTP {status_code} error during citation lookup"

                if status_code == 400:
                    logger.warning(f"Bad request: {clean_citation} - {str(e)}")
                    error_msg = "Invalid citation format"
                elif status_code == 401:
                    error_msg = "Authentication failed. Please check your API key."
                    logger.error(error_msg)
                elif status_code == 403:
                    error_msg = "Access forbidden. Your API key may not have the required permissions."
                    logger.error(error_msg)
                elif status_code == 404:
                    error_msg = f"Citation not found: {clean_citation}"
                    logger.debug(error_msg)
                elif status_code >= 500:
                    error_msg = f"Server error during citation lookup: {status_code}"
                    logger.error(error_msg)
                else:
                    error_msg = f"HTTP {status_code} error: {str(e)}"

                # Log response details if available
                if hasattr(e, "response") and e.response is not None:
                    try:
                        error_body = e.response.json()
                        logger.debug(
                            f"Error response: {json.dumps(error_body, indent=2)}"
                        )
                        error_msg = error_body.get("detail", error_msg)
                    except:
                        error_text = e.response.text[:500]
                        # Safely log the error text to avoid Unicode encoding errors
                        try:
                            logger.debug(f"Error response (non-JSON): {error_text}")
                        except UnicodeEncodeError:
                            # If Unicode fails, log a safe version
                            safe_text = error_text.encode('cp1252', errors='replace').decode('cp1252')
                            logger.debug(f"Error response (non-JSON, safe): {safe_text}")
                        error_msg = f"{error_msg}: {error_text}"

                return {
                    "verified": "false",
                    "citation": clean_citation,
                    "error": error_msg,
                    "source": "CourtListener API",
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")

        except Exception as e:
            logger.error(
                f"Unexpected error in citation lookup: {str(e)}", exc_info=True
            )

        return None

    def _verify_with_courtlistener(self, citation: str) -> dict:
        """
        Verify a citation using CourtListener API with a two-step process:
        1. Use citation-lookup API to verify the citation exists
        2. If verified, use search API to get canonical information (name, date, URL)
        """
        if not self.courtlistener_api_key:
            return {
                "verified": "false",
                "citation": citation,
                "error": "No CourtListener API key configured",
                "source": "CourtListener",
            }

        # Generate citation candidates for flexible matching
        candidates = [citation]
        tried_citations = set()

        # Add normalized versions
        normalized = self._clean_citation_for_lookup(citation)
        if normalized and normalized != citation:
            candidates.append(normalized)

        # Add components-based candidates
        components = self._extract_citation_components(citation)
        if components:
            # Add parallel citations if available
            for pc in components["parallel_citations"]:
                if pc not in candidates:
                    candidates.append(pc)
        
        # Try each candidate in order
        for cand in candidates:
            if cand in tried_citations:
                continue
            tried_citations.add(cand)
            
            # Step 1: Use citation-lookup to confirm case exists
            lookup_result = self._lookup_citation(cand)
            logger.info(f"[CourtListener] Citation Lookup result for '{cand}': {json.dumps(lookup_result, default=str)[:500]}")
            
            if lookup_result and lookup_result.get("verified") == "true":
                # Step 2: If citation-lookup is positive, use search API to get full canonical info
                logger.info(f"[CourtListener] Citation-lookup positive for '{cand}', now getting canonical info via search API")
                search_result = self._search_courtlistener_exact(cand)
                logger.info(f"[CourtListener] Search API result for '{cand}': {json.dumps(search_result, default=str)[:500]}")
                
                if search_result and search_result.get("verified") == "true":
                    # We have both confirmation and canonical info
                    logger.info(f"[CourtListener] Successfully verified '{cand}' with both lookup and search APIs")
                    return search_result
                else:
                    # Citation-lookup was positive but search failed, return lookup result with basic info
                    logger.warning(f"[CourtListener] Citation-lookup positive but search API failed for '{cand}', using lookup result")
                    # Extract basic info from lookup result if available
                    if lookup_result.get("case_name") and lookup_result.get("url"):
                        return lookup_result
                    else:
                        # Try to extract case name from the lookup result's absolute_url if available
                        if lookup_result.get("absolute_url"):
                            case_name = self._extract_case_name_from_url(lookup_result["absolute_url"])
                            lookup_result["case_name"] = case_name
                            lookup_result["canonical_name"] = case_name
                        return lookup_result
            
            # If citation-lookup failed, try flexible search as fallback
            flexible_result = self._search_courtlistener_flexible(cand)
            logger.info(f"[CourtListener] Flexible Search result for '{cand}': {json.dumps(flexible_result, default=str)[:500]}")
            if flexible_result.get("verified") == "true" and flexible_result.get("case_name") and flexible_result["case_name"] != "Unknown Case":
                return flexible_result
        
        # If all else fails, return the best available (even if not verified)
        # Try the original as fallback
        processed = self._process_courtlistener_result(citation, self._lookup_citation(citation))
        if processed:
            return processed
        return {
            "verified": "false",
            "citation": citation,
            "case_name": "Unknown Case",
            "date_filed": None,
            "parallel_citations": [],
            "source": "CourtListener",
            "error": "No match found in CourtListener API after all forms tried"
        }

    def _extract_case_name_from_url(self, absolute_url: str) -> str:
        """
        Extract case name from CourtListener absolute_url.
        
        Args:
            absolute_url (str): The absolute_url from CourtListener API
            
        Returns:
            str: The extracted case name in Title Case
        """
        try:
            if not absolute_url:
                return ""
            
            # Extract the last part of the URL path and convert from kebab-case to Title Case
            url_parts = absolute_url.strip('/').split('/')
            if len(url_parts) >= 2:
                case_slug = url_parts[-1]  # e.g., "brown-v-board-of-education"
                # Convert kebab-case to Title Case
                case_name = case_slug.replace('-', ' ').title()
                # Handle common legal abbreviations
                case_name = case_name.replace(' V ', ' v. ')
                case_name = case_name.replace(' V. ', ' v. ')
                return case_name
            
            return ""
        except Exception as e:
            logger.error(f"Error extracting case name from URL '{absolute_url}': {e}")
            return ""

    def _search_courtlistener_exact(self, citation: str) -> dict:
        """Search for an exact citation match in CourtListener.

        Returns:
            dict: A dictionary with verification results, always containing 'verified' and 'citation' keys
        """
        result = {
            "verified": "false",
            "citation": citation,
            "source": "CourtListener",
            "parallel_citations": [],
        }

        try:
            # Clean and prepare the citation for exact matching
            clean_citation = citation.strip("\"'").strip()

            # For v4 API, use the citation as-is with quotes for exact matching
            # Don't remove spaces or convert to uppercase - use the original format

            # Build query parameters for exact match
            params = {
                "q": f'citation:"{clean_citation}"',  # Quote the citation for exact match
                "type": "o",  # Opinions only
                "order_by": "score desc",  # Best match first
                "filed_after": "1750-01-01",  # Include older cases
                "page_size": 1,  # We only need one match for exact search
            }

            # Make the API request to the search endpoint
            response = requests.get(
                f"{self.courtlistener_base_url}/search/",
                headers={
                    k: v for k, v in self.headers.items() if v
                },  # Remove empty headers
                params=params,
                timeout=15,
            )
            response.raise_for_status()

            data = response.json()
            if (
                isinstance(data, dict)
                and data.get("count", 0) > 0
                and isinstance(data.get("results"), list)
                and data["results"]
            ):
                processed_result = self._process_courtlistener_result(
                    citation, data["results"][0]
                )
                if isinstance(processed_result, dict):
                    return processed_result
                else:
                    result["error"] = "Invalid response format from CourtListener"
                    logger.error(
                        f"Unexpected response format from _process_courtlistener_result: {type(processed_result)}"
                    )
            else:
                result["warning"] = "No exact match found in CourtListener"

        except requests.exceptions.RequestException as e:
            error_msg = f"Request to CourtListener failed: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
        except Exception as e:
            error_msg = f"Unexpected error in exact search: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["error"] = error_msg

        return result

    def _search_courtlistener_flexible(self, citation: str) -> dict:
        """
        Perform a more flexible search using citation components.

        Returns:
            dict: A dictionary with verification results, always containing 'verified' and 'citation' keys
        """
        result = {
            "verified": "false",
            "citation": citation,
            "source": "CourtListener",
            "parallel_citations": [],
        }

        try:
            components = self._extract_citation_components(citation)
            if not components:
                result["error"] = "Could not extract citation components"
                return result

            # For v4 API, build a structured query using the components
            search_terms = []

            # Clean and prepare components
            if "volume" in components and components["volume"]:
                search_terms.append(f'citation.volume:{components["volume"]}')

            if "reporter" in components and components["reporter"]:
                # Clean reporter - remove periods and spaces, convert to uppercase
                reporter = (
                    components["reporter"].replace(".", "").replace(" ", "").upper()
                )
                if reporter:  # Only add if not empty after cleaning
                    search_terms.append(f"citation.reporter:{reporter}")

            if "page" in components and components["page"]:
                search_terms.append(f'citation.page:{components["page"]}')

            if not search_terms:
                result["error"] = "No valid search terms could be generated"
                return result

            # Join terms with space for OR logic (more flexible matching)
            search_query = " ".join(search_terms)

            # Set up parameters for v4 API
            params = {
                "q": search_query,
                "type": "o",  # Opinions only
                "order_by": "score desc",  # Best match first
                "filed_after": "1750-01-01",
                "page_size": 5,  # Get more results to find the best match
            }

            # Make the API request to the v4 search endpoint
            response = requests.get(
                f"{self.courtlistener_base_url}/search/",
                headers={
                    k: v for k, v in self.headers.items() if v
                },  # Remove empty headers
                params=params,
                timeout=15,
            )
            response.raise_for_status()

            data = response.json()
            if data.get("count", 0) > 0 and isinstance(data.get("results"), list):
                # Try to find the best match among results
                for result_item in data["results"]:
                    if self._is_best_match(citation, result_item, components):
                        processed = self._process_courtlistener_result(
                            citation, result_item
                        )
                        if isinstance(processed, dict):
                            return processed

                result["warning"] = (
                    "Matching results found but none matched all criteria"
                )
            else:
                result["warning"] = "No matching results found"

        except requests.exceptions.RequestException as e:
            error_msg = f"Request error in flexible search: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
        except Exception as e:
            error_msg = f"Unexpected error in flexible search: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg

        return result

    def _is_best_match(self, citation: str, result: dict, components: dict) -> bool:
        """Determine if a search result is the best match for the citation."""
        # Check if any of the citation fields match exactly
        if (
            "citation" in result
            and result["citation"]
            and citation.lower() in [c.lower() for c in result["citation"].split("; ")]
        ):
            return True

        # Check if the components match
        result_components = self._extract_citation_components(
            result.get("citation", "")
        )
        if not result_components:
            return False

        # Compare key components - ensure both values are strings before comparison
        for key in ["volume", "reporter", "page"]:
            if components.get(key) and result_components.get(key):
                # Convert both values to strings to avoid type comparison errors
                comp_val = str(components[key]).lower()
                result_val = str(result_components[key]).lower()
                if comp_val != result_val:
                    return False

        return True

    def _process_courtlistener_result(
        self, original_citation: str, result: dict
    ) -> dict:
        """
        Process and format CourtListener API result.
        """
        try:
            # Log the raw result for debugging
            self.logger.info(f"[CourtListener] Raw result for '{original_citation}': {json.dumps(result, indent=2)}")
            
            # Check if this is a successful CourtListener response (has absolute_url)
            if result.get("absolute_url"):
                # Extract URL from absolute_url field
                url = f"https://www.courtlistener.com{result.get('absolute_url')}"
                
                # Extract case name from absolute_url (e.g., "/opinion/105221/brown-v-board-of-education/" -> "Brown v. Board of Education")
                case_name = ""
                absolute_url = result.get('absolute_url', '')
                if absolute_url:
                    # Extract the last part of the URL path and convert from kebab-case to Title Case
                    url_parts = absolute_url.strip('/').split('/')
                    if len(url_parts) >= 2:
                        case_slug = url_parts[-1]  # e.g., "brown-v-board-of-education"
                        # Convert kebab-case to Title Case
                        case_name = case_slug.replace('-', ' ').title()
                        # Handle common legal abbreviations
                        case_name = case_name.replace(' V ', ' v. ')
                        case_name = case_name.replace(' V. ', ' v. ')
                
                # Extract date - try multiple possible field names
                canonical_date = ""
                if result.get("date_filed"):
                    canonical_date = result.get("date_filed")
                elif result.get("dateFiled"):
                    canonical_date = result.get("dateFiled")
                elif result.get("date_filed_is_approximate") is False and result.get("date_filed"):
                    canonical_date = result.get("date_filed")
                
                # Log URL extraction
                self.logger.info(f"[CourtListener] URL extraction for '{original_citation}':")
                self.logger.info(f"  - absolute_url field: {result.get('absolute_url', 'NOT_FOUND')}")
                self.logger.info(f"  - Extracted case name: {case_name}")
                self.logger.info(f"  - Extracted date: {canonical_date}")
                self.logger.info(f"  - Final URL: {url}")
                
                processed_result = {
                    "verified": "true",
                    "case_name": case_name,
                    "canonical_name": case_name,  # Use extracted case name as canonical name
                    "citation": result.get("citation", original_citation),
                    "url": url,  # Ensure URL is set
                    "canonical_date": canonical_date,
                    "court": result.get("court", ""),
                    "docket_number": result.get("docket_number", result.get("docketNumber", "")),
                    "source": "CourtListener",
                    "confidence": result.get("confidence", 0.9),
                    "parallel_citations": result.get("parallel_citations", []),
                    "verification_method": "courtlistener_api"
                }
                
                # Log the final processed result
                self.logger.info(f"[CourtListener] Final processed result for '{original_citation}': {json.dumps(processed_result, indent=2)}")
                
                return processed_result
            else:
                # Log failed verification
                error_msg = result.get('error', 'Unknown error')
                self.logger.info(f"[CourtListener] Verification failed for '{original_citation}': {error_msg}")
                return {
                    "verified": "false",
                    "citation": original_citation,
                    "error": error_msg,
                    "source": "CourtListener",
                    "verification_method": "courtlistener_api"
                }
                
        except Exception as e:
            self.logger.error(f"[CourtListener] Error processing result for '{original_citation}': {e}")
            return {
                "verified": "false",
                "citation": original_citation,
                "error": f"Processing error: {str(e)}",
                "source": "CourtListener",
                "verification_method": "courtlistener_api"
            }

    def _verify_with_langsearch(self, citation):
        """Verify a citation using the LangSearch API."""
        if not self.langsearch_api_key:
            return {
                "verified": "false",
                "source": "LangSearch",
                "error": "No API key provided",
            }

        try:
            # Extract components for flexible search
            components = self._extract_citation_components(citation)

            # Build the search query
            query = f"legal citation {components['volume']} {components['reporter']} {components['page']}"
            if components["year"]:
                query += f" {components['year']}"
            if components["court"]:
                query += f" {components['court']}"

            # Make the API request
            headers = {
                "Authorization": f"Bearer {self.langsearch_api_key}",
                "Content-Type": "application/json",
            }
            data = {"query": query, "max_results": 3}
            response = requests.post(
                "https://api.langsearch.ai/v1/search", headers=headers, json=data
            )

            if response.status_code != 200:
                return {
                    "verified": "false",
                    "source": "LangSearch",
                    "error": f"API error: {response.status_code}",
                }

            results = response.json()

            # Check if any results match the citation
            if results.get("results", []):
                for result in results.get("results", []):
                    content = result.get("content", "")
                    # Check if the content contains the citation components
                    if (
                        components["volume"] in content
                        and components["reporter"] in content
                        and components["page"] in content
                    ):
                        return {
                            "verified": "true",
                            "source": "LangSearch",
                            "content": content,
                            "url": result.get("url", ""),
                            "score": result.get("score", 0),
                        }

            return {
                "verified": "false",
                "source": "LangSearch",
                "error": "Citation not found",
            }

        except Exception as e:
            logger.error(f"Error verifying citation '{citation}' with LangSearch: {e}")
            return {"verified": "false", "source": "LangSearch", "error": str(e)}

    def verify_citation(self, *args, **kwargs):
        """Deprecated. Use verify_citation_unified_workflow instead."""
        raise NotImplementedError("verify_citation is deprecated. Use verify_citation_unified_workflow instead.")

    def _check_database(self, citation):
        """
        Check if the citation exists in the database using optimized multi-strategy lookup.

        Args:
            citation (str): The citation to look up

        Returns:
            dict: A dictionary containing the verification result and any matching data
        """
        if not citation or not isinstance(citation, str):
            return {
                "verified": "false",
                "source": "Database",
                "error": "No valid citation provided",
                "citation": "",
            }

        conn = None
        try:
            # Clean and normalize the citation
            normalized_citation = normalize_citation(citation)
            components = self._extract_citation_components(normalized_citation)

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()

            # Optimized single query with multiple strategies
            query = """
                SELECT * FROM citations 
                WHERE citation_text = ? 
                   OR citation_text = ?
                   OR (citation_text LIKE ? AND citation_text LIKE ? AND citation_text LIKE ?)
                ORDER BY 
                    CASE 
                        WHEN citation_text = ? THEN 1
                        WHEN citation_text = ? THEN 2
                        ELSE 3
                    END
                LIMIT 1
            """
            
            # Prepare parameters for the optimized query
            volume_like = f"%{components.get('volume', '')}%" if components.get('volume') else "%"
            reporter_like = f"%{components.get('reporter', '')}%" if components.get('reporter') else "%"
            page_like = f"%{components.get('page', '')}%" if components.get('page') else "%"
            
            params = (
                citation,  # Exact match original
                normalized_citation,  # Exact match normalized
                volume_like, reporter_like, page_like,  # Component match
                citation,  # For ordering
                normalized_citation  # For ordering
            )

            cursor.execute(query, params)
            match = cursor.fetchone()

            if match:
                # Determine match type based on the result
                if match['citation_text'] == citation:
                    match_type = "exact"
                elif match['citation_text'] == normalized_citation:
                    match_type = "normalized"
                else:
                    match_type = "components"
                
                result = self._format_database_match(match, match_type, citation)
                if result.get("verified", False):
                    return result

            return {
                "verified": False,
                "source": "Database",
                "error": "Citation not found in database",
                "citation": citation,
            }

        except Exception as e:
            logger.error(f"Database lookup error for citation '{citation}': {e}")
            return {
                "verified": False,
                "source": "Database",
                "error": f"Database error: {str(e)}",
                "citation": citation,
            }
        finally:
            if conn:
                conn.close()

    def _format_database_match(
        self,
        match,
        match_type,
        original_citation,
        matched_column=None,
        matched_value=None,
    ):
        """
        Format a database match into a standardized result dictionary.
        Ensures that case name and date are applied to parallel citations.

        Args:
            match: The database row (as a dict-like object or dictionary)
            match_type: Type of match (e.g., 'exact', 'normalized', 'components')
            original_citation: The original citation that was searched for
            matched_column: The column or criteria that produced the match
            matched_value: The value that was matched against

        Returns:
            dict: A standardized result dictionary with the match details
        """
        try:
            # Convert SQLite Row to dictionary if needed
            if hasattr(match, "keys"):
                match_dict = dict(match)
            else:
                match_dict = match or {}

            # Safely get the citation value
            citation_value = match_dict.get("citation_text", "")

            # Build the result dictionary
            result = {
                "verified": "true",
                "source": "Database",
                "match_type": match_type,
                "citation": citation_value,
                "original_citation": original_citation,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

            # Add match details if provided
            if matched_column is not None:
                result["matched_column"] = matched_column
            if matched_value is not None:
                result["matched_value"] = matched_value

            # Add all columns from the database to the result
            if hasattr(match, "keys"):
                for key in match.keys():
                    if (
                        key != "id" and key not in result
                    ):  # Skip id and any already set fields
                        result[key] = match[key]
            elif isinstance(match_dict, dict):
                for key, value in match_dict.items():
                    if (
                        key != "id" and key not in result
                    ):  # Skip id and any already set fields
                        result[key] = value

            # Extract year from various sources
            year = ""
            if match_dict.get("year"):
                year = str(match_dict["year"])
            elif match_dict.get("date_filed"):
                try:
                    year_match = re.search(r'(\d{4})', str(match_dict["date_filed"]))
                    if year_match:
                        year = year_match.group(1)
                except Exception as e:
                    logger.warning(f"Error extracting year from date_filed: {e}")

            # Add year to result and metadata
            if year:
                result["year"] = year
                if "metadata" not in result:
                    result["metadata"] = {}
                result["metadata"]["year"] = year

            # Add parallel citations if available
            if "id" in match_dict:
                try:
                    # Create a new connection for parallel citations query
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT citation, reporter, category, year, url, case_name, date_filed 
                        FROM parallel_citations 
                        WHERE citation_id = ?
                    """,
                        (match_dict["id"],),
                    )

                    parallel_cites = []
                    for row in cursor.fetchall():
                        parallel_cite = {
                            "citation": row[0], 
                            "reporter": row[1], 
                            "category": row[2],
                            "url": row[4],
                            "case_name": row[5] if row[5] else match_dict.get("case_name", ""),
                            "date_filed": row[6] if row[6] else match_dict.get("date_filed", "")
                        }
                        # Add year if available
                        if row[3]:
                            parallel_cite["year"] = str(row[3])
                        elif not row[3] and year:
                            parallel_cite["year"] = year
                        parallel_cites.append(parallel_cite)

                    if parallel_cites:
                        result["parallel_citations"] = parallel_cites
                        logger.debug(f"Found {len(parallel_cites)} parallel citations for citation ID {match_dict['id']}")
                    
                    conn.close()
                except Exception as e:
                    logger.warning(f"Error fetching parallel citations: {e}")

            logger.info(
                f"Database match found (type: {match_type}) for citation: {original_citation} -> "
                f"{citation_value} (matched on: {matched_column or 'N/A'}) with year '{year}'"
            )
            return result

        except Exception as e:
            logger.error(f"Error formatting database match: {e}")
            return {
                "verified": False,
                "source": "Database",
                "error": f"Error processing database match: {str(e)}",
                "original_citation": original_citation,
                "match_type": match_type,
            }

    def _verify_with_database(self, citation):
        """
        Try to verify the citation using the database with multiple strategies.

        Args:
            citation (str): The citation to verify

        Returns:
            dict: Verification result with source 'Database' if found, None otherwise
        """
        if not citation or not isinstance(citation, str):
            logger.debug("Invalid citation provided to _verify_with_database")
            return {
                "verified": "false",
                "source": "Database",
                "error": "Invalid citation format",
                "citation": citation,
            }

        try:
            # First try with the exact citation
            result = self._check_database(citation)

            # If we have a verified result, return it
            if result and result.get("verified", False):
                return result

            # If we have an error (not just not found), log it
            if (
                "error" in result
                and "not found" not in str(result.get("error", "")).lower()
            ):
                logger.warning(
                    f"Database lookup error for citation '{citation}': {result.get('error')}"
                )

            # If we got here, no match was found
            return {
                "verified": "false",
                "source": "Database",
                "error": "Citation not found in database",
                "citation": citation,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(
                f"Error in _verify_with_database for citation '{citation}': {str(e)}",
                exc_info=True,
            )
            return {
                "verified": "false",
                "source": "Database",
                "error": f"Error verifying citation: {str(e)}",
                "citation": citation,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

    def _check_landmark_case(self, citation: str) -> Optional[dict]:
        """
        Check if a citation corresponds to a landmark case in our database.
        DEPRECATED: Landmark cases database has been removed as of 2025-05-22.

        Args:
            citation (str): The citation to check

        Returns:
            None: Landmark case checking is deprecated
        """
        # Landmark cases database has been removed
        return None

    def _verify_with_fuzzy_matching(self, citation):
        """Verify citation using fuzzy matching against database."""
        try:
            # This is a placeholder for fuzzy matching implementation
            # Could be implemented with fuzzy string matching against known citations
            return {"verified": "false", "error": "Fuzzy matching not implemented"}
        except Exception as e:
            logger.error(f"Error in fuzzy matching: {e}")
            return {"verified": "false", "error": str(e)}

    def _verify_with_web_search(self, citations) -> dict:
        """
        Verify citation(s) using web search across multiple legal sites.
        This is a fallback when CourtListener API doesn't find the citation.
        
        Args:
            citations (str or list): The citation(s) to verify
        Returns:
            dict: Verification result with case information
        """
        try:
            self.logger.info(f"Attempting web search verification for: {citations}")

            # Support both single citation and list of citations
            if isinstance(citations, str):
                citation_list = [citations]
            else:
                citation_list = citations

            # Try web search for each citation
            results = {}
            
            for citation in citation_list:
                self.logger.info(f"Starting web search for: {citation}")
                
                # Try multiple legal sites
                web_result = self._search_legal_sites(citation)
                
                if web_result and web_result.get('verified') == 'true':
                    results[citation] = web_result
                    self.logger.info(f"✅ Web search found: {citation} -> {web_result.get('case_name', 'N/A')}")
                else:
                    results[citation] = {
                        'verified': 'false',
                        'error': 'Not found in web search',
                        'verification_method': 'web_search'
                    }
                    self.logger.info(f"❌ Not found: {citation}")

            # For single citation, return the result directly
            if isinstance(citations, str):
                return results.get(citations, {'verified': 'false', 'error': 'Search failed'})
            
            # For multiple citations, return the best result or first verified result
            verified_results = [r for r in results.values() if r.get('verified') in ['true', 'true_by_parallel']]
            
            if verified_results:
                # Return the result with the highest confidence
                best_result = max(verified_results, key=lambda x: x.get('confidence', 0))
                return best_result
            
            return {'verified': 'false', 'error': 'No citations verified'}

        except Exception as e:
            self.logger.error(f"Error in _verify_with_web_search: {e}")
            return {
                'verified': False,
                'error': f'Web search error: {str(e)}',
                'verification_method': 'web_search'
            }

    def _search_legal_sites(self, citation: str) -> dict:
        """
        Search multiple legal sites for a citation.
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            from urllib.parse import quote_plus
            import time
            
            # Clean the citation
            clean_citation = citation.strip()
            
            # Try direct citation lookup first (more reliable)
            direct_result = self._direct_citation_lookup(clean_citation)
            if direct_result.get('verified') == 'true':
                return direct_result
            
            # Try Justia first (most reliable for legal citations)
            justia_result = self._search_justia(clean_citation)
            if justia_result.get('verified') == 'true':
                return justia_result
            
            # Try FindLaw
            findlaw_result = self._search_findlaw(clean_citation)
            if findlaw_result.get('verified') == 'true':
                return findlaw_result
            
            # Try Google Scholar
            scholar_result = self._search_google_scholar(clean_citation)
            if scholar_result.get('verified') == 'true':
                return scholar_result
            
            # If none found, return failure
            return {
                'verified': 'false',
                'error': 'Not found in any legal site',
                'verification_method': 'web_search'
            }
            
        except Exception as e:
            self.logger.error(f"Error in _search_legal_sites: {e}")
            return {'verified': 'false', 'error': str(e)}

    def _direct_citation_lookup(self, citation: str) -> dict:
        """
        Try direct citation lookup by constructing URLs based on citation patterns.
        This is more reliable than search pages for known citation formats.
        Also logs which method was attempted for statistics.
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            import re
            
            # Extract citation components
            components = self._extract_citation_components(citation)
            
            # Try Oklahoma Supreme Court cases (P.3d or OK format)
            if self._is_oklahoma_citation(citation):
                result = self._lookup_oklahoma_case(citation, components)
                self._log_lookup_stats(citation, 'oklahoma_direct', result.get('verified', False))
                if result.get('verified'):
                    return result
            
            # Try Illinois official format: 2023 IL 123456
            if re.match(r'\d{4}\s+IL\s+\d+', citation):
                result = self._lookup_state_case_justia(citation, 'illinois', 'IL')
                self._log_lookup_stats(citation, 'illinois_direct', result.get('verified', False))
                if result.get('verified'):
                    return result
            # Try Wisconsin: 2023 WI 12
            if re.match(r'\d{4}\s+WI\s+\d+', citation):
                result = self._lookup_state_case_justia(citation, 'wisconsin', 'WI')
                self._log_lookup_stats(citation, 'wisconsin_direct', result.get('verified', False))
                if result.get('verified'):
                    return result
            # Try Colorado: 2023 CO 15
            if re.match(r'\d{4}\s+CO\s+\d+', citation):
                result = self._lookup_state_case_justia(citation, 'colorado', 'CO')
                self._log_lookup_stats(citation, 'colorado_direct', result.get('verified', False))
                if result.get('verified'):
                    return result
            # Try Utah: 2023 UT 10
            if re.match(r'\d{4}\s+UT\s+\d+', citation):
                result = self._lookup_state_case_justia(citation, 'utah', 'UT')
                self._log_lookup_stats(citation, 'utah_direct', result.get('verified', False))
                if result.get('verified'):
                    return result
            # Add more states as needed...
            
            # Try other state court patterns (placeholder)
            if self._is_state_court_citation(citation):
                self._log_lookup_stats(citation, 'state_court_direct', False)
                return self._lookup_state_court_case(citation, components)
            
            # Try federal court patterns (placeholder)
            if self._is_federal_citation(citation):
                self._log_lookup_stats(citation, 'federal_court_direct', False)
                return self._lookup_federal_case(citation, components)
            
            self._log_lookup_stats(citation, 'no_direct_pattern', False)
            return {'verified': 'false', 'error': 'No direct lookup pattern available'}
        except Exception as e:
            self.logger.error(f"Error in direct citation lookup: {e}")
            return {'verified': 'false', 'error': str(e)}

    def _lookup_state_case_justia(self, citation: str, state_slug: str, state_abbr: str) -> dict:
        """Try to look up a state case on Justia by constructing the URL."""
        try:
            import requests
            from bs4 import BeautifulSoup
            import re
            # Extract year and case number
            match = re.match(r'(\d{4})\s+' + state_abbr + r'\s+(\d+)', citation)
            if not match:
                return {'verified': 'false', 'error': f'Not a {state_abbr} citation'}
            year, case_num = match.groups()
            justia_url = f"https://law.justia.com/cases/{state_slug}/supreme-court/{year}/"
            self.logger.info(f"[{state_abbr} Direct] Trying Justia URL: {justia_url}")
            response = requests.get(justia_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                case_links = soup.find_all('a', href=True)
                for link in case_links:
                    href = link.get('href', '')
                    if case_num in href or citation.replace(' ', '') in href:
                        full_url = f"https://law.justia.com{href}" if href.startswith('/') else href
                        case_response = requests.get(full_url, timeout=10, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        if case_response.status_code == 200:
                            case_soup = BeautifulSoup(case_response.text, 'html.parser')
                            page_text = case_soup.get_text()
                            if citation in page_text or f"{year} {state_abbr} {case_num}" in page_text:
                                title = case_soup.find('h1') or case_soup.find('title')
                                case_name = title.get_text().strip() if title else f"{state_abbr} Supreme Court Case"
                                self.logger.info(f"[{state_abbr} Direct] Found match for '{citation}': {case_name} {full_url}")
                                return {
                                    'verified': 'true',
                                    'case_name': case_name,
                                    'url': full_url,
                                    'source': f'Justia ({state_abbr} Direct)',
                                    'confidence': 0.9,
                                    'verification_method': 'direct_lookup',
                                    'court': f'{state_abbr} Supreme Court',
                                    'year': year
                                }
            return {'verified': 'false', 'error': f'{state_abbr} case not found via direct lookup'}
        except Exception as e:
            self.logger.error(f"Error in {state_abbr} case lookup: {e}")
            return {'verified': 'false', 'error': str(e)}

    def _log_lookup_stats(self, citation: str, method: str, success: bool):
        """Log which lookup method was attempted and whether it succeeded."""
        try:
            import datetime
            with open('lookup_method_stats.log', 'a', encoding='utf-8') as f:
                f.write(f"{datetime.datetime.now().isoformat()}\t{citation}\t{method}\t{success}\n")
        except Exception as e:
            self.logger.error(f"Failed to log lookup stats: {e}")

    def _is_oklahoma_citation(self, citation: str) -> bool:
        """Check if citation is an Oklahoma Supreme Court case."""
        # Oklahoma Supreme Court: 533 P.3d 764, 2023 OK 80, etc.
        ok_patterns = [
            r'\d+\s+P\.\d+\w*\s+\d+',  # P.3d format (fixed to include optional letters)
            r'\d{4}\s+OK\s+\d+',    # OK format
        ]
        return any(re.search(pattern, citation) for pattern in ok_patterns)

    def _is_state_court_citation(self, citation: str) -> bool:
        """Check if citation is a state court case."""
        # Common state court patterns
        state_patterns = [
            r'\d+\s+[A-Z]{2}\s+\d+',  # State abbreviations
            r'\d+\s+[A-Za-z]+\s+\d+',  # State names
        ]
        return any(re.search(pattern, citation) for pattern in state_patterns)

    def _search_findlaw(self, citation: str) -> dict:
        """Search FindLaw for a citation."""
        try:
            import requests
            from bs4 import BeautifulSoup
            from urllib.parse import quote_plus
            
            search_url = f"https://caselaw.findlaw.com/search?query={quote_plus(citation)}"
            
            self.logger.info(f"[FindLaw] Searching for '{citation}' at: {search_url}")
            
            response = requests.get(search_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for search results
                results = soup.select('.search-result') or soup.select('.result')
                
                self.logger.info(f"[FindLaw] Found {len(results)} potential results for '{citation}'")
                
                for result_item in results:
                    result_text = result_item.text.strip()
                    if citation in result_text:
                        # Extract URL
                        link = result_item.find('a')
                        url = link.get('href') if link else None
                        if url and not url.startswith('http'):
                            url = f"https://caselaw.findlaw.com{url}"
                        
                        self.logger.info(f"[FindLaw] Found match for '{citation}':")
                        self.logger.info(f"  - Case name: {result_text}")
                        self.logger.info(f"  - URL: {url}")
                        
                        result = {
                            'verified': 'true',
                            'case_name': result_text,
                            'url': url,
                            'source': 'FindLaw',
                            'confidence': 0.8,
                            'verification_method': 'web_search'
                        }
                        
                        self.logger.info(f"[FindLaw] Final result for '{citation}': {json.dumps(result, indent=2)}")
                        return result
            
            self.logger.info(f"[FindLaw] No match found for '{citation}'")
            return {'verified': 'false', 'error': 'Not found on FindLaw'}
            
        except Exception as e:
            self.logger.error(f"[FindLaw] Error searching for '{citation}': {e}")
            return {'verified': 'false', 'error': str(e)}

    def _search_google_scholar(self, citation: str) -> dict:
        """Search Google Scholar for a citation."""
        try:
            import requests
            from bs4 import BeautifulSoup
            from urllib.parse import quote_plus
            
            search_url = f"https://scholar.google.com/scholar?q={quote_plus(citation)}"
            
            self.logger.info(f"[Google Scholar] Searching for '{citation}' at: {search_url}")
            
            response = requests.get(search_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for search results
                results = soup.select('.gs_r')
                
                self.logger.info(f"[Google Scholar] Found {len(results)} potential results for '{citation}'")
                
                for result_item in results:
                    title_elem = result_item.select_one('.gs_rt')
                    if title_elem:
                        title = title_elem.text.strip()
                        if citation in title:
                            # Extract URL
                            link = title_elem.find('a')
                            url = link.get('href') if link else None
                            
                            self.logger.info(f"[Google Scholar] Found match for '{citation}':")
                            self.logger.info(f"  - Case name: {title}")
                            self.logger.info(f"  - URL: {url}")
                            
                            result = {
                                'verified': 'true',
                                'case_name': title,
                                'url': url,
                                'source': 'Google Scholar',
                                'confidence': 0.7,
                                'verification_method': 'web_search'
                            }
                            
                            self.logger.info(f"[Google Scholar] Final result for '{citation}': {json.dumps(result, indent=2)}")
                            return result
            
            self.logger.info(f"[Google Scholar] No match found for '{citation}'")
            return {'verified': 'false', 'error': 'Not found on Google Scholar'}
            
        except Exception as e:
            self.logger.error(f"[Google Scholar] Error searching for '{citation}': {e}")
            return {'verified': 'false', 'error': str(e)}

    def _parallel_search_legal_sites(self, citation, max_workers=4):
        """
        Search multiple legal sites in parallel for a citation.
        """
        try:
            # For now, use the sequential search but could be enhanced with threading
            return self._search_legal_sites(citation)
        except Exception as e:
            self.logger.error(f"Error in parallel search: {e}")
            return {'verified': 'false', 'error': str(e)}

    def _web_search_hybrid(self, citations, max_results_per_citation=20):
        """
        Hybrid web search combining batch and individual searches.
        """
        try:
            results = {}
            for citation in citations:
                results[citation] = self._search_legal_sites(citation)
            return results
        except Exception as e:
            self.logger.error(f"Error in hybrid search: {e}")
            return {citation: {'verified': 'false', 'error': str(e)} for citation in citations}

    def _create_session(self):
        """Create a requests session with retry logic and timeout."""
        session = requests.Session()
        retry_strategy = Retry(
            total=2,  # Reduced from 3 to fail faster
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504, 522, 524],
            allowed_methods=["GET", "POST"],
            respect_retry_after_header=True,
        )
        timeout = 10  # seconds
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=10, pool_maxsize=10
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        import functools
        session.request = functools.partial(session.request, timeout=timeout)
        if self.courtlistener_api_key:
            session.headers.update(
                {
                    "Authorization": f"Token {self.courtlistener_api_key}",
                    "User-Agent": "CaseStrainer/1.0 (https://github.com/jafrank88/casestrainer; your@email.com)",
                }
            )
        else:
            session.headers.update(
                {
                    "User-Agent": "CaseStrainer/1.0 (https://github.com/jafrank88/casestrainer; your@email.com)"
                }
            )
        return session

    def verify_citation_unified_workflow(self, citation: str, extracted_case_name: str = None, 
                                       hinted_case_name: str = None) -> dict:
        """
        Unified workflow for citation verification with optimized method prioritization.
        """
        try:
            self.logger.info(f"[DEBUG] verify_citation_unified_workflow: Starting verification for citation '{citation}'")
            
            # 1. Extract clean citation string
            clean_citation = self.extract_clean_citation(citation)
            self.logger.info(f"[DEBUG] verify_citation_unified_workflow: Clean citation: '{clean_citation}'")
            
            # 2. Validate citation format
            if not self.is_valid_citation_format(clean_citation):
                self.logger.info(f"[DEBUG] verify_citation_unified_workflow: Invalid citation format, returning error")
                return {
                    "verified": "false",
                    "canonical_citation": clean_citation,
                    "url": None,
                    "extracted_case_name": extracted_case_name,
                    "hinted_case_name": hinted_case_name,
                    "extracted_date": None,
                    "canonical_date": None,
                    "error": "Invalid citation format: Unrecognized citation format",
                    "all_citations": [clean_citation],
                    "primary_citation": clean_citation,
                    "case_name": extracted_case_name or hinted_case_name,
                    "format_analysis": {
                        "format_type": "unknown",
                        "is_valid_format": False,
                        "is_valid_volume": False,
                        "error": "Unrecognized citation format"
                    },
                    "likelihood_score": 0.1,
                    "explanation": "Invalid citation format: Unrecognized citation format"
                }
            
            # 3. Try CourtListener API first (highest success rate)
            self.logger.info(f"[DEBUG] verify_citation_unified_workflow: Trying CourtListener API for '{clean_citation}'")
            courtlistener_result = self._try_courtlistener_api(clean_citation, extracted_case_name, hinted_case_name)
            self.logger.info(f"[DEBUG] verify_citation_unified_workflow: CourtListener result: {json.dumps(courtlistener_result, indent=2)}")
            
            if courtlistener_result.get('verified') == 'true':
                self.logger.info(f"[DEBUG] verify_citation_unified_workflow: CourtListener verification successful, returning result")
                return courtlistener_result
            
            # 4. Try optimized web search with method prioritization
            self.logger.info(f"[DEBUG] verify_citation_unified_workflow: CourtListener failed, trying web search")
            web_search_result = self._optimized_web_search(clean_citation, extracted_case_name)
            if web_search_result.get('verified') == 'true':
                return web_search_result
            
            # 5. Return failure result
            self.logger.info(f"[DEBUG] verify_citation_unified_workflow: All verification methods failed, returning failure result")
            return {
                "verified": "false",
                "canonical_citation": clean_citation,
                "url": None,
                "extracted_case_name": extracted_case_name,
                "hinted_case_name": hinted_case_name,
                "extracted_date": None,
                "canonical_date": None,
                "error": "Citation could not be verified by any source",
                "all_citations": [clean_citation],
                "primary_citation": clean_citation,
                "case_name": extracted_case_name or hinted_case_name,
                "format_analysis": {
                    "format_type": "valid",
                    "is_valid_format": True,
                    "is_valid_volume": True,
                    "error": None
                },
                "likelihood_score": 0.5,
                "explanation": "Citation format is valid but not found in searched databases"
            }
            
        except Exception as e:
            self.logger.error(f"[DEBUG] verify_citation_unified_workflow: Exception occurred: {str(e)}")
            return {
                "verified": "false",
                "canonical_citation": citation,
                "url": None,
                "extracted_case_name": extracted_case_name,
                "hinted_case_name": hinted_case_name,
                "extracted_date": None,
                "canonical_date": None,
                "error": f"Verification error: {str(e)}",
                "all_citations": [citation],
                "primary_citation": citation,
                "case_name": extracted_case_name or hinted_case_name,
                "format_analysis": {
                    "format_type": "error",
                    "is_valid_format": False,
                    "is_valid_volume": False,
                    "error": str(e)
                },
                "likelihood_score": 0.0,
                "explanation": f"Error during verification: {str(e)}"
            }

    def expand_database_from_unverified(self, limit=5):
        """
        Expand the database by attempting to verify unverified citations.
        
        Args:
            limit: Maximum number of citations to attempt to verify
            
        Returns:
            int: Number of citations successfully verified
        """
        try:
            db_manager = get_database_manager()
            
            # Get unverified citations from database
            unverified_citations = db_manager.execute_query(
                "SELECT citation_text FROM citations WHERE found = 0 OR found IS NULL LIMIT ?",
                (limit,)
            )
            
            if not unverified_citations:
                return 0
            
            verified_count = 0
            
            for row in unverified_citations:
                citation_text = row['citation_text']
                
                try:
                    # Attempt to verify the citation
                    result = self.verify_citation_unified_workflow(citation_text)
                    
                    if result.get('verified'):
                        # Update the database with verification result
                        db_manager.execute_query(
                            """
                            UPDATE citations 
                            SET found = 1, 
                                case_name = ?, 
                                confidence = ?, 
                                source = ?, 
                                url = ?,
                                year = ?,
                                date_filed = ?,
                                court = ?,
                                docket_number = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE citation_text = ?
                            """,
                            (
                                result.get('case_name'),
                                0.9 if result.get('verified') else 0.0,
                                result.get('source', 'enhanced_verifier'),
                                result.get('url'),
                                result.get('canonical_date', '').split('-')[0] if result.get('canonical_date') else None,
                                result.get('canonical_date'),
                                result.get('court'),
                                result.get('docket_number'),
                                citation_text
                            )
                        )
                        verified_count += 1
                        
                except Exception as e:
                    self.logger.debug(f"Failed to verify citation {citation_text}: {e}")
                    continue
            
            return verified_count
            
        except Exception as e:
            self.logger.error(f"Database expansion failed: {e}")
            return 0

    def _analyze_citation_format(self, citation_text: str) -> dict:
        """
        Analyze a citation format and determine if it's valid.

        Args:
            citation_text (str): The citation text to analyze

        Returns:
            dict: Analysis result with format type, validity, and details
        """
        # Strip whitespace
        citation = citation_text.strip()

        # Check against each pattern
        for format_type, pattern in CITATION_PATTERNS.items():
            match = re.match(pattern, citation)
            if match:
                # Citation matches this format
                if format_type == "us_reports":
                    volume, page = match.groups()
                    volume_num = int(volume)
                    min_vol, max_vol = VALID_VOLUME_RANGES["us_reports"]
                    is_valid_volume = min_vol <= volume_num <= max_vol
                    details = {
                        "volume": volume_num,
                        "page": int(page),
                        "valid_volume_range": f"{min_vol}-{max_vol}",
                    }

                    result = {
                        "format_type": format_type,
                        "is_valid_format": True,
                        "is_valid_volume": is_valid_volume,
                        "details": details,
                    }

                    if not is_valid_volume:
                        result["volume_error"] = (
                            f"Volume {volume_num} is outside the valid range ({min_vol}-{max_vol}) for {format_type}"
                        )

                    return result

                elif format_type == "federal_reporter":
                    volume, series, page = match.groups()
                    volume_num = int(volume)
                    series_num = int(series)

                    # Check if series is valid - but be more flexible for future series
                    if series_num > 10:  # Allow for future F.4d, F.5d, etc. up to F.10d
                        return {
                            "format_type": format_type,
                            "is_valid_format": True,  # Consider it valid format but with a warning
                            "is_valid_volume": True,  # Consider it valid volume but with a warning
                            "warning": f"Unusual series number: F.{series}d (common series are F.1d, F.2d, and F.3d, but this could be a new series)",
                        }

                    range_key = f"federal_reporter_{series_num}"
                    min_vol, max_vol = VALID_VOLUME_RANGES.get(range_key, (1, 1000))
                    is_valid_volume = min_vol <= volume_num <= max_vol
                    details = {
                        "volume": volume_num,
                        "series": series_num,
                        "page": int(page),
                        "valid_volume_range": f"{min_vol}-{max_vol}",
                    }

                    result = {
                        "format_type": format_type,
                        "is_valid_format": True,
                        "is_valid_volume": is_valid_volume,
                        "details": details,
                    }

                    if not is_valid_volume:
                        result["volume_error"] = (
                            f"Volume {volume_num} is outside the valid range ({min_vol}-{max_vol}) for {format_type} series {series_num}"
                        )

                    return result

                elif format_type == "federal_supplement":
                    volume, series_str, page = match.groups()
                    volume_num = int(volume)
                    series = int(series_str) if series_str else 1

                    # Check volume range based on series
                    range_key = f"federal_supplement_{series}"
                    min_vol, max_vol = VALID_VOLUME_RANGES.get(range_key, (1, 1000))
                    is_valid_volume = min_vol <= volume_num <= max_vol
                    details = {
                        "volume": volume_num,
                        "series": series,
                        "page": int(page),
                        "valid_volume_range": f"{min_vol}-{max_vol}",
                    }

                    result = {
                        "format_type": format_type,
                        "is_valid_format": True,
                        "is_valid_volume": is_valid_volume,
                        "details": details,
                    }

                    if not is_valid_volume:
                        result["volume_error"] = (
                            f"Volume {volume_num} is outside the valid range ({min_vol}-{max_vol}) for {format_type} series {series}"
                        )

                    return result

                # Default for other recognized formats
                return {
                    "format_type": format_type,
                    "is_valid_format": True,
                    "is_valid_volume": True,
                    "details": {
                        "note": "Format recognized but detailed validation not implemented"
                    },
                }

        # If we get here, the format wasn't recognized
        return {
            "format_type": "unknown",
            "is_valid_format": False,
            "is_valid_volume": False,
            "error": "Unrecognized citation format",
        }

    def _calculate_likelihood_score(self, citation_text: str, case_name: str, format_analysis: dict) -> float:
        """
        Calculate the likelihood that a citation is a real case not found in databases
        rather than a hallucination or typo.

        Args:
            citation_text (str): The citation text
            case_name (str): The case name
            format_analysis (dict): The format analysis result

        Returns:
            float: Likelihood score between 0.0 and 1.0
        """
        # Start with a base score based on format validity
        if not format_analysis["is_valid_format"]:
            return 0.1  # Very unlikely to be real if format is invalid

        if not format_analysis["is_valid_volume"]:
            return 0.2  # Unlikely to be real if volume is invalid

        # Base score for valid format
        score = 0.5

        # Adjust score based on format type
        format_type = format_analysis["format_type"]
        if format_type == "us_reports":
            # U.S. Reports are well-documented, so if not found, less likely to be real
            score -= 0.2
        elif format_type in ["federal_reporter", "federal_supplement"]:
            # Federal cases are also well-documented
            score -= 0.1
        elif format_type == "state_reporter":
            # State cases might be less well-documented in some databases
            score += 0.1

        # If we have a case name, it's more likely to be real
        if case_name and len(case_name) > 5:
            score += 0.1

        # Ensure score is between 0.0 and 1.0
        return max(0.0, min(1.0, score))

    def _generate_explanation(self, likelihood_score: float, format_analysis: dict) -> str:
        """
        Generate an explanation for the verification result.

        Args:
            likelihood_score (float): The likelihood score
            format_analysis (dict): The format analysis result

        Returns:
            str: Explanation text
        """
        if not format_analysis["is_valid_format"]:
            return f"Invalid citation format: {format_analysis.get('error', 'Unrecognized format')}"

        if not format_analysis["is_valid_volume"]:
            return f"Invalid volume number: {format_analysis.get('volume_error', 'Volume number out of range')}"

        if likelihood_score < 0.3:
            return "Citation format is valid but likely a hallucination or typo as it does not appear in any legal database and has characteristics of fictional citations."
        elif likelihood_score < 0.6:
            return "Citation format is valid but not found in any legal database. It could be a real case from a less-indexed court or a well-formatted hallucination."
        else:
            return "Citation format is valid and has characteristics of a real case, but was not found in the searched legal databases. It may be from a specialized or historical court not fully indexed in the databases checked."

    def _is_federal_citation(self, citation: str) -> bool:
        """Check if citation is a federal court case."""
        # Federal court patterns
        federal_patterns = [
            r'\d+\s+F\.\d+',  # F.3d, F.2d, F.Supp., etc.
            r'\d+\s+S\.Ct\.',  # Supreme Court
            r'\d+\s+L\.Ed\.',  # Lawyers' Edition
            r'\d+\s+U\.S\.',   # United States Reports
        ]
        return any(re.search(pattern, citation) for pattern in federal_patterns)

    def _search_justia(self, citation: str) -> dict:
        """Search Justia for a citation."""
        try:
            import requests
            from bs4 import BeautifulSoup
            from urllib.parse import quote_plus
            
            # Clean the citation
            clean_citation = citation.strip()
            
            # Search URL
            search_url = f"https://law.justia.com/search?query={quote_plus(clean_citation)}"
            
            # Make request
            response = requests.get(search_url, timeout=10)
            response.raise_for_status()
            
            # Parse results
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for case results
            case_links = soup.find_all('a', href=True)
            for link in case_links:
                href = link.get('href', '')
                if '/cases/' in href and clean_citation.lower() in link.get_text().lower():
                    return {
                        'verified': True,
                        'source': 'Justia',
                        'url': f"https://law.justia.com{href}",
                        'method': 'justia_search'
                    }
            
            return {
                'verified': 'false',
                'source': 'Justia',
                'url': None,
                'method': 'justia_search'
            }
            
        except Exception as e:
            return {
                'verified': 'false',
                'source': 'Justia',
                'url': None,
                'method': 'justia_search',
                'error': str(e)
            }

    def extract_clean_citation(self, citation_obj):
        """Extract clean citation string from various formats."""
        if isinstance(citation_obj, str):
            # Handle eyecite object strings
            if "FullCaseCitation(" in citation_obj:
                match = re.search(r"FullCaseCitation\('([^']+)'", citation_obj)
                return match.group(1) if match else citation_obj
            elif "ShortCaseCitation(" in citation_obj:
                match = re.search(r"ShortCaseCitation\('([^']+)'", citation_obj)
                return match.group(1) if match else citation_obj
            elif "FullLawCitation(" in citation_obj:
                match = re.search(r"FullLawCitation\('([^']+)'", citation_obj)
                return match.group(1) if match else citation_obj
            return citation_obj
        return str(citation_obj)

    def is_valid_citation_format(self, citation: str) -> bool:
        """Flexible citation format validation supporting case names, parallel citations, pinpoints, and hyphenated pages."""
        # Regex for a single citation (volume reporter page, with optional hyphenated page)
        # Updated to handle multi-word reporters like "Wn. App." and "P.3d"
        single_citation = r"\d+\s+[A-Za-z\.\s]+\s+\d+(?:-\d+)?"
        # Allow pinpoint pages (just numbers, optionally hyphenated)
        pinpoint_page = r"\d+(?:-\d+)?"
        # Allow multiple citations, each optionally followed by pinpoint pages
        citations_group = rf"({single_citation}(?:,\s*{pinpoint_page})*(?:,\s*{single_citation}(?:,\s*{pinpoint_page})*)*)"
        # Optional case name at the start, ending with a comma
        case_name = r"(?:[\w\s\.\'\-]+?,\s*)?"
        # Trailing year in parentheses
        year = r"\(\d{4}\)"
        # Full pattern: [case name,] citation[, pinpoint ...][, citation[, pinpoint ...]] (year)
        pattern = rf"^{case_name}{citations_group}\s*{year}$"
        
        # Test the pattern
        if re.match(pattern, citation.strip()):
            return True
            
        # Also accept if any citation in the string matches the old patterns (for backward compatibility)
        legacy_patterns = [
            r'\d+\s+[A-Z]+\.[\d]*\s+\d+',  # Standard reporter format (F.3d, F.Supp., etc.)
            r'\d+\s+[A-Z]{2}\s+\d+',       # State court format (OK 80, etc.)
            r'\d+\s+U\.S\.\s+\d+',         # Supreme Court
            r'\d+\s+S\.Ct\.\s+\d+',        # Supreme Court Reporter
            r'\d+\s+L\.Ed\.\d*\s+\d+',     # Lawyers' Edition
            r'\d+\s+U\.S\.C\.\s+§\s+\d+',  # U.S. Code
            r'\d+\s+[A-Z]+\s+\d+',         # General reporter format
            r'\d+\s+[A-Z]+\.[A-Z]+\s+\d+', # Multi-letter reporter (N.J.Super., etc.)
            r'\d+\s+Wn\.\s*App\.\s+\d+',   # Washington App
            r'\d+\s+P\.\d+\s+\d+',         # Pacific reporter
        ]
        
        for legacy in legacy_patterns:
            if re.search(legacy, citation):
                return True
        return False

    def _try_courtlistener_api(self, citation: str, extracted_case_name: str = None, hinted_case_name: str = None) -> dict:
        """Try CourtListener API with optimized approach."""
        try:
            # Use the existing CourtListener verification method
            self.logger.info(f"[DEBUG] _try_courtlistener_api: Starting verification for citation '{citation}' with extracted_name='{extracted_case_name}', hinted_name='{hinted_case_name}'")
            result = self._verify_with_courtlistener(citation)
            self.logger.info(f"[DEBUG] _try_courtlistener_api: _verify_with_courtlistener returned: {json.dumps(result, indent=2)}")
            
            if result.get('verified') == 'true':
                self.logger.info(f"[DEBUG] _try_courtlistener_api: Verification successful, returning result with canonical_name: {result.get('canonical_name', 'NOT_FOUND')}")
                result['verification_method'] = 'courtlistener_api'
                # Include the extracted and hinted case names in the result
                result['extracted_case_name'] = extracted_case_name
                result['hinted_case_name'] = hinted_case_name
                return result
            else:
                self.logger.info(f"[DEBUG] _try_courtlistener_api: Verification failed, returning {'verified': 'false'}")
                return {
                    'verified': 'false',
                    'extracted_case_name': extracted_case_name,
                    'hinted_case_name': hinted_case_name
                }
        except Exception as e:
            self.logger.debug(f"CourtListener API failed for {citation}: {e}")
            return {
                'verified': 'false',
                'extracted_case_name': extracted_case_name,
                'hinted_case_name': hinted_case_name
            }

    def _optimized_web_search(self, citation: str, case_name: str = None) -> dict:
        """Optimized web search with method prioritization."""
        try:
            # Use optimized web searcher if available
            if self.optimized_searcher:
                # Run async search in sync context
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If we're already in an async context, create a new thread
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(
                                asyncio.run,
                                self.optimized_searcher.search_parallel(citation, case_name, max_workers=3)
                            )
                            result = future.result()
                    else:
                        # We can run async directly
                        result = loop.run_until_complete(
                            self.optimized_searcher.search_parallel(citation, case_name, max_workers=3)
                        )
                    
                    if result.get('verified') == 'true':
                        result['verification_method'] = method_name
                        return result
                except Exception as e:
                    self.logger.debug(f"Optimized searcher failed: {e}")
            
            # Fallback to original methods if optimized searcher is not available
            search_methods = []
            
            # Check if it's a state court citation
            if self._is_state_court_citation(citation):
                search_methods.extend([
                    ('justia', self._search_justia),
                    ('findlaw', self._search_findlaw),
                    ('google_scholar', self._search_google_scholar)
                ])
            else:
                # For federal citations, try Google Scholar first
                search_methods.extend([
                    ('google_scholar', self._search_google_scholar),
                    ('justia', self._search_justia),
                    ('findlaw', self._search_findlaw)
                ])
            
            # Try each method in order
            for method_name, method_func in search_methods:
                try:
                    result = method_func(citation)
                    if result.get('verified'):
                        result['verification_method'] = method_name
                        return result
                except Exception as e:
                    self.logger.debug(f"Method {method_name} failed for {citation}: {e}")
                    continue
            
            return {'verified': 'false'}
            
        except Exception as e:
            self.logger.debug(f"Optimized web search failed for {citation}: {e}")
            return {'verified': 'false'}

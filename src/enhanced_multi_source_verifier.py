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
from typing import Dict, Any, Optional, List, Tuple
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

# Configure logging
logger = logging.getLogger(__name__)

class RateLimitError(Exception):
    pass

# Add at the top with other imports
try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DDGS = None
    DUCKDUCKGO_AVAILABLE = False

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

    def _normalize_citation(self, citation):
        """Normalize citation format for better matching.

        This method normalizes citations by:
        1. Removing extra whitespace
        2. Applying Washington citation spacing rules
        3. Standardizing Washington citations (Wn. -> Wash.)
        4. Preserving reporter series (e.g., P.3d, F.4th)
        5. Handling international citations
        6. Standardizing regional reporters
        7. Handling edge cases and variations

        Args:
            citation (str): The citation to normalize

        Returns:
            str: The normalized citation
        """
        if not citation or not isinstance(citation, str):
            return ""

        # Replace multiple spaces with a single space and trim
        normalized = re.sub(r"\s+", " ", citation.strip())

        # Apply Washington citation spacing rules
        normalized = apply_washington_spacing_rules(normalized)

        # Normalize Washington citations (Wn. -> Wash.) - IMPROVED
        normalized = re.sub(r"Wn\.\s*App\.", "Wash. App.", normalized)
        normalized = re.sub(r"Wn\.\s*2d", "Wash. 2d", normalized)
        normalized = re.sub(r"Wn\.\s*3d", "Wash. 3d", normalized)
        normalized = re.sub(r"Wn\.", "Wash.", normalized)

        # Standardize regional reporters
        normalized = re.sub(r"Cal\.\s*App\.", "Cal. App.", normalized)
        normalized = re.sub(r"Cal\.\s*Rptr\.", "Cal. Rptr.", normalized)
        normalized = re.sub(r"N\.Y\.\s*App\.", "N.Y. App.", normalized)
        normalized = re.sub(r"Tex\.\s*App\.", "Tex. App.", normalized)
        normalized = re.sub(r"Fla\.\s*App\.", "Fla. App.", normalized)
        normalized = re.sub(r"Ill\.\s*App\.", "Ill. App.", normalized)
        normalized = re.sub(r"Ohio\s*App\.", "Ohio App.", normalized)
        normalized = re.sub(r"Mich\.\s*App\.", "Mich. App.", normalized)
        normalized = re.sub(r"Pa\.\s*Super\.", "Pa. Super.", normalized)
        normalized = re.sub(r"Mass\.\s*App\.", "Mass. App.", normalized)

        # Handle international citations
        normalized = re.sub(r"UKSC", "UKSC", normalized)  # UK Supreme Court
        normalized = re.sub(r"EWCA\s+Civ", "EWCA Civ", normalized)  # England and Wales Court of Appeal
        normalized = re.sub(r"EWHC", "EWHC", normalized)  # England and Wales High Court
        normalized = re.sub(r"SCC", "SCC", normalized)  # Supreme Court of Canada
        normalized = re.sub(r"FCA", "FCA", normalized)  # Federal Court of Appeal (Canada)
        normalized = re.sub(r"FC", "FC", normalized)  # Federal Court (Canada)
        normalized = re.sub(r"HCA", "HCA", normalized)  # High Court of Australia
        normalized = re.sub(r"FCA", "FCA", normalized)  # Federal Court of Australia

        # Handle special characters and edge cases
        normalized = re.sub(r"[\u2013\u2014]", "-", normalized)  # Replace em/en dashes with hyphens
        normalized = re.sub(r"[\u2018\u2019]", "'", normalized)  # Replace smart quotes
        normalized = re.sub(r"[\u201C\u201D]", '"', normalized)  # Replace smart quotes
        normalized = re.sub(r"[\u00A0]", " ", normalized)  # Replace non-breaking spaces

        # Clean up common formatting issues
        normalized = re.sub(r"\s*,\s*", ", ", normalized)  # Standardize commas
        normalized = re.sub(r"\s+v\.?\s+", " v. ", normalized)  # Standardize v.
        normalized = re.sub(r"\s+&\.?\s+", " & ", normalized)  # Standardize &
        normalized = re.sub(r"\s+vs\.?\s+", " v. ", normalized)  # Standardize vs.
        normalized = re.sub(r"\s+versus\s+", " v. ", normalized)  # Standardize versus

        # Handle parentheses and brackets
        normalized = re.sub(r"\(\s*", "(", normalized)  # Remove space after opening parenthesis
        normalized = re.sub(r"\s*\)", ")", normalized)  # Remove space before closing parenthesis
        normalized = re.sub(r"\[\s*", "[", normalized)  # Remove space after opening bracket
        normalized = re.sub(r"\s*\]", "]", normalized)  # Remove space before closing bracket

        # Handle periods and abbreviations
        normalized = re.sub(r"\.\s*\.", "..", normalized)  # Fix double periods
        normalized = re.sub(r"\.\s*\.\s*\.", "...", normalized)  # Fix triple periods

        return normalized

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

            # Handle parallel citations (e.g., "123 Wn.2d 456, 789 P.2d 123")
            if "," in citation:
                parts = [p.strip() for p in citation.split(",")]
                if len(parts) > 1 and any(p[0].isdigit() for p in parts[1:]):
                    components["parallel_citations"] = [
                        p.strip() for p in parts[1:] if p.strip()
                    ]
                    citation = parts[0]  # Process the first citation normally

            # Enhanced volume, reporter, and page extraction
            # Handle various formats including regional reporters
            patterns = [
                # Standard format: 123 Wn.2d 456
                r"(\d+)\s+([A-Za-z\.\s]+?)(?:\s+(\d+))?(?:\s*,\s*(\d+))?",
                # Federal format: 123 F.3d 456
                r"(\d+)\s+(F\.\d+[a-z]?)\s+(\d+)",
                # Regional format: 123 Cal. App. 4th 456
                r"(\d+)\s+([A-Za-z\.\s]+?)\s+(\d+[a-z]+)\s+(\d+)",
                # State format: 123 P.3d 456
                r"(\d+)\s+([A-Z]\.\d+[a-z]?)\s+(\d+)",
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

            # Clean up reporter abbreviation
            components["reporter"] = (
                components["reporter"].replace(" ", "").replace("..", ".")
            )

        except Exception as e:
            logger.warning(
                f"Error extracting citation components from '{citation}': {e}"
            )

        return components

    def _check_cache(self, citation):
        """Check if the citation is in the cache."""
        cache_file = os.path.join(
            self.cache_dir,
            f"{self._normalize_citation(citation).replace(' ', '_')}.json",
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
            f"{self._normalize_citation(citation).replace(' ', '_')}.json",
        )
        try:
            with open(cache_file, "w") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache for citation '{citation}': {e}")

    def _save_to_database(self, citation, result):
        """
        Save the verification result to the database, including parallel citations and year metadata.

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
                        # Extract year from parallel citation if available
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
                        # Insert or update the parallel citation with url
                        db_manager.execute_query(
                            """
                            INSERT INTO parallel_citations (
                                citation_id, citation, reporter, category, year, url
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            ON CONFLICT(citation_id, citation, url) DO UPDATE SET
                                reporter = excluded.reporter,
                                category = excluded.category,
                                year = excluded.year,
                                url = excluded.url
                            """,
                            (
                                citation_id,
                                cite,
                                parallel.get("reporter", ""),
                                parallel.get("category", ""),
                                parallel_year,
                                url,
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

        # Handle common citation formats
        # 1. Standard format: 123 F.4th 456
        # 2. With comma: 123 F.4th 456, 789
        # 3. With 'at': 123 F.4th 456, at 789
        parts = []
        for part in clean.split():
            # Remove any non-alphanumeric characters except periods and hyphens
            part = "".join(c for c in part if c.isalnum() or c in ".-")
            if part and part.lower() not in [
                "at",
                "p.",
            ]:  # Skip common connecting words
                parts.append(part)

        # Rejoin with single spaces
        return " ".join(parts)

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
                        "verified": False,
                        "citation": clean_citation,
                        "error": error_msg,
                        "source": "CourtListener API",
                    }

                # Process the response based on the API version and structure
                if not data:
                    error_msg = "Empty response from API"
                    logger.warning(f"{error_msg} for citation: {clean_citation}")
                    return {
                        "verified": False,
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
                        
                        if result and result.get("verified", False):
                            logger.info(f"Successfully verified citation via lookup: {clean_citation}")
                            return result
                        else:
                            error_msg = result.get("error", "Citation not found in CourtListener") if result else "No valid clusters found"
                            logger.info(f"Citation not found via lookup: {clean_citation} - {error_msg}")
                            return {
                                "verified": False,
                                "citation": clean_citation,
                                "error": error_msg,
                                "source": "CourtListener API",
                            }
                    else:
                        error_msg = citation_data.get("error_message", "Citation lookup failed")
                        logger.info(f"Citation lookup failed: {clean_citation} - {error_msg}")
                        return {
                            "verified": False,
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
                        "verified": False,
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
                    "verified": False,
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
        Verify a citation using the CourtListener API v4.
        Uses a two-step process:
        1. Citation-lookup to confirm case exists
        2. Search API to get full canonical information (URL, case name, year, parallel citations)
        """
        self.citations_checked_cl.append(citation)
        self.citation_paths.setdefault(citation, []).append("CL")
        # Try the original and all normalized forms
        tried_citations = set()
        candidates = [citation]
        # Add normalized forms (e.g., Wn.2d -> Wash. 2d)
        norm_syn = normalize_washington_synonyms(citation)
        if norm_syn != citation:
            candidates.append(norm_syn)
        # Add cleaned version
        cleaned = self._clean_citation_for_lookup(citation)
        if cleaned != citation and cleaned not in candidates:
            candidates.append(cleaned)
        # Try all parallel citations if present
        components = self._extract_citation_components(citation)
        if components.get("parallel_citations"):
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
            
            if lookup_result and lookup_result.get("verified", False):
                # Step 2: If citation-lookup is positive, use search API to get full canonical info
                logger.info(f"[CourtListener] Citation-lookup positive for '{cand}', now getting canonical info via search API")
                search_result = self._search_courtlistener_exact(cand)
                logger.info(f"[CourtListener] Search API result for '{cand}': {json.dumps(search_result, default=str)[:500]}")
                
                if search_result and search_result.get("verified", False):
                    # We have both confirmation and canonical info
                    return search_result
                else:
                    # Citation-lookup was positive but search failed, return lookup result
                    logger.warning(f"[CourtListener] Citation-lookup positive but search API failed for '{cand}', using lookup result")
                    return lookup_result
            
            # If citation-lookup failed, try flexible search as fallback
            flexible_result = self._search_courtlistener_flexible(cand)
            logger.info(f"[CourtListener] Flexible Search result for '{cand}': {json.dumps(flexible_result, default=str)[:500]}")
            if flexible_result.get("verified", False) and flexible_result.get("case_name") and flexible_result["case_name"] != "Unknown Case":
                return flexible_result
        
        # If all else fails, return the best available (even if not verified)
        # Try the original as fallback
        processed = self._process_courtlistener_result(citation, self._lookup_citation(citation))
        if processed:
            return processed
        return {
            "verified": False,
            "citation": citation,
            "case_name": "Unknown Case",
            "date_filed": None,
            "parallel_citations": [],
            "source": "CourtListener",
            "error": "No match found in CourtListener API after all forms tried"
        }

    def _search_courtlistener_exact(self, citation: str) -> dict:
        """Search for an exact citation match in CourtListener.

        Returns:
            dict: A dictionary with verification results, always containing 'verified' and 'citation' keys
        """
        result = {
            "verified": False,
            "citation": citation,
            "source": "CourtListener",
            "parallel_citations": [],
        }

        try:
            # Set up headers if not already set
            if not hasattr(self, "headers"):
                self.headers = {
                    "Authorization": (
                        f"Token {self.courtlistener_api_key}"
                        if self.courtlistener_api_key
                        else ""
                    ),
                    "Content-Type": "application/json",
                }

            # Set base URL if not already set
            if not hasattr(self, "courtlistener_base_url"):
                self.courtlistener_base_url = (
                    "https://www.courtlistener.com/api/rest/v4"
                )

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
            "verified": False,
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
        """Process CourtListener API result with enhanced date extraction."""
        try:
            # Extract case information with fallbacks for different API versions
            case_name = (
                result.get("caseName")
                or result.get("name")
                or self._extract_case_name_from_cluster(result)
                or "Unknown Case"
            )
            docket_number = result.get("docketNumber") or result.get(
                "docket_number", ""
            )

            # Handle court information which might be a string or object
            court = ""
            court_data = result.get("court") or {}
            if isinstance(court_data, dict):
                court = court_data.get("name") or court_data.get("full_name") or ""
            elif isinstance(court_data, str):
                court = court_data

            # Get the main citation, falling back to the original if not found
            citation = result.get("citation") or original_citation

            # Extract parallel citations if available
            parallel_citations = []
            if "parallel_citations" in result and isinstance(
                result["parallel_citations"], list
            ):
                parallel_citations = result["parallel_citations"]
            elif "citations" in result and isinstance(
                result["citations"], list
            ):
                parallel_citations = result["citations"]

            # Get the URL, falling back to resource_uri or absolute_url
            url = result.get("absolute_url") or result.get(
                "resource_uri", ""
            )
            if url and not url.startswith(("http://", "https://")):
                url = f"https://www.courtlistener.com{url}"

            # Enhanced date extraction with multiple fallbacks
            date_filed = self._extract_date_with_fallbacks(result, original_citation)
            
            # Extract additional metadata
            opinion_type = result.get("type") or result.get("opinion_type", "")
            precedential = result.get("precedential", True)
            
            # Extract judge information if available
            judge = ""
            judge_data = result.get("judges") or result.get("judge", "")
            if isinstance(judge_data, list) and judge_data:
                judge = judge_data[0].get("name", "") if isinstance(judge_data[0], dict) else str(judge_data[0])
            elif isinstance(judge_data, str):
                judge = judge_data

            return {
                "verified": True,
                "case_name": case_name,
                "citation": citation,
                "parallel_citations": parallel_citations,
                "url": url,
                "date_filed": date_filed,
                "court": court,
                "docket_number": docket_number,
                "opinion_type": opinion_type,
                "precedential": precedential,
                "judge": judge,
                "source": "courtlistener",
                "confidence": 0.95,
            }

        except Exception as e:
            self.logger.error(f"Error processing CourtListener result: {e}")
            return {
                "verified": False,
                "error": f"Failed to process CourtListener result: {str(e)}",
                "source": "courtlistener",
            }
    
    def _extract_case_name_from_cluster(self, cluster_data: dict) -> str:
        """Extract case name from cluster data by fetching the opinion details."""
        try:
            # Try to get case name from sub_opinions if available
            if "sub_opinions" in cluster_data and cluster_data["sub_opinions"]:
                opinion_url = cluster_data["sub_opinions"][0]
                if isinstance(opinion_url, str):
                    # Fetch the opinion details to get the case name
                    opinion_data = self._fetch_opinion_details(opinion_url)
                    if opinion_data and opinion_data.get("case_name"):
                        return opinion_data["case_name"]
            
            # Try to extract from absolute_url if it contains the case name
            absolute_url = cluster_data.get("absolute_url", "")
            if absolute_url and "/opinion/" in absolute_url:
                # URL format: /opinion/105221/brown-v-board-of-education/
                parts = absolute_url.split("/")
                if len(parts) >= 4:
                    case_slug = parts[-2]  # Get the last part before trailing slash
                    if case_slug and case_slug != "opinion":
                        # Convert slug to readable case name
                        case_name = case_slug.replace("-", " ").title()
                        return case_name
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"Error extracting case name from cluster: {e}")
            return ""
    
    def _fetch_opinion_details(self, opinion_url: str) -> dict:
        """Fetch opinion details from CourtListener API."""
        try:
            if not opinion_url.startswith("http"):
                opinion_url = f"https://www.courtlistener.com{opinion_url}"
            
            headers = {
                "Authorization": f"Token {self.courtlistener_api_key}" if self.courtlistener_api_key else "",
                "Content-Type": "application/json"
            }
            headers = {k: v for k, v in headers.items() if v}
            
            response = requests.get(opinion_url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            
        except Exception as e:
            self.logger.debug(f"Error fetching opinion details: {e}")
        
        return {}
    
    def _extract_date_with_fallbacks(self, citation_data: dict, original_citation: str) -> str:
        """Extract date with multiple fallback methods."""
        # Try multiple date fields from CourtListener
        date_fields = [
            "date_filed",
            "dateFiled", 
            "date_created",
            "dateCreated",
            "date_modified",
            "dateModified",
            "date_published",
            "datePublished",
            "filed_date",
            "filedDate"
        ]
        
        for field in date_fields:
            date_value = citation_data.get(field)
            if date_value:
                # Try to parse the date
                parsed_date = self._parse_date_string(date_value)
                if parsed_date:
                    return parsed_date
        
        # If no date found in API response, try to extract from citation context
        # This would require additional context from the document
        return ""
    
    def _parse_date_string(self, date_string: str) -> str:
        """Parse various date string formats."""
        if not date_string:
            return ""
        
        try:
            # Handle ISO format dates
            if isinstance(date_string, str) and 'T' in date_string:
                from datetime import datetime
                dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            
            # Handle timestamp
            if isinstance(date_string, (int, float)):
                from datetime import datetime
                dt = datetime.fromtimestamp(date_string)
                return dt.strftime('%Y-%m-%d')
            
            # Handle common date formats
            import re
            date_patterns = [
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
                r'(\d{1,2})-(\d{1,2})-(\d{4})',  # MM-DD-YYYY
                r'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, str(date_string))
                if match:
                    if len(match.groups()) == 3:
                        if len(match.group(1)) == 4:  # YYYY-MM-DD or YYYY/MM/DD
                            year, month, day = match.groups()
                        else:  # MM/DD/YYYY or MM-DD-YYYY
                            month, day, year = match.groups()
                        
                        # Ensure proper formatting
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # If it's already in a good format, return as is
            if re.match(r'\d{4}-\d{2}-\d{2}', str(date_string)):
                return str(date_string)
                
        except Exception as e:
            self.logger.debug(f"Error parsing date string '{date_string}': {e}")
        
        return ""

    def _verify_with_langsearch(self, citation):
        """Verify a citation using the LangSearch API."""
        if not self.langsearch_api_key:
            return {
                "verified": False,
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
                    "verified": False,
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
                            "verified": True,
                            "source": "LangSearch",
                            "content": content,
                            "url": result.get("url", ""),
                            "score": result.get("score", 0),
                        }

            return {
                "verified": False,
                "source": "LangSearch",
                "error": "Citation not found",
            }

        except Exception as e:
            logger.error(f"Error verifying citation '{citation}' with LangSearch: {e}")
            return {"verified": False, "source": "LangSearch", "error": str(e)}

    def verify_citation(
        self,
        citation,
        extracted_case_name=None,  # Add parameter for extracted case name
        use_cache=True,
        use_database=False,  # Changed default to False - database only for archiving
        use_api=True,
        force_refresh=False,
    ):
        """
        Verify a citation using the unified workflow.
        
        This method now uses the most efficient approach:
        1. CourtListener API first (fastest, most reliable)
        2. Web search only if needed
        
        Args:
            citation (str): The citation to verify
            extracted_case_name (str): Case name extracted from document (optional)
            use_cache (bool): Whether to use cache (default: True)
            use_database (bool): Whether to use database (default: False)
            use_api (bool): Whether to use API (default: True)
            force_refresh (bool): Whether to force refresh cache (default: False)
            
        Returns:
            dict: Verification result with case information
        """
        # Use the unified workflow for single citation
        return self.verify_citation_unified_workflow(
            citation,
            extracted_case_name=extracted_case_name,
            use_cache=use_cache,
            use_database=use_database,
            use_api=use_api,
            force_refresh=force_refresh
        )

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
                "verified": False,
                "source": "Database",
                "error": "No valid citation provided",
                "citation": "",
            }

        conn = None
        try:
            # Clean and normalize the citation
            normalized_citation = self._normalize_citation(citation)
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
                "verified": True,
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
                        SELECT citation, reporter, category, year, url 
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
                            "url": row[4]
                        }
                        # Add year if available
                        if row[3]:
                            parallel_cite["year"] = str(row[3])
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
                "verified": False,
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
                "verified": False,
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
                "verified": False,
                "source": "Database",
                "error": f"Error verifying citation: {str(e)}",
                "citation": citation,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }

    # Landmark cases functionality has been removed as it's no longer maintained

    def _verify_with_fuzzy_matching(self, citation):
        """Verify citation using fuzzy matching against database."""
        try:
            # This is a placeholder for fuzzy matching implementation
            # Could be implemented with fuzzy string matching against known citations
            return {"verified": False, "error": "Fuzzy matching not implemented"}
        except Exception as e:
            logger.error(f"Error in fuzzy matching: {e}")
            return {"verified": False, "error": str(e)}

    def _verify_with_web_search(self, citations) -> dict:
        """
        Verify citation(s) using parallel web search across multiple legal sites.
        Args:
            citations (str or list): The citation(s) to verify
        Returns:
            dict: Verification result with case information
        """
        try:
            logger.info(f"Attempting parallel web search verification for: {citations}")

            # Support both single citation and list of citations
            if isinstance(citations, str):
                citation_list = [citations]
            else:
                citation_list = citations

            # Use parallel search for each citation
            results = {}
            
            for citation in citation_list:
                logger.info(f"Starting parallel search for: {citation}")
                
                # Try parallel search first (fastest and most efficient)
                parallel_result = self._parallel_search_legal_sites(citation, max_workers=4)
                
                if parallel_result and parallel_result.get('verified', False):
                    results[citation] = parallel_result
                    logger.info(f"✅ Parallel search found: {citation} -> {parallel_result.get('canonical_name', 'N/A')}")
                else:
                    # Fallback to hybrid search if parallel search fails
                    logger.info(f"Parallel search failed for {citation}, trying hybrid search")
                    hybrid_result = self._web_search_hybrid([citation], max_results_per_citation=20)
                    
                    if citation in hybrid_result and hybrid_result[citation].get('verified', False):
                        results[citation] = hybrid_result[citation]
                        logger.info(f"✅ Hybrid search found: {citation}")
                    else:
                        results[citation] = {
                            'verified': False,
                            'error': 'Not found in parallel or hybrid search',
                            'verification_method': 'web_search'
                        }
                        logger.info(f"❌ Not found: {citation}")

            # For single citation, return the result directly
            if isinstance(citations, str):
                return results.get(citations, {'verified': False, 'error': 'Search failed'})
            
            # For multiple citations, return the best result or first verified result
            verified_results = [r for r in results.values() if r.get('verified', False)]
            
            if verified_results:
                # Return the result with the highest confidence or from the best site
                best_result = max(verified_results, key=lambda x: (
                    x.get('has_complete_metadata', False),
                    x.get('has_full_text', False),
                    x.get('confidence', 'low') == 'high'
                ))
                return best_result
            
            return {'verified': False, 'error': 'No citations verified'}

        except Exception as e:
            logger.error(f"Error in _verify_with_web_search: {e}")
            return {
                'verified': False,
                'error': f'Web search error: {str(e)}',
                'verification_method': 'web_search'
            }

    def _parallel_search_legal_sites(self, citation, max_workers=4):
        """
        Search multiple legal sites in parallel for a citation.
        """
        try:
            # This is a placeholder for parallel search implementation
            # Could be implemented with concurrent.futures.ThreadPoolExecutor
            return {'verified': False, 'error': 'Parallel search not implemented'}
        except Exception as e:
            logger.error(f"Error in parallel search: {e}")
            return {'verified': False, 'error': str(e)}

    def _web_search_hybrid(self, citations, max_results_per_citation=20):
        """
        Hybrid web search combining batch and individual searches.
        """
        try:
            # This is a placeholder for hybrid search implementation
            # Could combine batch search with individual fallback
            return {citation: {'verified': False, 'error': 'Hybrid search not implemented'} for citation in citations}
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return {citation: {'verified': False, 'error': str(e)} for citation in citations}

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

    def verify_citation_unified_workflow(
        self,
        citation,
        extracted_case_name=None,
        use_cache=True,
        use_database=False,
        use_api=True,
        force_refresh=False,
        full_text=None,  # Add full_text parameter for case name extraction
    ):
        """
        Unified workflow for verifying a citation using multiple sources.
        Tries CourtListener API, then database, then web search.
        Returns a dict with canonical_citation, url, and other metadata.
        """
        # Initialize result with extracted information
        base_result = {
            "verified": False,
            "canonical_citation": citation,
            "url": None,
            "extracted_case_name": extracted_case_name,
            "hinted_case_name": None,  # Will be set if we can extract from context
            "extracted_date": None,    # Will be set if we can extract from context
            "canonical_date": None,    # Will be set from verified source
            "error": "Citation could not be verified by any source."
        }
        
        # Extract case names if full_text is provided
        if full_text:
            try:
                from src.case_name_extraction_core import extract_case_name_from_text, extract_case_name_hinted
                
                # Extract case name from text context
                extracted_name = extract_case_name_from_text(full_text, citation)
                if extracted_name:
                    base_result["extracted_case_name"] = extracted_name
                
                # Get canonical name first (needed for hinted extraction)
                canonical_name = None
                if use_api:
                    # Try to get canonical name from CourtListener
                    result = self._verify_with_courtlistener(citation)
                    if result.get("verified"):
                        canonical_name = result.get("case_name")
                
                # Extract hinted case name if we have canonical name
                if canonical_name:
                    hinted_name = extract_case_name_hinted(full_text, citation, canonical_name)
                    if hinted_name:
                        base_result["hinted_case_name"] = hinted_name
                        
            except Exception as e:
                self.logger.debug(f"Error extracting case names: {e}")
        
        # Try to extract hinted case name and date from citation context
        if extracted_case_name:
            base_result["hinted_case_name"] = extracted_case_name
        
        # Extract date from citation if possible (e.g., "640 P.2d 716 (1982)")
        import re
        date_match = re.search(r'\((\d{4})\)', citation)
        if date_match:
            base_result["extracted_date"] = date_match.group(1)
        
        # 1. Try CourtListener API
        if use_api:
            result = self._verify_with_courtlistener(citation)
            if result.get("verified"):
                # Merge with base result
                base_result.update(result)
                base_result["canonical_citation"] = result.get("citation", citation)
                base_result["url"] = result.get("opinion_url") or result.get("url")
                base_result["canonical_date"] = result.get("date_filed")
                base_result["verified"] = True
                return base_result
        
        # 2. Try database
        if use_database:
            result = self._check_database(citation)
            if result.get("verified"):
                # Merge with base result
                base_result.update(result)
                base_result["canonical_citation"] = result.get("citation", citation)
                base_result["url"] = result.get("opinion_url") or result.get("url")
                base_result["canonical_date"] = result.get("date_filed")
                base_result["verified"] = True
                return base_result
        
        # 3. Try web search
        result = self._verify_with_web_search([citation]).get(citation, {})
        if result.get("verified"):
            # Merge with base result
            base_result.update(result)
            base_result["canonical_citation"] = result.get("citation", citation)
            base_result["url"] = result.get("opinion_url") or result.get("url")
            base_result["canonical_date"] = result.get("date_filed")
            base_result["verified"] = True
            return base_result
        
        # 4. If all fail, return failure result with extracted info
        return base_result

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

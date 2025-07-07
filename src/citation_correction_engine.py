"""
Citation Correction Engine

This module provides suggestions for correcting invalid or unverified citations
by finding similar verified citations and applying intelligent correction rules.
"""

import os
import logging
import sqlite3
import re
from datetime import datetime
try:
    import Levenshtein
    LEVENSHTEIN_AVAILABLE = True
except ImportError:
    LEVENSHTEIN_AVAILABLE = False
    print("Warning: Levenshtein module not available, using difflib fallback")
import sys
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
from src.citation_format_utils import apply_washington_spacing_rules
from src.database_manager import get_database_manager

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import configure_logging

# Configure logging if not already configured
if not logging.getLogger().hasHandlers():
    configure_logging()

logger = logging.getLogger(__name__)

class CitationCorrectionEngine:
    """
    A system for suggesting corrections to invalid or unverified citations
    by finding similar verified citations and applying intelligent correction rules.
    """

    def __init__(self):
        """Initialize the correction engine."""
        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "citations.db"
        )
        self.cache_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "correction_cache"
        )

        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # Initialize the database
        self._init_database()

    def suggest_corrections(self, citation, max_suggestions=5, min_similarity=0.7):
        """
        Suggest corrections for a potentially invalid citation.

        Args:
            citation (str): The citation to correct
            max_suggestions (int): Maximum number of suggestions to return
            min_similarity (float): Minimum similarity score (0-1) for suggestions

        Returns:
            dict: Dictionary containing the original citation and a list of suggested corrections
        """
        if not citation:
            return {"citation": "", "suggestions": [], "error": "No citation provided"}

        # Ensure citation is a string
        if not isinstance(citation, str):
            try:
                citation = str(citation)
            except Exception as e:
                return {
                    "citation": "[invalid]" + str(citation)[:50],
                    "suggestions": [],
                    "error": f"Invalid citation format: {str(e)}",
                }

        try:
            logger.info(f"Processing citation: {citation}")
            # Normalize the input citation
            normalized_citation = self._normalize_citation(citation)

            # Basic validation
            if not normalized_citation or len(normalized_citation.strip()) < 3:
                return {
                    "citation": citation,
                    "suggestions": [],
                    "error": "Citation is too short or empty after normalization",
                }

            # Try to get similar citations from the database
            try:
                similar_citations = self._find_similar_citations(
                    citation, min_similarity
                )

                # If we found similar citations, return them
                if similar_citations:
                    # Convert to the expected format
                    suggestions = [
                        {
                            "corrected_citation": item["citation"],
                            "similarity": item["similarity"],
                            "explanation": f"Similar to verified citation (confidence: {item['similarity']:.1%})",
                            "correction_type": "similar_verified",
                        }
                        for item in similar_citations[:max_suggestions]
                    ]
                    return {
                        "citation": citation,
                        "suggestions": suggestions,
                        "info": f"Found {len(similar_citations)} similar citations in database",
                    }

                logger.info(f"No similar citations found for: {citation}")

            except Exception as e:
                logger.warning(f"Error getting similar citations: {e}")
                import traceback

                logger.debug(traceback.format_exc())
                # Continue to provide rule-based suggestions even if database lookup failed

            # If no similar citations found or error occurred, provide basic suggestions
            suggestions = []

            # Add normalized version as a suggestion if different from original
            if normalized_citation != citation:
                suggestions.append(
                    {
                        "corrected_citation": normalized_citation,
                        "similarity": 0.9,
                        "explanation": "Normalized citation format",
                        "correction_type": "normalization",
                    }
                )

            # Add some basic suggestions based on common patterns
            if "U.S." in normalized_citation or "US" in normalized_citation.upper():
                us_corrected = (
                    normalized_citation.replace("US", "U.S.")
                    .replace(" ", " ")
                    .replace("U.S.", "U.S. ")
                    .strip()
                )

                # Only add if it's different from the normalized version
                if us_corrected != normalized_citation:
                    suggestions.append(
                        {
                            "corrected_citation": us_corrected,
                            "similarity": 0.85,
                            "explanation": "Standardized U.S. Supreme Court citation format",
                            "correction_type": "format_standardization",
                        }
                    )

            return {"citation": citation, "suggestions": suggestions[:max_suggestions]}

        except re.error as e:
            logger.error(f"Regex error processing citation '{citation}': {str(e)}")
            return {
                "citation": citation,
                "suggestions": [],
                "error": f"Error processing citation format: {str(e)}",
            }
        except Exception as e:
            logger.error(f"Unexpected error processing citation '{citation}': {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            return {
                "citation": citation,
                "suggestions": [],
                "error": f"Error generating suggestions: {str(e)}",
            }

    def _normalize_citation(self, citation):
        """
        Normalize citation format for better matching.

        Args:
            citation (str): The citation to normalize

        Returns:
            str: The normalized citation
        """
        if not citation:
            return ""

        logger.info(f"Normalizing citation: {citation}")

        try:
            # Basic normalization
            if not isinstance(citation, str):
                citation = str(citation)

            normalized = citation.strip()

            # Replace multiple spaces with a single space
            normalized = re.sub(r"\s+", " ", normalized)

            # Remove any leading or trailing punctuation
            normalized = normalized.strip(" .,;:")

            # Apply Washington citation spacing rules first
            normalized = apply_washington_spacing_rules(normalized)

            # Handle common citation formats
            # Federal Reporter format (e.g., 123 F.3d 456 or 123 F.2d 456)
            fed_reporter = re.match(r"^(\d+)\s+([A-Za-z\.\d]+)\s+(\d+)$", normalized)
            if fed_reporter:
                vol = fed_reporter.group(1)
                reporter = (
                    fed_reporter.group(2).upper().replace(" ", "")
                )  # Remove any spaces in reporter
                page = fed_reporter.group(3)
                return f"{vol} {reporter} {page}"

            # US Reports format (e.g., 410 U.S. 113 or 410 US 113)
            us_reports = re.match(
                r"^(\d+)\s+U\.?\s*S\.?\s*(\d+)$", normalized, re.IGNORECASE
            )
            if us_reports:
                vol = us_reports.group(1)
                page = us_reports.group(2)
                return f"{vol} U.S. {page}"

            # Handle format without periods (e.g., 410 US 113)
            us_no_periods = re.match(r"^(\d+)\s+US\s+(\d+)$", normalized, re.IGNORECASE)
            if us_no_periods:
                vol = us_no_periods.group(1)
                page = us_no_periods.group(2)
                return f"{vol} U.S. {page}"

            # Washington Reports/Appeals format
            wash_cites = re.match(
                r"^(\d+)\s+Wn\.?\s*(2d|App)?\s*(\d*)$", normalized, re.IGNORECASE
            )
            if wash_cites:
                vol = wash_cites.group(1)
                series = (
                    f" {wash_cites.group(2).upper()}" if wash_cites.group(2) else ""
                )
                page = f" {wash_cites.group(3)}" if wash_cites.group(3) else ""
                return f"{vol} WASH{series}{page}"

            # Additional citation formats can be added here

            # Apply general normalization rules
            normalized = re.sub(r"Wash\.\s*App\.", "Wn. App.", normalized)
            normalized = re.sub(r"Wash\.", "Wn.", normalized)

            # Normalize reporter abbreviations
            normalized = re.sub(
                r"P\.\s*(\d+)(d|th)", r"P.\1\2", normalized, flags=re.IGNORECASE
            )  # P.2d, P.3d
            normalized = re.sub(
                r"F\.\s*(\d+)(d|th)", r"F.\1\2", normalized, flags=re.IGNORECASE
            )  # F.2d, F.3d

            # Standardize spacing around periods in reporter abbreviations
            # Only remove spaces after periods if the next character is a lowercase letter
            normalized = re.sub(
                r"\.\s+(?=[a-z])", ".", normalized
            )  # Remove spaces after periods only before lowercase letters

            return normalized.strip()

        except Exception as e:
            logger.error(f"Error normalizing citation '{citation}': {str(e)}")
            return citation.strip()

    def _extract_citation_components(self, citation):
        """Extract components from a citation for flexible matching."""
        components = {"volume": "", "reporter": "", "page": "", "court": "", "year": ""}

        try:
            # First normalize the citation to handle variations like "US" vs "U.S."
            normalized = citation.upper()

            # Handle US Reports format (e.g., 410 U.S. 113 or 410 US 113)
            us_reports = re.match(
                r"^(\d+)\s+U\.?\s*S\.?\s*(\d+)", normalized, re.IGNORECASE
            )
            if us_reports:
                components["volume"] = us_reports.group(1)
                components["reporter"] = "U.S."
                components["page"] = us_reports.group(2)
                components["court"] = "United States Supreme Court"
                return components

            # Handle Federal Reporter format (e.g., 123 F.3d 456 or 123 F.2d 456)
            fed_reporter = re.match(
                r"^(\d+)\s+([A-Za-z\.\d]+)\s+(\d+)", normalized, re.IGNORECASE
            )
            if fed_reporter:
                components["volume"] = fed_reporter.group(1)
                reporter = (
                    fed_reporter.group(2).upper().replace(" ", "")
                )  # Remove any spaces in reporter

                # Normalize reporter format (e.g., F3d -> F.3d)
                reporter = re.sub(r"F(\d+)(D|d)", r"F.\1d", reporter)

                components["reporter"] = reporter
                components["page"] = fed_reporter.group(3)

                if any(rep in reporter.upper() for rep in ["F.2D", "F.3D"]):
                    components["court"] = "United States Court of Appeals"
                elif any(
                    rep in reporter.upper()
                    for rep in ["F.SUPP", "F.SUPP.2D", "F.SUPP.3D"]
                ):
                    components["court"] = "United States District Court"

                return components

            # Handle Washington Reports/Appeals format
            wash_cites = re.match(
                r"^(\d+)\s+WN\.?\s*(2D|APP)?\s*(\d*)", normalized, re.IGNORECASE
            )
            if wash_cites:
                components["volume"] = wash_cites.group(1)
                series = (
                    f" {wash_cites.group(2).upper()}" if wash_cites.group(2) else ""
                )
                components["reporter"] = f"WASH{series}"
                if wash_cites.group(3):
                    components["page"] = wash_cites.group(3)
                if "APP" in normalized:
                    components["court"] = "Washington Court of Appeals"
                else:
                    components["court"] = "Washington Supreme Court"
                return components

            # Extract volume, reporter, and page for general case
            volume_reporter_page = re.search(
                r"(\d+)\s+([A-Za-z\.\s]+?)(?:\s+(\d+))?\s*$", citation
            )
            if volume_reporter_page:
                components["volume"] = volume_reporter_page.group(1)
                components["reporter"] = volume_reporter_page.group(2).strip()
                if volume_reporter_page.group(3):
                    components["page"] = volume_reporter_page.group(3)

            # Extract year
            year = re.search(r"\((\d{4})\)", citation)
            if year:
                components["year"] = year.group(1)

            # Determine court based on reporter if not already set
            if not components["court"]:
                if "WN. APP" in normalized or "WASH. APP" in normalized:
                    components["court"] = "Washington Court of Appeals"
                elif "WN." in normalized or "WASH." in normalized:
                    components["court"] = "Washington Supreme Court"
                elif "U.S." in normalized or "US " in normalized:
                    components["court"] = "United States Supreme Court"
                elif "F." in normalized:
                    if "SUPP." in normalized:
                        components["court"] = "United States District Court"
                    else:
                        components["court"] = "United States Court of Appeals"

        except Exception as e:
            logger.error(
                f"Error extracting components from citation '{citation}': {str(e)}"
            )
            import traceback

            logger.error(traceback.format_exc())

        return components

    def _init_database(self):
        """Initialize the database with required tables if they don't exist."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if the citations table exists and has the correct schema
            cursor.execute("PRAGMA table_info(citations)")
            columns = [col[1] for col in cursor.fetchall()]

            # If table doesn't exist or is missing required columns, recreate it
            if not columns or "citation_text" not in columns:
                # Drop existing table if it exists
                cursor.execute("""DROP TABLE IF EXISTS citations""")

                # Create citations table with the correct schema
                cursor.execute(
                    """
                    CREATE TABLE citations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        citation_text TEXT NOT NULL UNIQUE,
                        found BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create an index on citation_text for faster lookups
                cursor.execute(
                    """
                    CREATE INDEX idx_citation_text ON citations (citation_text)
                """
                )

                # Create an index on found for faster filtering
                cursor.execute(
                    """
                    CREATE INDEX idx_citation_found ON citations (found)
                """
                )

                # Seed the database with sample data
                self._seed_database(cursor)
            else:
                # Table exists with correct schema, just check if it's empty
                cursor.execute("""SELECT COUNT(*) FROM citations""")
                count = cursor.fetchone()[0]

                # If database is empty, seed with some sample citations
                if count == 0:
                    self._seed_database(cursor)

            conn.commit()
            logger.info("Database initialized successfully")

        except sqlite3.Error as e:
            error_msg = f"Error initializing database: {e}"
            logging.error(error_msg)
            if conn:
                conn.rollback()
            raise RuntimeError(error_msg)
        finally:
            if conn:
                conn.close()

    def _seed_database(self, cursor):
        """Seed the database with sample verified citations."""
        try:
            sample_citations = [
                # US Supreme Court cases
                "410 U.S. 113",  # Roe v. Wade
                "347 U.S. 483",  # Brown v. Board of Education
                "384 U.S. 436",  # Miranda v. Arizona
                "163 U.S. 537",  # Plessy v. Ferguson
                "5 U.S. 137",  # Marbury v. Madison
                # Federal Reporter cases
                "347 F.3d 123",
                "456 F.2d 789",
                "789 F.3d 456",
                "123 F.Supp.2d 456",
                "456 F.Supp.2d 789",
                # Washington State cases
                "123 Wn.2d 456",
                "456 Wn. App. 789",
                "789 Wn.2d 123",
                "123 Wn. App. 456",
                "456 Wn. 789",
            ]

            # Insert sample citations
            for citation in sample_citations:
                try:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO citations (citation_text, found)
                        VALUES (?, 1)
                    """,
                        (citation,),
                    )
                except Exception as e:
                    logger.warning(f"Could not insert citation {citation}: {e}")

            logger.info(
                f"Seeded database with {len(sample_citations)} sample citations"
            )

        except Exception as e:
            logger.error(f"Error seeding database: {e}")
            import traceback

            logger.error(traceback.format_exc())

    def _get_verified_citations(self):
        """
        Get all verified citations from the database.

        Returns:
            list: List of verified citation strings, or empty list if error occurs
        """
        try:
            # Ensure database is initialized
            self._init_database()

            db_manager = get_database_manager()
            logger.debug("Using DatabaseManager to fetch verified citations")

            # Check if the citations table exists
            tables = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='citations'")
            if not tables:
                logger.warning("Citations table does not exist in the database")
                return []

            # Check if the 'found' column exists
            columns = db_manager.execute_query("PRAGMA table_info(citations)")
            column_names = [col['name'] for col in columns]

            # Prepare query based on available columns
            if "found" in column_names:
                query = "SELECT citation_text FROM citations WHERE found = 1"
                logger.debug("Querying for verified citations with 'found = 1'")
            else:
                query = "SELECT citation_text FROM citations"
                logger.warning("'found' column not found, returning all citations")

            rows = db_manager.execute_query(query)
            verified_citations = [row["citation_text"] for row in rows if row and row["citation_text"]]

            logger.info(f"Retrieved {len(verified_citations)} verified citations from database")
            return verified_citations

        except Exception as e:
            logger.error(f"Unexpected error in _get_verified_citations: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def _similarity_score(self, citation1, citation2):
        """Calculate similarity score between two citations."""
        # Normalize citations
        norm1 = self._normalize_citation(citation1)
        norm2 = self._normalize_citation(citation2)

        # Calculate similarity using available method
        if LEVENSHTEIN_AVAILABLE:
            # Use Levenshtein distance
            distance = Levenshtein.distance(norm1, norm2)
            max_len = max(len(norm1), len(norm2))
            
            if max_len == 0:
                return 0.0
            
            # Convert distance to similarity score (0 to 1)
            similarity = 1.0 - (distance / max_len)
        else:
            # Use difflib as fallback
            similarity = SequenceMatcher(None, norm1, norm2).ratio()

        # Extract components
        comp1 = self._extract_citation_components(citation1)
        comp2 = self._extract_citation_components(citation2)

        # Boost score if components match
        component_matches = 0
        component_total = 0

        for key in ["volume", "reporter", "page"]:
            if comp1[key] and comp2[key]:
                component_total += 1
                if comp1[key] == comp2[key]:
                    component_matches += 1

        if component_total > 0:
            component_similarity = component_matches / component_total
            # Weight: 70% string similarity, 30% component similarity
            similarity = (0.7 * similarity) + (0.3 * component_similarity)

        return similarity

    def _find_similar_citations(self, citation, threshold=0.7):
        """
        Find similar verified citations above a similarity threshold.

        Args:
            citation (str): The citation to find similar matches for
            threshold (float): Minimum similarity score (0-1) to consider a match

        Returns:
            list: List of dictionaries with 'citation' and 'similarity' keys,
                  sorted by similarity in descending order
        """
        if not citation or not isinstance(citation, str):
            logger.warning(f"Invalid citation provided: {citation}")
            return []

        logger.debug(
            f"Finding similar citations for: {citation} (threshold: {threshold})"
        )

        try:
            # Get verified citations with error handling
            verified_citations = self._get_verified_citations()
            if not verified_citations:
                logger.debug("No verified citations found in database")
                return []

            logger.debug(
                f"Comparing against {len(verified_citations)} verified citations"
            )

            similar_citations = []

            for verified_citation in verified_citations:
                try:
                    # Skip invalid citations
                    if not verified_citation or not isinstance(verified_citation, str):
                        continue

                    # Calculate similarity score
                    similarity = self._similarity_score(citation, verified_citation)

                    # Add to results if above threshold
                    if similarity >= threshold:
                        similar_citations.append(
                            {"citation": verified_citation, "similarity": similarity}
                        )

                except Exception as e:
                    logger.warning(
                        f"Error comparing citations '{citation}' and '{verified_citation}': {e}"
                    )
                    continue

            # Sort by similarity (highest first)
            similar_citations.sort(key=lambda x: x["similarity"], reverse=True)

            # Log results
            result_count = len(similar_citations)
            if result_count > 0:
                logger.debug(
                    f"Found {result_count} similar citations (best match: {similar_citations[0]['similarity']:.2f})"
                )
            else:
                logger.debug("No similar citations found above threshold")

            return similar_citations

        except Exception as e:
            logger.error(f"Error in _find_similar_citations: {e}")
            import traceback

            logger.debug(traceback.format_exc())
            return []

    def _apply_correction_rules(self, citation):
        """Apply correction rules to fix common citation errors."""
        corrected = citation

        # Apply Washington citation spacing rules first
        corrected = apply_washington_spacing_rules(corrected)

        # Rule 1: Fix spacing issues
        corrected = re.sub(
            r"(\d+)([A-Za-z])", r"\1 \2", corrected
        )  # Add space between number and letter
        corrected = re.sub(
            r"([A-Za-z])(\d+)", r"\1 \2", corrected
        )  # Add space between letter and number

        # Rule 2: Fix common reporter abbreviations
        corrected = re.sub(r"Wash\.\s*App\.", "Wn. App.", corrected)
        corrected = re.sub(r"Wash\.", "Wn.", corrected)
        corrected = re.sub(r"Pac\.", "P.", corrected)
        corrected = re.sub(r"Fed\.", "F.", corrected)

        # Rule 3: Fix edition markers
        corrected = re.sub(r"P\s*(\d+\s*d)", r"P.\1", corrected)
        corrected = re.sub(r"P\s*(\d+)\s*th", r"P.\1d", corrected)
        corrected = re.sub(r"F\s*(\d+\s*d)", r"F.\1", corrected)
        corrected = re.sub(r"F\s*(\d+)\s*th", r"F.\1d", corrected)

        # Rule 4: Fix missing periods in abbreviations
        corrected = re.sub(
            r"(\b[A-Z][a-z]*)(\s)", r"\1.\2", corrected
        )  # Add period after abbreviations

        # Rule 5: Fix case name formatting
        if " v " in corrected:
            corrected = corrected.replace(" v ", " v. ")

        return corrected

    def _check_database_initialized(self):
        """Check if the database is properly initialized with data."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM citations WHERE found = 1")
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception as e:
            logger.error(f"Error checking database: {e}")
            return False

    def suggest_corrections(self, citation):
        """
        Suggest corrections for an invalid or unverified citation.
        Returns a list of suggested corrections with explanations.
        """
        if not citation:
            return {
                "citation": citation,
                "suggestions": [],
                "error": "No citation provided",
            }

        logger.info(f"Suggesting corrections for citation: {citation}")

        # Check if database is initialized with data
        if not self._check_database_initialized():
            logger.warning("Citation database is empty or not properly initialized")
            # Instead of returning an error, try to apply rule-based corrections
            logger.info("Proceeding with rule-based corrections only")

            # Apply correction rules
            rule_corrected = self._apply_correction_rules(citation)

            # Only return the rule-based correction if it's different from the original
            if rule_corrected != citation:
                return {
                    "citation": citation,
                    "suggestions": [
                        {
                            "corrected_citation": rule_corrected,
                            "similarity": 0.8,  # Estimated similarity
                            "explanation": "Applied automatic correction rules (database not available)",
                            "correction_type": "rule_based",
                        }
                    ],
                    "warning": "Citation database is empty. Only rule-based corrections are available.",
                }

            return {
                "citation": citation,
                "suggestions": [],
                "warning": "No corrections available. Citation database is empty.",
            }

        # Apply correction rules
        rule_corrected = self._apply_correction_rules(citation)

        # Find similar citations
        similar_citations = self._find_similar_citations(citation)

        # Prepare suggestions
        suggestions = []

        # Add rule-based correction if different from original
        if rule_corrected != citation:
            try:
                similarity = self._similarity_score(citation, rule_corrected)
                suggestions.append(
                    {
                        "corrected_citation": rule_corrected,
                        "similarity": similarity,
                        "explanation": "Applied automatic correction rules",
                        "correction_type": "rule_based",
                    }
                )
            except Exception as e:
                logger.error(f"Error applying rule-based correction: {e}")

        # Add similar citations if any
        if similar_citations:
            for similar in similar_citations[:5]:  # Limit to top 5
                try:
                    suggestions.append(
                        {
                            "corrected_citation": similar["citation"],
                            "similarity": similar["similarity"],
                            "explanation": f"Similar to verified citation (similarity: {similar['similarity']:.2f})",
                            "correction_type": "similar_citation",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error processing similar citation: {e}")
                    continue

        # Sort suggestions by similarity if we have any
        if suggestions:
            suggestions.sort(key=lambda x: x.get("similarity", 0), reverse=True)

        return {
            "citation": citation,
            "suggestions": suggestions,
            "correction_date": datetime.now().isoformat(),
        }

    def batch_suggest_corrections(self, citations):
        """
        Suggest corrections for a batch of citations.
        Returns a list of correction suggestions.
        """
        results = []

        for citation in citations:
            result = self.suggest_corrections(citation)
            results.append(result)

        return results

    def apply_best_correction(self, citation):
        """
        Apply the best correction to a citation.
        Returns the corrected citation and an explanation.
        """
        suggestions = self.suggest_corrections(citation)

        if not suggestions["suggestions"]:
            return {
                "citation": citation,
                "corrected": False,
                "corrected_citation": citation,
                "explanation": "No corrections available",
            }

        # Get the best suggestion
        best_suggestion = suggestions["suggestions"][0]

        return {
            "citation": citation,
            "corrected": True,
            "corrected_citation": best_suggestion["corrected_citation"],
            "similarity": best_suggestion["similarity"],
            "explanation": best_suggestion["explanation"],
            "correction_type": best_suggestion["correction_type"],
        }


# Example usage
if __name__ == "__main__":
    correction_engine = CitationCorrectionEngine()

    # Example invalid citations
    invalid_citations = [
        "410 US 113",  # Missing periods in U.S.
        "347US483",  # Missing spaces
        "198 Wash2d 271",  # Missing period
        "175WashApp1",  # Missing spaces and periods
        "123 P3d 456",  # Missing period
    ]

    # Suggest corrections for each citation
    for citation in invalid_citations:
        result = correction_engine.suggest_corrections(citation)
        print(f"Citation: {citation}")
        print(f"Suggestions: {len(result['suggestions'])}")

        for i, suggestion in enumerate(result["suggestions"]):
            print(
                f"  {i+1}. {suggestion['corrected_citation']} (similarity: {suggestion['similarity']:.2f})"
            )
            print(f"     Explanation: {suggestion['explanation']}")

        print()

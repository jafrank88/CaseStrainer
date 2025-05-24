"""
Citation Correction Engine

This module provides suggestions for correcting invalid or unverified citations
by finding similar verified citations and applying intelligent correction rules.
"""

import os
import sys
import json
import logging
import sqlite3
import re
from datetime import datetime
from difflib import SequenceMatcher
import Levenshtein

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("citation_correction")


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

    def _normalize_citation(self, citation):
        """Normalize citation format for better matching."""
        if not citation:
            return ""

        # Replace multiple spaces with a single space
        normalized = re.sub(r"\s+", " ", citation.strip())

        # Normalize Washington citations
        normalized = re.sub(r"Wash\.\s*App\.", "Wn. App.", normalized)
        normalized = re.sub(r"Wash\.", "Wn.", normalized)

        # Normalize Pacific Reporter citations
        normalized = re.sub(r"P\.(\d+)d", "P.2d", normalized)
        normalized = re.sub(r"P\.(\d+)th", "P.3d", normalized)

        # Normalize Federal Reporter citations
        normalized = re.sub(r"F\.(\d+)d", "F.2d", normalized)
        normalized = re.sub(r"F\.(\d+)th", "F.3d", normalized)

        return normalized

    def _extract_citation_components(self, citation):
        """Extract components from a citation for flexible matching."""
        components = {"volume": "", "reporter": "", "page": "", "court": "", "year": ""}

        # Extract volume, reporter, and page
        volume_reporter_page = re.search(r"(\d+)\s+([A-Za-z\.\s]+)\s+(\d+)", citation)
        if volume_reporter_page:
            components["volume"] = volume_reporter_page.group(1)
            components["reporter"] = volume_reporter_page.group(2).strip()
            components["page"] = volume_reporter_page.group(3)

        # Extract year
        year = re.search(r"\((\d{4})\)", citation)
        if year:
            components["year"] = year.group(1)

        # Extract court
        if "Wn. App." in citation or "Wash. App." in citation:
            components["court"] = "Washington Court of Appeals"
        elif "Wn." in citation or "Wash." in citation:
            components["court"] = "Washington Supreme Court"
        elif "U.S." in citation:
            components["court"] = "United States Supreme Court"
        elif "F." in citation:
            if "Supp." in citation:
                components["court"] = "United States District Court"
            else:
                components["court"] = "United States Court of Appeals"

        return components

    def _get_verified_citations(self):
        """Get all verified citations from the database."""
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all verified citations
            cursor.execute("SELECT citation_text FROM citations WHERE found = 1")
            rows = cursor.fetchall()

            # Close the connection
            conn.close()

            # Extract citation texts
            verified_citations = [row[0] for row in rows if row[0]]

            return verified_citations

        except Exception as e:
            logger.error(f"Error getting verified citations: {e}")
            return []

    def _similarity_score(self, citation1, citation2):
        """Calculate similarity score between two citations."""
        # Normalize citations
        norm1 = self._normalize_citation(citation1)
        norm2 = self._normalize_citation(citation2)

        # Calculate Levenshtein distance
        distance = Levenshtein.distance(norm1, norm2)
        max_len = max(len(norm1), len(norm2))

        if max_len == 0:
            return 0.0

        # Convert distance to similarity score (0 to 1)
        similarity = 1.0 - (distance / max_len)

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
        """Find similar verified citations above a similarity threshold."""
        verified_citations = self._get_verified_citations()
        similar_citations = []

        for verified_citation in verified_citations:
            similarity = self._similarity_score(citation, verified_citation)

            if similarity >= threshold:
                similar_citations.append(
                    {"citation": verified_citation, "similarity": similarity}
                )

        # Sort by similarity (highest first)
        similar_citations.sort(key=lambda x: x["similarity"], reverse=True)

        return similar_citations

    def _apply_correction_rules(self, citation):
        """Apply correction rules to fix common citation errors."""
        corrected = citation

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
        corrected = re.sub(r"P\s*(\d+)\s*d", r"P.\2d", corrected)
        corrected = re.sub(r"P\s*(\d+)\s*th", r"P.\2d", corrected)
        corrected = re.sub(r"F\s*(\d+)\s*d", r"F.\2d", corrected)
        corrected = re.sub(r"F\s*(\d+)\s*th", r"F.\2d", corrected)

        # Rule 4: Fix missing periods in abbreviations
        corrected = re.sub(
            r"(\b[A-Z][a-z]*)(\s)", r"\1.\2", corrected
        )  # Add period after abbreviations

        # Rule 5: Fix case name formatting
        if " v " in corrected:
            corrected = corrected.replace(" v ", " v. ")

        return corrected

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

        # Apply correction rules
        rule_corrected = self._apply_correction_rules(citation)

        # Find similar citations
        similar_citations = self._find_similar_citations(citation)

        # Prepare suggestions
        suggestions = []

        # Add rule-based correction if different from original
        if rule_corrected != citation:
            suggestions.append(
                {
                    "corrected_citation": rule_corrected,
                    "similarity": self._similarity_score(citation, rule_corrected),
                    "explanation": "Applied automatic correction rules",
                    "correction_type": "rule_based",
                }
            )

        # Add similar citations
        for similar in similar_citations[:5]:  # Limit to top 5
            suggestions.append(
                {
                    "corrected_citation": similar["citation"],
                    "similarity": similar["similarity"],
                    "explanation": f"Similar to verified citation (similarity: {similar['similarity']:.2f})",
                    "correction_type": "similar_citation",
                }
            )

        # Sort suggestions by similarity
        suggestions.sort(key=lambda x: x["similarity"], reverse=True)

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

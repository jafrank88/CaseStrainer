#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Citation Correction Suggestions

This module provides functionality to suggest corrections for unconfirmed citations
by finding similar verified citations and providing "did you mean" alternatives.
"""

import re
import json
import os
import requests
from fuzzywuzzy import fuzz

# Path to the citation database
DOWNLOAD_DIR = "downloaded_briefs"
UNCONFIRMED_CITATIONS_FILE = os.path.join(
    DOWNLOAD_DIR, "unconfirmed_citations_flat.json"
)
CORRECTION_CACHE_FILE = os.path.join(DOWNLOAD_DIR, "correction_suggestions.json")

# CourtListener API URL
COURTLISTENER_API_URL = "https://www.courtlistener.com/api/rest/v3/search/"


# Load API key from config.json
def load_api_key():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config.get("courtlistener_api_key")
    except Exception as e:
        print(f"Error loading API key: {e}")
        return None


def load_unconfirmed_citations():
    """Load unconfirmed citations from the JSON file."""
    try:
        if os.path.exists(UNCONFIRMED_CITATIONS_FILE):
            with open(UNCONFIRMED_CITATIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading unconfirmed citations: {e}")
        return []


def load_correction_cache():
    """Load correction suggestions from cache."""
    try:
        if os.path.exists(CORRECTION_CACHE_FILE):
            with open(CORRECTION_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading correction cache: {e}")
        return {}


def save_correction_cache(cache):
    """Save correction suggestions to cache."""
    try:
        with open(CORRECTION_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
        print(f"Saved correction suggestions to {CORRECTION_CACHE_FILE}")
    except Exception as e:
        print(f"Error saving correction cache: {e}")


def normalize_citation(citation_text):
    """Normalize citation text for comparison."""
    # Remove punctuation and convert to lowercase
    normalized = re.sub(r"[^\w\s]", "", citation_text.lower())
    # Remove extra whitespace
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def extract_citation_components(citation_text):
    """Extract components from a citation for better matching."""
    components = {}

    # Extract volume numbers
    volume_match = re.search(r"(\d+)\s+", citation_text)
    if volume_match:
        components["volume"] = volume_match.group(1)

    # Extract reporter abbreviations (e.g., Wn.2d, P.3d)
    reporter_match = re.search(r"([A-Za-z]+\.(?:\s*\d+)?[A-Za-z]*)", citation_text)
    if reporter_match:
        components["reporter"] = reporter_match.group(1)

    # Extract page numbers
    page_match = re.search(r",\s*(\d+)", citation_text)
    if page_match:
        components["page"] = page_match.group(1)

    # Extract year if present
    year_match = re.search(r"\((\d{4})\)", citation_text)
    if year_match:
        components["year"] = year_match.group(1)

    # Extract WL citation if present
    wl_match = re.search(r"(\d{4})\s+WL\s+(\d+)", citation_text)
    if wl_match:
        components["wl_year"] = wl_match.group(1)
        components["wl_number"] = wl_match.group(2)

    return components


def find_similar_citations(citation_text, api_key=None):
    """Find similar citations using the CourtListener API and local database."""
    # First check the cache
    cache = load_correction_cache()
    if citation_text in cache:
        print(f"Using cached suggestions for {citation_text}")
        return cache[citation_text]

    suggestions = []

    # Extract components for better matching
    components = extract_citation_components(citation_text)

    # Search CourtListener API if we have an API key
    if api_key:
        try:
            # Build search query based on components
            query_parts = []
            if "volume" in components:
                query_parts.append(components["volume"])
            if "reporter" in components:
                query_parts.append(components["reporter"])

            # If we have WL citation, search for that specifically
            if "wl_year" in components and "wl_number" in components:
                query_parts = [f"{components['wl_year']} WL {components['wl_number']}"]

            query = " ".join(query_parts)

            if query:
                # Set up API request
                headers = {
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "application/json",
                }

                params = {
                    "q": query,
                    "type": "o",  # Opinion type
                    "order_by": "score desc",  # Order by relevance
                    "page_size": 5,  # Limit to 5 results
                }

                # Make the request
                print(f"Searching CourtListener API for: {query}")
                response = requests.get(
                    COURTLISTENER_API_URL, headers=headers, params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])

                    for result in results:
                        # Extract citation information
                        case_name = result.get("case_name", "")
                        citation = result.get("citation", "")
                        url = f"https://www.courtlistener.com{result.get('absolute_url', '')}"

                        if citation:
                            # Calculate similarity score
                            similarity = fuzz.ratio(
                                normalize_citation(citation_text),
                                normalize_citation(citation),
                            )

                            if similarity > 60:  # Only include if reasonably similar
                                suggestions.append(
                                    {
                                        "citation": citation,
                                        "case_name": case_name,
                                        "url": url,
                                        "similarity": similarity,
                                        "source": "CourtListener API",
                                    }
                                )
        except Exception as e:
            print(f"Error searching CourtListener API: {e}")

    # Also search our local database of confirmed citations
    unconfirmed_citations = load_unconfirmed_citations()
    confirmed_citations = [
        c for c in unconfirmed_citations if c.get("confidence", 0) >= 0.7
    ]

    for citation in confirmed_citations:
        confirmed_text = citation.get("citation_text", "")
        if confirmed_text:
            # Calculate similarity score
            similarity = fuzz.ratio(
                normalize_citation(citation_text), normalize_citation(confirmed_text)
            )

            # Also check component-based similarity
            confirmed_components = extract_citation_components(confirmed_text)
            component_match = False

            # Check if key components match
            if "reporter" in components and "reporter" in confirmed_components:
                if components["reporter"] == confirmed_components["reporter"]:
                    component_match = True

            if (
                "wl_year" in components
                and "wl_year" in confirmed_components
                and components["wl_year"] == confirmed_components["wl_year"]
            ):
                component_match = True

            # Include if similar enough or components match
            if similarity > 60 or component_match:
                suggestions.append(
                    {
                        "citation": confirmed_text,
                        "case_name": citation.get("case_name", ""),
                        "url": citation.get("court_listener_url", ""),
                        "similarity": similarity,
                        "source": "Local Database",
                    }
                )

    # Sort by similarity score (highest first)
    suggestions.sort(key=lambda x: x["similarity"], reverse=True)

    # Limit to top 5 suggestions
    suggestions = suggestions[:5]

    # Cache the results
    cache[citation_text] = suggestions
    save_correction_cache(cache)

    return suggestions


def suggest_corrections_for_all():
    """Generate correction suggestions for all unconfirmed citations."""
    api_key = load_api_key()
    unconfirmed_citations = load_unconfirmed_citations()

    # Filter to only include actual unconfirmed citations
    low_confidence_citations = [
        c for c in unconfirmed_citations if c.get("confidence", 0) < 0.7
    ]

    print(
        f"Generating correction suggestions for {len(low_confidence_citations)} unconfirmed citations"
    )

    # Process each citation
    all_suggestions = {}
    for i, citation in enumerate(low_confidence_citations, 1):
        citation_text = citation.get("citation_text", "")
        if citation_text:
            print(f"[{i}/{len(low_confidence_citations)}] Processing: {citation_text}")
            suggestions = find_similar_citations(citation_text, api_key)

            if suggestions:
                all_suggestions[citation_text] = suggestions
                print(f"  Found {len(suggestions)} suggestions")
            else:
                print("  No suggestions found")

    # Save all suggestions to cache
    save_correction_cache(all_suggestions)

    return all_suggestions


def get_correction_suggestions(citation_text):
    """Get correction suggestions for a specific citation."""
    cache = load_correction_cache()

    # If not in cache, generate suggestions
    if citation_text not in cache:
        api_key = load_api_key()
        suggestions = find_similar_citations(citation_text, api_key)
        return suggestions

    return cache[citation_text]


if __name__ == "__main__":
    # Generate suggestions for all unconfirmed citations
    suggest_corrections_for_all()

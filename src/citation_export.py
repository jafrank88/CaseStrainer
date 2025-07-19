#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Citation Export and Integration

This module provides functionality to export citations in various formats
including plain text, BibTeX, EndNote, and JSON for integration with other tools.
"""

import os
import re
import json
import datetime

# Path to the citation database
DOWNLOAD_DIR = "downloaded_briefs"
UNCONFIRMED_CITATIONS_FILE = os.path.join(
    DOWNLOAD_DIR, "unconfirmed_citations_flat.json"
)
EXPORT_DIR = os.path.join(DOWNLOAD_DIR, "exports")

# Ensure export directory exists
if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR)


def load_citations(filter_criteria=None):
    """Load citations from the database with optional filtering."""
    try:
        if os.path.exists(UNCONFIRMED_CITATIONS_FILE):
            with open(UNCONFIRMED_CITATIONS_FILE, "r", encoding="utf-8") as f:
                citations = json.load(f)

                # Apply filters if provided
                if filter_criteria:
                    filtered_citations = []
                    for citation in citations:
                        # Check each filter criterion
                        include = True
                        for key, value in filter_criteria.items():
                            if key in citation:
                                # For confidence, treat as a minimum threshold
                                if key == "confidence":
                                    if citation[key] < float(value):
                                        include = False
                                        break
                                # For text fields, check if value is contained
                                elif isinstance(citation[key], str) and isinstance(
                                    value, str
                                ):
                                    if value.lower() not in citation[key].lower():
                                        include = False
                                        break
                                # For exact matches
                                elif citation[key] != value:
                                    include = False
                                    break

                        if include:
                            filtered_citations.append(citation)

                    return filtered_citations

                return citations
        return []
    except Exception as e:
        logger.error(f"Error loading citations: {e}")
        return []


def generate_unique_filename(base_name, extension):
    """Generate a unique filename with timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"


def export_to_text(citations, filename=None):
    """Export citations to a plain text file."""
    if not citations:
        return None

    if not filename:
        filename = generate_unique_filename("citations_export", "txt")

    filepath = os.path.join(EXPORT_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# CaseStrainer Citations Export\n")
            f.write(
                f"# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            f.write(f"# Total Citations: {len(citations)}\n\n")

            for i, citation in enumerate(citations, 1):
                f.write(f"## Citation {i}\n")
                f.write(f"Case: {citation.get('case_name', 'Unknown')}\n")
                f.write(f"Citation: {citation.get('citation_text', '')}\n")
                f.write(f"Confidence: {citation.get('confidence', 0)}\n")
                f.write(f"Status: {citation.get('hallucination_status', 'unknown')}\n")

                if citation.get("explanation"):
                    f.write(f"Explanation: {citation['explanation']}\n")

                if citation.get("court_listener_url"):
                    f.write(f"URL: {citation['court_listener_url']}\n")

                f.write("\n")

        return filepath
    except Exception as e:
        logger.error(f"Error exporting to text: {e}")
        return None


def export_to_bibtex(citations, filename=None):
    """Export citations to BibTeX format."""
    if not citations:
        return None

    if not filename:
        filename = generate_unique_filename("citations_export", "bib")

    filepath = os.path.join(EXPORT_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("% CaseStrainer Citations Export - BibTeX Format\n")
            f.write(
                f"% Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            for citation in citations:
                # Generate a unique BibTeX key
                case_name = citation.get("case_name", "Unknown")
                year_match = re.search(
                    r"\((\d{4})\)", citation.get("citation_text", "")
                )
                year = year_match.group(1) if year_match else "0000"

                # Create a sanitized key from case name
                key_base = re.sub(r"[^a-zA-Z]", "", case_name.split(" ")[0].lower())
                if not key_base:
                    key_base = "case"

                bibtex_key = f"{key_base}{year}"

                # Write BibTeX entry
                f.write(f"@misc{{{bibtex_key},\n")
                f.write(f"  title = {{{case_name}}},\n")

                # Extract author if available (use first party in case name)
                if case_name and " v. " in case_name:
                    author = case_name.split(" v. ")[0].strip()
                    f.write(f"  author = {{{author}}},\n")

                # Add year if available
                if year_match:
                    f.write(f"  year = {{{year}}},\n")

                # Add citation as note
                f.write(
                    f"  note = {{Citation: {citation.get('citation_text', '')}}},\n"
                )

                # Add URL if available
                if citation.get("court_listener_url"):
                    f.write(f"  url = {{{citation['court_listener_url']}}},\n")

                # Add confidence as custom field
                f.write(
                    f"  howpublished = {{Confidence: {citation.get('confidence', 0)}}},\n"
                )

                # Close the entry
                f.write("}\n\n")

        return filepath
    except Exception as e:
        logger.error(f"Error exporting to BibTeX: {e}")
        return None


def export_to_endnote(citations, filename=None):
    """Export citations to EndNote format (RIS)."""
    if not citations:
        return None

    if not filename:
        filename = generate_unique_filename("citations_export", "ris")

    filepath = os.path.join(EXPORT_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            for citation in citations:
                # Start RIS entry
                f.write("TY  - CASE\n")  # Type: Legal Case

                # Case name
                case_name = citation.get("case_name", "Unknown")
                f.write(f"T1  - {case_name}\n")  # Primary title

                # Extract year if available
                year_match = re.search(
                    r"\((\d{4})\)", citation.get("citation_text", "")
                )
                if year_match:
                    f.write(f"Y1  - {year_match.group(1)}\n")  # Year

                # Citation text
                f.write(f"M1  - {citation.get('citation_text', '')}\n")  # Misc. field 1

                # URL if available
                if citation.get("court_listener_url"):
                    f.write(f"UR  - {citation['court_listener_url']}\n")

                # Confidence and status as notes
                f.write(f"N1  - Confidence: {citation.get('confidence', 0)}\n")
                f.write(
                    f"N1  - Status: {citation.get('hallucination_status', 'unknown')}\n"
                )

                # End RIS entry
                f.write("ER  - \n\n")

        return filepath
    except Exception as e:
        logger.error(f"Error exporting to EndNote: {e}")
        return None


def export_to_json(citations, filename=None):
    """Export citations to JSON format."""
    if not citations:
        return None

    if not filename:
        filename = generate_unique_filename("citations_export", "json")

    filepath = os.path.join(EXPORT_DIR, filename)

    try:
        # Add metadata to the export
        export_data = {
            "metadata": {
                "generated": datetime.datetime.now().isoformat(),
                "count": len(citations),
                "source": "CaseStrainer",
            },
            "citations": citations,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)

        return filepath
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        return None


def export_citations(citations, format_type, filename=None):
    """Export citations in the specified format."""
    if format_type.lower() == "text":
        return export_to_text(citations, filename)
    elif format_type.lower() == "bibtex":
        return export_to_bibtex(citations, filename)
    elif format_type.lower() == "endnote":
        return export_to_endnote(citations, filename)
    elif format_type.lower() == "json":
        return export_to_json(citations, filename)
    else:
        logger.info(f"Unsupported export format: {format_type}")
        return None


if __name__ == "__main__":
    # Test export functionality
    citations = load_citations()
    logger.info(f"Loaded {len(citations)} citations")

    # Export in all formats
    text_file = export_to_text(citations)
    bibtex_file = export_to_bibtex(citations)
    endnote_file = export_to_endnote(citations)
    json_file = export_to_json(citations)

    logger.info(f"Exported to text: {text_file}")
    logger.info(f"Exported to BibTeX: {bibtex_file}")
    logger.info(f"Exported to EndNote: {endnote_file}")
    logger.info(f"Exported to JSON: {json_file}")

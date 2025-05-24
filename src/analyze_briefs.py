"""
Supreme Court Brief Citation Analyzer

This script analyzes the downloaded Supreme Court briefs using CaseStrainer,
extracts citations, verifies them, and records unverified citations with context.
"""

import os
import sys
import json
import csv
import traceback
import re
from datetime import datetime

# Import CaseStrainer functions
from file_utils import extract_text_from_file
from app_final import extract_citations
from multi_source_verifier import MultiSourceVerifier

# Constants
BRIEFS_DIR = "downloaded_briefs"
BRIEFS_CSV = "supreme_court_briefs.csv"
UNVERIFIED_CITATIONS_FILE = "unverified_citations.json"
CONTEXT_CHARS = 200  # Number of characters to include before and after the citation


def load_briefs_from_csv():
    """Load brief information from the CSV file."""
    briefs = []

    try:
        with open(BRIEFS_CSV, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                briefs.append(row)

        print(f"Loaded {len(briefs)} briefs from CSV file")
        return briefs

    except Exception as e:
        print(f"Error loading briefs from CSV file: {e}")
        traceback.print_exc()
        return []


def update_briefs_csv(briefs):
    """Update the CSV file with brief information."""
    try:
        with open(BRIEFS_CSV, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "Docket Number",
                "Caption",
                "Brief Type",
                "Filing Date",
                "PDF URL",
                "Local Path",
                "Analyzed",
                "Unverified Citations",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # Write header
            writer.writeheader()

            # Write brief information
            for brief in briefs:
                writer.writerow(brief)

        print(f"Updated CSV file: {BRIEFS_CSV}")

    except Exception as e:
        print(f"Error updating CSV file: {e}")
        traceback.print_exc()


def extract_citation_context(text, citation_text):
    """Extract the context around a citation."""
    try:
        # Find all occurrences of the citation in the text
        citation_positions = []
        for match in re.finditer(re.escape(citation_text), text):
            start_pos = match.start()
            end_pos = match.end()
            citation_positions.append((start_pos, end_pos))

        if not citation_positions:
            print(f"Citation not found in text: {citation_text}")
            return None

        # Extract context for each occurrence
        contexts = []
        for start_pos, end_pos in citation_positions:
            # Calculate context boundaries
            context_start = max(0, start_pos - CONTEXT_CHARS)
            context_end = min(len(text), end_pos + CONTEXT_CHARS)

            # Extract context
            context_before = text[context_start:start_pos]
            context_after = text[end_pos:context_end]
            full_context = context_before + citation_text + context_after

            contexts.append(
                {
                    "context_before": context_before,
                    "context_after": context_after,
                    "full_context": full_context,
                }
            )

        return contexts[0] if contexts else None

    except Exception as e:
        print(f"Error extracting context for citation: {e}")
        traceback.print_exc()
        return None


def save_unverified_citations(unverified_citations):
    """Save unverified citations to a JSON file."""
    try:
        # Load existing unverified citations if the file exists
        existing_citations = []
        if os.path.exists(UNVERIFIED_CITATIONS_FILE):
            try:
                with open(UNVERIFIED_CITATIONS_FILE, "r") as f:
                    existing_citations = json.load(f)
            except Exception as e:
                print(f"Error loading existing unverified citations: {e}")

        # Add new unverified citations
        existing_citations.extend(unverified_citations)

        # Save the combined list
        with open(UNVERIFIED_CITATIONS_FILE, "w") as f:
            json.dump(existing_citations, f, indent=2)

        print(
            f"Saved {len(unverified_citations)} unverified citations to "
            f"{UNVERIFIED_CITATIONS_FILE}"
        )

    except Exception as e:
        print(f"Error saving unverified citations: {e}")
        traceback.print_exc()


def analyze_brief(brief, verifier):
    """Analyze a brief to extract and verify citations."""
    print(f"Analyzing brief: {brief['Caption']}")

    try:
        # Get the local path
        local_path = brief["Local Path"]
        if not os.path.exists(local_path):
            print(f"Brief file not found: {local_path}")
            return []

        # Extract text from the brief
        brief_text = extract_text_from_file(local_path)
        if not brief_text:
            print(f"No text extracted from brief: {local_path}")
            return []

        # Extract citations from the text
        citations = extract_citations(brief_text)
        if not citations:
            print(f"No citations found in brief: {local_path}")
            return []

        print(f"Found {len(citations)} citations in brief: {brief['Caption']}")

        # Verify each citation
        unverified_citations = []
        for citation in citations:
            # Verify the citation
            result = verifier.verify_citation(citation)

            # If the citation is not verified, add it to the list
            if not result.get("verified", False):
                # Extract context for the citation
                context = extract_citation_context(brief_text, citation)

                if context:
                    unverified_citations.append(
                        {
                            "citation_text": citation,
                            "source_brief": brief["Caption"],
                            "brief_url": brief["PDF URL"],
                            "context_before": context["context_before"],
                            "context_after": context["context_after"],
                            "full_context": context["full_context"],
                            "verification_result": result,
                        }
                    )

        print(
            f"Found {len(unverified_citations)} unverified citations in brief: {brief['Caption']}"
        )

        # Update brief information
        brief["Analyzed"] = "Yes"
        brief["Unverified Citations"] = str(len(unverified_citations))

        return unverified_citations

    except Exception as e:
        print(f"Error analyzing brief: {e}")
        traceback.print_exc()
        return []


def main():
    """Main function to analyze briefs."""
    print("Starting Supreme Court Brief Citation Analyzer...")

    # Create a MultiSourceVerifier
    verifier = MultiSourceVerifier()

    # Load briefs from CSV
    briefs = load_briefs_from_csv()
    if not briefs:
        print("No briefs found in CSV file")
        return

    # Analyze each brief
    all_unverified_citations = []
    for i, brief in enumerate(briefs):
        # Skip if already analyzed
        if brief["Analyzed"] == "Yes":
            print(f"Skipping already analyzed brief: {brief['Caption']}")
            continue

        print(f"Processing brief {i+1} of {len(briefs)}: {brief['Caption']}")

        # Analyze the brief
        unverified_citations = analyze_brief(brief, verifier)
        all_unverified_citations.extend(unverified_citations)

        # Save after each brief to avoid losing data
        save_unverified_citations(unverified_citations)

        # Update the CSV file
        update_briefs_csv(briefs)

    print(f"Finished analyzing {len(briefs)} briefs")
    print(f"Found {len(all_unverified_citations)} total unverified citations")
    print(f"Unverified citations saved to {UNVERIFIED_CITATIONS_FILE}")


if __name__ == "__main__":
    main()

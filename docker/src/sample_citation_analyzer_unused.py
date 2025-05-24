"""
Sample Citation Analyzer

This script provides a way to analyze sample legal text with citations,
extract the citations using eyecite, verify them against CourtListener,
and save unverified citations with their surrounding context.
"""

import os
import sys
import json
import requests
import traceback
import time
import random
from datetime import datetime
import re

# Import eyecite for citation extraction
try:
    from eyecite import get_citations
    from eyecite.tokenizers import AhocorasickTokenizer

    print("Successfully imported eyecite")
except ImportError:
    print("Error: eyecite not installed. Please install it with 'pip install eyecite'")
    sys.exit(1)

# Constants
OUTPUT_FILE = "unverified_citations_with_context.json"
CONTEXT_CHARS = 200  # Number of characters to include before and after the citation

# Sample text with citations for testing
SAMPLE_TEXT_WITH_CITATIONS = """
The Supreme Court's decision in Brown v. Board of Education, 347 U.S. 483 (1954), 
overturned the "separate but equal" doctrine established in Plessy v. Ferguson, 163 U.S. 537 (1896).
The Court later expanded on this in Loving v. Virginia, 388 U.S. 1 (1967).

In the context of environmental law, the Court held in Massachusetts v. EPA, 549 U.S. 497 (2007),
that the Clean Air Act gives the EPA the authority to regulate greenhouse gases.

More recently, in Obergefell v. Hodges, 576 U.S. 644 (2015), the Court recognized a fundamental
right to marry for same-sex couples.

The Washington Supreme Court in State v. Blake, 197 Wn.2d 170, 481 P.3d 521 (2021),
held that Washington's strict liability drug possession statute was unconstitutional.

In an unpublished opinion, Smith v. Jones, 2022 WL 123456, the court discussed various aspects
of contract law that might be relevant to our case.

The court in Johnson v. Department of Licensing, 157 Wn. App. 434, 238 P.3d 91 (2010), 
addressed administrative law issues related to license revocation.

The decision in Microsoft Corp. v. United States, 530 U.S. 1301 (2000), dealt with
antitrust issues in the technology sector.

The court in State v. Abdulle, 174 Wn.2d 411, 275 P.3d 1113 (2012), discussed the requirements
for proving accomplice liability in criminal cases.

In Roe v. TeleTech Customer Care Management LLC, 171 Wn.2d 736, 257 P.3d 586 (2011),
the Washington Supreme Court held that the state's Medical Use of Marijuana Act does not
protect an employee from being fired for failing a drug test.

The Supreme Court's decision in Citizens United v. Federal Election Commission, 558 U.S. 310 (2010),
struck down restrictions on independent expenditures by corporations and unions in elections.
"""

# Additional sample text with made-up citations for testing
SAMPLE_TEXT_WITH_MADE_UP_CITATIONS = """
In the fictional case of Johnson v. Smith, 432 U.S. 789 (1982), the Court established
a three-part test for determining whether a statute violates the Due Process Clause.

The Washington Supreme Court in State v. Williams, 298 Wn.2d 456, 789 P.3d 123 (2019),
created a new standard for evaluating search and seizure claims under the state constitution.

In United States v. Thompson, 876 F.3d 543 (9th Cir. 2018), the Ninth Circuit addressed
the application of the Fourth Amendment to digital evidence.

The court in City of Seattle v. Johnson, 189 Wn. App. 567, 456 P.3d 789 (2017),
discussed the limits of municipal authority to regulate land use.

In the landmark case of People v. Technology Corp., 567 U.S. 890 (2014), the Supreme Court
established new guidelines for antitrust enforcement in the technology sector.

The Washington Court of Appeals in Smith v. Department of Health, 234 Wn. App. 567, 789 P.3d 123 (2020),
addressed the scope of administrative agencies' rulemaking authority.
"""


def extract_citations_with_context(text, source_name):
    """Extract citations using eyecite and include surrounding context."""
    print(f"Extracting citations from {source_name} using eyecite")

    try:
        # Use AhocorasickTokenizer which is more widely compatible
        tokenizer = AhocorasickTokenizer()

        # Use eyecite to extract citations
        citation_objects = get_citations(text, tokenizer=tokenizer)

        # Convert to our format with context
        formatted_citations = []
        for citation in citation_objects:
            # Get the citation text
            citation_text = citation.matched_text()

            # Get start and end positions
            start_pos = citation.span()[0]
            end_pos = citation.span()[1]

            # Calculate context boundaries
            context_start = max(0, start_pos - CONTEXT_CHARS)
            context_end = min(len(text), end_pos + CONTEXT_CHARS)

            # Extract context
            context_before = text[context_start:start_pos]
            context_after = text[end_pos:context_end]

            # Add to our list
            formatted_citations.append(
                {
                    "citation_text": citation_text,
                    "source": source_name,
                    "context_before": context_before,
                    "context_after": context_after,
                    "full_context": context_before + citation_text + context_after,
                    "citation_type": str(type(citation).__name__),
                    "metadata": {
                        "reporter": getattr(citation, "reporter", None),
                        "volume": getattr(citation, "volume", None),
                        "page": getattr(citation, "page", None),
                        "year": getattr(citation, "year", None),
                    },
                }
            )

        print(f"Found {len(formatted_citations)} citations in {source_name}")
        return formatted_citations

    except Exception as e:
        print(f"Error extracting citations with eyecite: {e}")
        traceback.print_exc()
        return []


def check_citation_in_courtlistener(citation_text):
    """Check if citation exists in CourtListener."""
    print(f"Checking citation in CourtListener: {citation_text}")

    try:
        # Load API key from config.json
        api_key = None
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                api_key = config.get("courtlistener_api_key")
        except Exception as e:
            print(f"Error loading API key from config.json: {e}")
            return False

        if not api_key:
            print("No CourtListener API key found")
            return False

        # Set up headers with API key
        headers = {
            "Authorization": f"Token {api_key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }

        # Prepare search query
        params = {"citation": citation_text, "format": "json"}

        # Make the request
        response = requests.get(
            "https://www.courtlistener.com/api/rest/v3/search/",
            headers=headers,
            params=params,
        )

        if response.status_code != 200:
            print(f"Error checking citation in CourtListener: {response.status_code}")
            return False

        # Parse the response
        data = response.json()

        # Check if any results were found
        if data.get("count", 0) > 0:
            print(f"Citation found in CourtListener: {citation_text}")
            return True
        else:
            print(f"Citation not found in CourtListener: {citation_text}")
            return False

    except Exception as e:
        print(f"Error checking citation in CourtListener: {e}")
        traceback.print_exc()
        return False


def check_citation_with_descrybe(citation_text):
    """Generate a URL for manual verification with Descrybe.ai."""
    base_url = "https://descrybe.ai/search"
    query_param = f"?q={citation_text}"
    return base_url + query_param


def process_sample_text():
    """Process the sample texts with citations."""
    print("Processing sample texts with citations")

    # Extract citations from the real citations sample text
    real_citations = extract_citations_with_context(
        SAMPLE_TEXT_WITH_CITATIONS, "Sample Text (Real Citations)"
    )

    # Extract citations from the made-up citations sample text
    made_up_citations = extract_citations_with_context(
        SAMPLE_TEXT_WITH_MADE_UP_CITATIONS, "Sample Text (Made-up Citations)"
    )

    # Combine all citations
    all_citations = real_citations + made_up_citations

    # Check each citation in CourtListener
    unverified_citations = []
    for citation in all_citations:
        citation_text = citation.get("citation_text")
        if not citation_text:
            continue

        # Check if citation exists in CourtListener
        found = check_citation_in_courtlistener(citation_text)

        # If citation is not verified, add it to the list
        if not found:
            # Add Descrybe.ai verification URL
            descrybe_url = check_citation_with_descrybe(citation_text)

            unverified_citations.append(
                {
                    "citation_text": citation_text,
                    "source": citation.get("source", "Unknown"),
                    "citation_metadata": citation.get("metadata", {}),
                    "context_before": citation.get("context_before", ""),
                    "context_after": citation.get("context_after", ""),
                    "full_context": citation.get("full_context", ""),
                    "manual_verification_url": descrybe_url,
                    "manual_verification_source": "Descrybe.ai",
                }
            )
            print(f"Unverified citation: {citation_text}")
            print(f"Manual verification URL: {descrybe_url}")

        # Add a small delay to avoid overwhelming the API
        time.sleep(random.uniform(0.5, 1.5))

    return unverified_citations


def save_unverified_citations(unverified_citations):
    """Save unverified citations to a JSON file."""
    print(f"Saving {len(unverified_citations)} unverified citations to {OUTPUT_FILE}")

    try:
        # Load existing unverified citations if the file exists
        existing_citations = []
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, "r") as f:
                existing_citations = json.load(f)

        # Combine existing and new citations
        all_citations = existing_citations + unverified_citations

        # Remove duplicates based on citation_text and source
        unique_citations = []
        seen = set()
        for citation in all_citations:
            key = (citation["citation_text"], citation["source"])
            if key not in seen:
                seen.add(key)
                unique_citations.append(citation)

        # Save to file
        with open(OUTPUT_FILE, "w") as f:
            json.dump(unique_citations, f, indent=2)

        print(
            f"Saved {len(unique_citations)} unique unverified citations to {OUTPUT_FILE}"
        )

    except Exception as e:
        print(f"Error saving unverified citations: {e}")
        traceback.print_exc()


def main():
    """Main function to process sample texts and extract unverified citations with context."""
    print("Starting extraction of unverified citations with context from sample texts")

    # Process sample texts
    unverified_citations = process_sample_text()

    # Save results
    save_unverified_citations(unverified_citations)

    print("Finished extracting unverified citations")
    print(f"Found {len(unverified_citations)} unverified citations")

    # Display the results in a more readable format
    if unverified_citations:
        print("\nUnverified Citations with Context:")
        for i, citation in enumerate(unverified_citations):
            print(f"\n{i+1}. Citation: {citation['citation_text']}")
            print(f"   Source: {citation['source']}")
            print(
                f"   Context: ...{citation['context_before']} [{citation['citation_text']}] {citation['context_after']}..."
            )
            print(f"   Manual verification: {citation['manual_verification_url']}")


if __name__ == "__main__":
    main()

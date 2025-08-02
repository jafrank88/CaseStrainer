#!/usr/bin/env python
"""
Script to generate synthetic unconfirmed citations for testing purposes.
This creates a dataset of 100+ unconfirmed citations that can be used to test the CaseStrainer interface.
"""
import os
import json
import random
import logging
logger = logging.getLogger(__name__)

# Directory to save generated citations
DOWNLOAD_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "downloaded_briefs"
)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Common case name patterns
PLAINTIFF_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Miller",
    "Davis",
    "Garcia",
    "Rodriguez",
    "Wilson",
    "Martinez",
    "Anderson",
    "Taylor",
    "Thomas",
    "Hernandez",
    "Moore",
    "Martin",
    "Jackson",
    "Thompson",
    "White",
    "Lopez",
    "Lee",
    "Gonzalez",
    "Harris",
    "Clark",
    "Lewis",
    "Robinson",
    "Walker",
    "Perez",
    "Hall",
    "State of Washington",
    "United States",
    "City of Seattle",
    "King County",
    "Department of Corrections",
    "Microsoft",
    "Amazon",
    "Boeing",
    "Starbucks",
    "Costco",
    "T-Mobile",
    "Expedia",
    "Zillow",
    "Nordstrom",
    "REI",
]

DEFENDANT_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Miller",
    "Davis",
    "Garcia",
    "Rodriguez",
    "Wilson",
    "Martinez",
    "Anderson",
    "Taylor",
    "Thomas",
    "Hernandez",
    "Moore",
    "Martin",
    "Jackson",
    "Thompson",
    "White",
    "Lopez",
    "Lee",
    "Gonzalez",
    "Harris",
    "Clark",
    "Lewis",
    "Robinson",
    "Walker",
    "Perez",
    "Hall",
    "State of Washington",
    "United States",
    "City of Seattle",
    "King County",
    "Department of Corrections",
    "Microsoft",
    "Amazon",
    "Boeing",
    "Starbucks",
    "Costco",
    "T-Mobile",
    "Expedia",
    "Zillow",
    "Nordstrom",
    "REI",
]

# Citation formats
CITATION_FORMATS = [
    # Washington Reporter
    "{} Wn.2d {}",
    "{} Wn. App. {}",
    "{} Wash. {}",
    "{} Wash. App. {}",
    "{} Wash.2d {}",
    # Federal Reporters
    "{} F.Supp.2d {}",
    "{} F.Supp.3d {}",
    "{} F.2d {}",
    "{} F.3d {}",
    "{} F.4th {}",
    "{} U.S. {}",
    "{} S. Ct. {}",
    "{} L. Ed. 2d {}",
    # West Law and other electronic formats
    "{} WL {}",
    "{} BL {}",
]

# Source files (fictional brief names)
SOURCE_FILES = [
    "Appellant_Brief_Division1.pdf",
    "Respondent_Brief_Division1.pdf",
    "Reply_Brief_Division1.pdf",
    "Appellant_Brief_Division2.pdf",
    "Respondent_Brief_Division2.pdf",
    "Reply_Brief_Division2.pdf",
    "Appellant_Brief_Division3.pdf",
    "Respondent_Brief_Division3.pdf",
    "Reply_Brief_Division3.pdf",
    "Appellant_Brief_Supreme.pdf",
    "Respondent_Brief_Supreme.pdf",
    "Reply_Brief_Supreme.pdf",
    "Supplemental_Brief_Division1.pdf",
    "Supplemental_Brief_Division2.pdf",
    "Supplemental_Brief_Division3.pdf",
    "Supplemental_Brief_Supreme.pdf",
    "Amicus_Brief_Division1.pdf",
    "Amicus_Brief_Division2.pdf",
    "Amicus_Brief_Division3.pdf",
    "Amicus_Brief_Supreme.pdf",
]

# Confidence levels and explanations
CONFIDENCE_LEVELS = [0.3, 0.4, 0.5, 0.6, 0.7]
EXPLANATIONS = [
    "Citation could not be verified by CourtListener, web search, or AI analysis.",
    "Citation not found in CourtListener database. Web search also couldn't verify this citation.",
    "LangSearch generated inconsistent summaries for this citation (similarity: {:.2f}), suggesting it may be hallucinated.",
    "Citation not found in any legal database. This may be a typo or a non-existent case.",
    "Citation format appears valid but could not be verified in available legal databases.",
]


def generate_random_citation():
    """Generate a random citation in a valid format but with random numbers."""
    citation_format = random.choice(CITATION_FORMATS)

    # Generate random volume and page numbers
    if "WL" in citation_format or "BL" in citation_format:
        # For WL and BL citations, use year and random number
        year = random.randint(1990, 2023)
        page = random.randint(100000, 9999999)
        citation = citation_format.format(year, page)
    else:
        # For reporter citations, use random volume and page
        volume = random.randint(1, 999)
        page = random.randint(1, 999)
        citation = citation_format.format(volume, page)

    return citation


def generate_random_case_name():
    """Generate a random case name in the format 'Plaintiff v. Defendant'."""
    plaintiff = random.choice(PLAINTIFF_NAMES)
    defendant = random.choice(DEFENDANT_NAMES)

    # Ensure plaintiff and defendant are different
    while plaintiff == defendant:
        defendant = random.choice(DEFENDANT_NAMES)

    return f"{plaintiff} v. {defendant}"


def generate_unconfirmed_citations(num_citations=100):
    """Generate a specified number of synthetic unconfirmed citations."""
    unconfirmed_citations = []

    for _ in range(num_citations):
        citation_text = generate_random_citation()
        case_name = generate_random_case_name()
        confidence = random.choice(CONFIDENCE_LEVELS)

        # Choose an explanation and format it with a random similarity score if needed
        explanation = random.choice(EXPLANATIONS)
        if "{:.2f}" in explanation:
            similarity = random.uniform(
                0.1, 0.39
            )  # Low similarity for unconfirmed citations
            explanation = explanation.format(similarity)

        # Create citation object
        citation = {
            "citation_text": citation_text,
            "case_name": case_name,
            "confidence": confidence,
            "explanation": explanation,
            "source_file": random.choice(SOURCE_FILES),
            "is_hallucinated": True,
            "hallucination_status": "unverified",
        }

        # Add some variety with optional fields
        if random.random() < 0.3:  # 30% chance to have summaries
            citation["summaries"] = [
                f"This appears to be a case about {random.choice(['contracts', 'torts', 'criminal law', 'property', 'constitutional law'])} but details are unclear.",
                f"The case might involve {random.choice(['a dispute between parties', 'an appeal of a lower court decision', 'a challenge to a statute', 'a motion to dismiss'])}, but sources are inconsistent.",
            ]

        unconfirmed_citations.append(citation)

    return unconfirmed_citations


def main():
    """Main function to generate and save synthetic unconfirmed citations."""
    logger.info("Generating synthetic unconfirmed citations for testing...")

    # Generate at least 100 unconfirmed citations
    num_citations = 120  # Generate a few extra
    citations = generate_unconfirmed_citations(num_citations)

    # Save the citations to a file
    output_file = os.path.join(DOWNLOAD_DIR, "unconfirmed_citations_flat.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(citations, f, indent=2)

    logger.info(f"Generated {num_citations} synthetic unconfirmed citations")
    logger.info(f"Saved to: {output_file}")

    # Also create a grouped version by source file
    grouped_citations = {}
    for citation in citations:
        source_file = citation["source_file"]
        if source_file not in grouped_citations:
            grouped_citations[source_file] = []

        # Create a copy without the source_file field to avoid redundancy
        citation_copy = citation.copy()
        citation_copy.pop("source_file", None)
        grouped_citations[source_file].append(citation_copy)

    # Save the grouped citations
    grouped_file = os.path.join(DOWNLOAD_DIR, "all_unconfirmed_citations.json")
    with open(grouped_file, "w", encoding="utf-8") as f:
        json.dump(grouped_citations, f, indent=2)

    logger.info(f"Grouped citations saved to: {grouped_file}")
    logger.info("\nNow you can add these citations to the CaseStrainer interface by updating the templates.")


if __name__ == "__main__":
    main()

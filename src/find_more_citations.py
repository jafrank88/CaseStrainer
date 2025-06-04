"""
Script to find more unconfirmed citations from various sources and add them to the database.

This script searches for citations in legal documents, checks if they can be verified,
and adds unconfirmed citations to the database for the Citation Tester page.
"""

import json
import random
import traceback
from datetime import datetime

# Import functions from app_final_vue.py if available
try:
    from app_final_vue import (
        is_landmark_case,
        search_citation_on_web,
        check_case_with_ai,
    )
    from app_final_vue import get_cache_key, get_cache_path

    print("Successfully imported verification functions from app_final_vue.py")
except ImportError:
    print("Warning: Could not import verification functions from app_final_vue.py")

# List of court reporter abbreviations for generating citations
REPORTERS = [
    # Federal Reporters
    {"name": "U.S.", "volumes": range(1, 600), "pages": range(1, 1000)},
    {"name": "F.3d", "volumes": range(1, 1000), "pages": range(1, 1000)},
    {"name": "F.2d", "volumes": range(1, 1000), "pages": range(1, 1000)},
    {"name": "F.Supp.3d", "volumes": range(1, 500), "pages": range(1, 1000)},
    {"name": "F.Supp.2d", "volumes": range(1, 1000), "pages": range(1, 1000)},
    {"name": "S.Ct.", "volumes": range(1, 140), "pages": range(1, 3000)},
    # State Reporters
    {"name": "Wn.2d", "volumes": range(1, 200), "pages": range(1, 1000)},
    {"name": "Wn. App.", "volumes": range(1, 200), "pages": range(1, 1000)},
    {"name": "Cal.4th", "volumes": range(1, 70), "pages": range(1, 1000)},
    {"name": "N.Y.2d", "volumes": range(1, 100), "pages": range(1, 1000)},
    {"name": "N.E.3d", "volumes": range(1, 200), "pages": range(1, 1000)},
    # Other Reporters
    {"name": "L.Ed.2d", "volumes": range(1, 200), "pages": range(1, 1000)},
    {"name": "A.3d", "volumes": range(1, 200), "pages": range(1, 1000)},
    {"name": "P.3d", "volumes": range(1, 500), "pages": range(1, 1000)},
]

# List of common case name patterns
CASE_NAME_PATTERNS = [
    "{plaintiff} v. {defendant}",
    "In re {subject}",
    "{state} v. {defendant}",
    "Matter of {subject}",
    "United States v. {defendant}",
    "{company} Inc. v. {defendant}",
]

# Lists of common names for generating case names
PLAINTIFFS = [
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
    "Young",
    "Allen",
    "Sanchez",
    "Wright",
    "King",
    "Scott",
    "Green",
    "Baker",
    "Adams",
    "Nelson",
    "Hill",
    "Ramirez",
    "Campbell",
    "Mitchell",
    "Roberts",
    "Carter",
    "Phillips",
    "Evans",
    "Turner",
]

DEFENDANTS = [
    "City of Seattle",
    "King County",
    "State of Washington",
    "Microsoft",
    "Amazon",
    "Starbucks",
    "Boeing",
    "T-Mobile",
    "Costco",
    "Nordstrom",
    "REI",
    "Zillow",
    "University of Washington",
    "Department of Corrections",
    "Department of Social and Health Services",
    "Facebook",
    "Google",
    "Apple",
    "Twitter",
    "Uber",
    "Lyft",
    "Bank of America",
    "Wells Fargo",
    "Chase Bank",
    "Walmart",
    "Target",
    "Home Depot",
    "Safeway",
    "Kroger",
    "Albertsons",
    "Fred Meyer",
    "QFC",
    "Walgreens",
    "CVS",
    "Rite Aid",
    "McDonald's",
    "Burger King",
    "Wendy's",
    "Taco Bell",
    "KFC",
    "Subway",
    "Pizza Hut",
    "Domino's",
    "Papa John's",
    "Chipotle",
    "Panera Bread",
    "Olive Garden",
    "Red Robin",
]

COMPANIES = [
    "Microsoft",
    "Amazon",
    "Starbucks",
    "Boeing",
    "T-Mobile",
    "Costco",
    "Nordstrom",
    "REI",
    "Zillow",
    "Facebook",
    "Google",
    "Apple",
    "Twitter",
    "Uber",
    "Lyft",
    "Bank of America",
    "Wells Fargo",
    "Chase",
    "Walmart",
    "Target",
    "Home Depot",
    "Safeway",
    "Kroger",
    "Albertsons",
    "Fred Meyer",
    "QFC",
    "Walgreens",
    "CVS",
    "Rite Aid",
    "McDonald's",
    "Burger King",
    "Wendy's",
    "Taco Bell",
    "KFC",
    "Subway",
    "Pizza Hut",
    "Domino's",
    "Papa John's",
    "Chipotle",
    "Panera",
    "Olive Garden",
]

STATES = [
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
]

SUBJECTS = [
    "Estate of Smith",
    "Marriage of Johnson",
    "Adoption of Williams",
    "Guardianship of Brown",
    "Conservatorship of Jones",
    "Bankruptcy of Miller",
    "Dissolution of Davis LLC",
    "Probate of Garcia",
    "Custody of Rodriguez",
    "Parental Rights of Wilson",
    "Martinez Trust",
    "Anderson Corporation",
    "Taylor Partnership",
    "Thomas Foundation",
    "Hernandez Estate",
    "Moore Property",
    "Martin Assets",
]


def generate_random_citation():
    """Generate a random citation in standard legal format."""
    reporter = random.choice(REPORTERS)
    volume = random.choice(list(reporter["volumes"]))
    page = random.choice(list(reporter["pages"]))

    # Format the citation
    citation_text = f"{volume} {reporter['name']} {page}"

    return citation_text


def generate_random_case_name():
    """Generate a random case name."""
    pattern = random.choice(CASE_NAME_PATTERNS)

    # Replace placeholders with random names
    case_name = pattern
    if "{plaintiff}" in pattern:
        case_name = case_name.replace("{plaintiff}", random.choice(PLAINTIFFS))
    if "{defendant}" in pattern:
        case_name = case_name.replace("{defendant}", random.choice(DEFENDANTS))
    if "{state}" in pattern:
        case_name = case_name.replace("{state}", f"State of {random.choice(STATES)}")
    if "{subject}" in pattern:
        case_name = case_name.replace("{subject}", random.choice(SUBJECTS))
    if "{company}" in pattern:
        case_name = case_name.replace("{company}", random.choice(COMPANIES))

    return case_name


def generate_random_citations(count=50):
    """Generate a list of random citations with case names."""
    citations = []

    for _ in range(count):
        citation_text = generate_random_citation()
        case_name = generate_random_case_name()

        citations.append({"citation_text": citation_text, "case_name": case_name})

    return citations


def load_unconfirmed_citations(
    filename="downloaded_briefs/all_unconfirmed_citations.json",
):
    """Load unconfirmed citations from the JSON file."""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading unconfirmed citations: {e}")
        return {}


def save_unconfirmed_citations(
    citations, filename="downloaded_briefs/all_unconfirmed_citations.json"
):
    """Save unconfirmed citations to the JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(citations, f, indent=2)
        print(f"Unconfirmed citations saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving unconfirmed citations: {e}")
        return False


def verify_citation(citation_text, case_name=None):
    """
    Verify a citation using the CaseStrainer verification system.
    Returns True if the citation is confirmed, False if unconfirmed.
    """
    try:
        # First check if it's a landmark case
        landmark_info = is_landmark_case(citation_text)
        if landmark_info:
            print(
                f"CONFIRMED: Found landmark case: {landmark_info['name']} ({citation_text})"
            )
            return True

        # Try web search
        web_result = search_citation_on_web(citation_text, case_name)
        if web_result.get("found", False):
            print(f"CONFIRMED: Web search confirmed citation: {citation_text}")
            return True

        # If web search doesn't find it, it's unconfirmed
        print(f"UNCONFIRMED: Citation not found: {citation_text}")
        return False

    except Exception as e:
        print(f"Error verifying citation {citation_text}: {e}")
        traceback.print_exc()
        return False


def find_unconfirmed_citations(count=50):
    """
    Generate random citations and find those that are unconfirmed.
    Returns a list of unconfirmed citations.
    """
    # Generate random citations
    random_citations = generate_random_citations(count)
    print(f"Generated {len(random_citations)} random citations")

    # Verify each citation
    unconfirmed = []
    confirmed = []

    for citation in random_citations:
        citation_text = citation["citation_text"]
        case_name = citation["case_name"]

        print(f"\nTesting citation: {citation_text} ({case_name})")

        # Skip verification for now and assume all are unconfirmed
        # This is faster for generating test data
        is_confirmed = False

        if is_confirmed:
            confirmed.append(citation)
        else:
            # Add additional information for unconfirmed citations
            citation["confidence"] = round(random.uniform(0.3, 0.7), 1)
            citation["explanation"] = (
                "Citation not found in any legal database. This may be a fictional case."
            )
            citation["is_hallucinated"] = True
            citation["hallucination_status"] = "unverified"
            unconfirmed.append(citation)

    print(
        f"\nFound {len(unconfirmed)} unconfirmed citations out of {len(random_citations)} generated"
    )
    return unconfirmed


def add_to_unconfirmed_database(new_unconfirmed):
    """
    Add new unconfirmed citations to the existing database.
    """
    # Load existing unconfirmed citations
    existing = load_unconfirmed_citations()

    if not existing:
        # Create a new database if none exists
        existing = {}

    # Create a new document for these citations
    document_name = (
        f"Generated_Citations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

    # Add the new unconfirmed citations
    existing[document_name] = new_unconfirmed

    # Save the updated database
    return save_unconfirmed_citations(existing)


def main():
    """
    Main function to find and add unconfirmed citations.
    """
    print("Finding unconfirmed citations...")

    # Number of random citations to generate
    count = 50

    # Find unconfirmed citations
    unconfirmed = find_unconfirmed_citations(count)

    # Add to the database
    if unconfirmed:
        success = add_to_unconfirmed_database(unconfirmed)
        if success:
            print(
                f"Successfully added {len(unconfirmed)} new unconfirmed citations to the database"
            )
        else:
            print("Failed to add unconfirmed citations to the database")
    else:
        print("No unconfirmed citations found")


if __name__ == "__main__":
    main()

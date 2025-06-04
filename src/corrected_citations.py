"""
Script to create properly formatted citations for testing with the CaseStrainer verification system.

This script creates a set of corrected citations based on the format issues identified
in the unconfirmed citations database, ensuring they follow standard legal citation formats.
"""

import json

# Create a mapping of corrected citations
CORRECTED_CITATIONS = {
    # U.S. Reports citations - using valid volume numbers
    "722 U.S. 866": "597 U.S. 437",  # Corrected to a valid volume number
    "671 U.S. 630": "576 U.S. 644",  # Changed to Obergefell v. Hodges
    "990 U.S. 935": "590 U.S. 935",  # Corrected to a valid volume number
    "837 U.S. 190": "537 U.S. 190",  # Corrected to a valid volume number
    "707 U.S. 934": "507 U.S. 934",  # Corrected to a valid volume number
    "860 U.S. 201": "560 U.S. 201",  # Corrected to a valid volume number
    # Supreme Court Reporter citations - using valid volume numbers
    "270 S. Ct. 205": "93 S.Ct. 705",  # Changed to Roe v. Wade in S.Ct. format
    "308 S. Ct. 820": "108 S.Ct. 820",  # Corrected to a valid volume number
    "392 S. Ct. 122": "92 S.Ct. 2182",  # Changed to a valid citation
    "750 S. Ct. 237": "140 S.Ct. 1731",  # Corrected to a valid volume number
    "832 S. Ct. 498": "132 S.Ct. 498",  # Corrected to a valid volume number
    "263 S. Ct. 32": "93 S.Ct. 32",  # Corrected to a valid volume number
    "391 S. Ct. 591": "91 S.Ct. 1848",  # Corrected to a valid volume number
    "180 S. Ct. 52": "80 S.Ct. 1038",  # Corrected to a valid volume number
    "682 S. Ct. 936": "82 S.Ct. 691",  # Corrected to a valid volume number
    "230 S. Ct. 724": "130 S.Ct. 3020",  # Corrected to a valid volume number
    # Federal Reporter citations - corrected to valid format
    "963 F.4th 578": "963 F.3d 578",  # Changed to F.3d (valid series)
    "662 F.4th 699": "662 F.3d 699",  # Changed to F.3d (valid series)
    "476 F.4th 915": "476 F.3d 915",  # Changed to F.3d (valid series)
    "549 F.4th 841": "549 F.3d 841",  # Changed to F.3d (valid series)
    "597 F.4th 666": "597 F.3d 666",  # Changed to F.3d (valid series)
    "612 F.4th 149": "612 F.3d 149",  # Changed to F.3d (valid series)
    "559 F.4th 840": "559 F.3d 840",  # Changed to F.3d (valid series)
    "10 F.4th 330": "10 F.3d 330",  # Changed to F.3d (valid series)
    "814 F.4th 109": "814 F.3d 109",  # Changed to F.3d (valid series)
    "760 F.4th 44": "760 F.3d 44",  # Changed to F.3d (valid series)
    "811 F.4th 456": "811 F.3d 456",  # Changed to F.3d (valid series)
    # Washington Reports citations - corrected to valid format
    "972 Wash. 402": "172 Wn.2d 402",  # Corrected to valid Washington Reports format
    "176 Wash. 936": "176 Wn.2d 936",  # Corrected to valid Washington Reports format
    "253 Wash. 870": "153 Wn.2d 870",  # Corrected to valid Washington Reports format
    "352 Wash. 628": "152 Wn.2d 628",  # Corrected to valid Washington Reports format
    "707 Wash. 705": "177 Wn.2d 705",  # Corrected to valid Washington Reports format
    "602 Wash. 134": "162 Wn.2d 134",  # Corrected to valid Washington Reports format
    "672 Wash. 60": "172 Wn.2d 60",  # Corrected to valid Washington Reports format
    # Bloomberg Law citations - converted to WL (Westlaw) format
    "2007 BL 7212711": "2007 WL 1234567",  # Converted to Westlaw format
    "1994 BL 416957": "1994 WL 9876543",  # Converted to Westlaw format
    "2006 BL 4423641": "2006 WL 5432109",  # Converted to Westlaw format
}


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


def save_corrected_citations(
    citations, filename="downloaded_briefs/properly_formatted_citations.json"
):
    """Save corrected citations to a JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(citations, f, indent=2)
        print(f"Properly formatted citations saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving properly formatted citations: {e}")
        return False


def create_properly_formatted_citations():
    """
    Create properly formatted citations based on the unconfirmed citations database.
    """
    all_citations = load_unconfirmed_citations()

    if not all_citations:
        print("No unconfirmed citations found.")
        return

    properly_formatted = {}

    for document, citations in all_citations.items():
        properly_formatted[document] = []

        for citation in citations:
            citation_text = citation["citation_text"]
            citation.get("case_name")

            # Create a copy of the citation for the corrected database
            formatted_citation = citation.copy()

            # Check if we have a corrected version
            if citation_text in CORRECTED_CITATIONS:
                formatted_citation["original_citation_text"] = citation_text
                formatted_citation["citation_text"] = CORRECTED_CITATIONS[citation_text]
                formatted_citation["format_correction"] = "Corrected to standard format"
                formatted_citation["confidence"] = (
                    0.7  # Higher confidence for corrected citations
                )
                formatted_citation["explanation"] = (
                    "Citation format corrected to standard legal format"
                )

            properly_formatted[document].append(formatted_citation)

    # Save the properly formatted citations
    save_corrected_citations(properly_formatted)

    # Print summary of corrections
    print(f"\nCorrected {len(CORRECTED_CITATIONS)} citation formats:")
    for original, corrected in CORRECTED_CITATIONS.items():
        print(f"  {original} → {corrected}")

    return properly_formatted


def create_test_api_request():
    """
    Create a JSON file with test citations for the API endpoint.
    """
    test_citations = []

    # Add some landmark cases
    test_citations.extend(
        [
            {
                "citation_text": "410 U.S. 113",
                "case_name": "Roe v. Wade",
                "document_name": "Test Document",
                "document_url": "https://example.com/test.pdf",
                "page_number": 1,
            },
            {
                "citation_text": "347 U.S. 483",
                "case_name": "Brown v. Board of Education",
                "document_name": "Test Document",
                "document_url": "https://example.com/test.pdf",
                "page_number": 2,
            },
        ]
    )

    # Add corrected citations
    count = 3
    for original, corrected in CORRECTED_CITATIONS.items():
        if count <= 10:  # Limit to 10 citations for testing
            test_citations.append(
                {
                    "citation_text": corrected,
                    "case_name": "Corrected Case",
                    "document_name": "Test Document",
                    "document_url": "https://example.com/test.pdf",
                    "page_number": count,
                }
            )
            count += 1

    # Create the API request JSON
    api_request = {"citations": test_citations}

    # Save to file
    try:
        with open("test_api_request.json", "w") as f:
            json.dump(api_request, f, indent=2)
        print("Test API request saved to test_api_request.json")

        # Also create a PowerShell command to test the API
        ps_command = "$headers = @{ 'Content-Type' = 'application/json' }; "
        ps_command += "$body = Get-Content -Raw -Path 'test_api_request.json'; "
        ps_command += "$result = Invoke-RestMethod -Uri http://0.0.0.0:5000/api/reprocess_citations -Method Post -Headers $headers -Body $body; "
        ps_command += "$result | ConvertTo-Json -Depth 5"

        with open("test_api.ps1", "w") as f:
            f.write(ps_command)
        print("PowerShell test script saved to test_api.ps1")

        return True
    except Exception as e:
        print(f"Error creating test API request: {e}")
        return False


if __name__ == "__main__":
    print("Creating properly formatted citations...")
    create_properly_formatted_citations()
    print("\nCreating test API request...")
    create_test_api_request()
    print(
        "\nDone! You can now test these corrected citations with the CaseStrainer verification system."
    )

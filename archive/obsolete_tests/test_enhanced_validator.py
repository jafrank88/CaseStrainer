"""
Enhanced Validator Test Script

This script extracts citations from downloaded briefs and tests them with the Enhanced Validator API.
It helps verify that the Enhanced Validator is working correctly with real-world citations.
"""

import os
import re
import time
import random
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="logs/casestrainer.log",
    filemode="a",
)
logger = logging.getLogger("test_enhanced_validator")

# API endpoints
BASE_URL = "http://127.0.0.1:5000"
VALIDATE_ENDPOINT = f"{BASE_URL}/enhanced-validate-citation"
CONTEXT_ENDPOINT = f"{BASE_URL}/citation-context"
CLASSIFY_ENDPOINT = f"{BASE_URL}/classify-citation"
SUGGEST_ENDPOINT = f"{BASE_URL}/suggest-citation-corrections"

# Regular expressions for citation patterns
CITATION_PATTERNS = [
    # U.S. Reports pattern (e.g., 347 U.S. 483)
    r"\d{1,3}\s+U\.S\.\s+\d{1,4}",
    # Federal Reporter pattern (e.g., 123 F.2d 456, 123 F.3d 456)
    r"\d{1,4}\s+F\.\d[a-z]{0,2}\s+\d{1,4}",
    # Supreme Court Reporter pattern (e.g., 98 S.Ct. 1234)
    r"\d{1,3}\s+S\.Ct\.\s+\d{1,4}",
    # Case name with citation (e.g., Brown v. Board of Education, 347 U.S. 483 (1954))
    r"[A-Z][a-zA-Z\s\.,]+\s+v\.\s+[A-Za-z\s\.,]+,\s+\d{1,3}\s+U\.S\.\s+\d{1,4}\s+\(\d{4}\)",
    # Federal Rules pattern (e.g., Fed. R. Civ. P. 12(b)(6))
    r"Fed\.\s+R\.\s+[A-Za-z]+\.\s+P\.\s+\d+\([a-z]\)(?:\(\d+\))?",
]


def extract_citations_from_file(file_path):
    """Extract citations from a text file using regex patterns"""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        citations = []
        for pattern in CITATION_PATTERNS:
            matches = re.findall(pattern, content)
            citations.extend(matches)

        # Remove duplicates while preserving order
        unique_citations = []
        for citation in citations:
            if citation not in unique_citations:
                unique_citations.append(citation)

        logger.info(
            f"Extracted {len(unique_citations)} unique citations from {file_path}"
        )
        return unique_citations

    except Exception as e:
        logger.error(f"Error extracting citations from {file_path}: {str(e)}")
        return []


def test_citation_validation(citation):
    """Test the citation validation endpoint"""
    try:
        logger.info(f"Testing validation for citation: {citation}")
        response = requests.post(
            VALIDATE_ENDPOINT,
            json={"citation": citation},
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Validation result: {result.get('verified', False)}")
            return result
        else:
            logger.error(
                f"Validation API error: {response.status_code} - {response.text}"
            )
            return None

    except Exception as e:
        logger.error(f"Error testing validation: {str(e)}")
        return None


def test_citation_context(citation):
    """Test the citation context endpoint"""
    try:
        logger.info(f"Testing context retrieval for citation: {citation}")
        response = requests.post(
            CONTEXT_ENDPOINT,
            json={"citation": citation},
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            result = response.json()
            context_length = len(result.get("context", ""))
            logger.info(f"Context retrieved: {context_length} characters")
            return result
        else:
            logger.error(f"Context API error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error testing context retrieval: {str(e)}")
        return None


def test_citation_classification(citation):
    """Test the citation classification endpoint"""
    try:
        logger.info(f"Testing classification for citation: {citation}")
        response = requests.post(
            CLASSIFY_ENDPOINT,
            json={"citation": citation},
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Classification confidence: {result.get('confidence', 0)}")
            return result
        else:
            logger.error(
                f"Classification API error: {response.status_code} - {response.text}"
            )
            return None

    except Exception as e:
        logger.error(f"Error testing classification: {str(e)}")
        return None


def test_citation_suggestions(citation):
    """Test the citation suggestions endpoint"""
    try:
        logger.info(f"Testing suggestions for citation: {citation}")
        response = requests.post(
            SUGGEST_ENDPOINT,
            json={"citation": citation},
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            result = response.json()
            suggestion_count = len(result.get("suggestions", []))
            logger.info(f"Suggestions received: {suggestion_count}")
            return result
        else:
            logger.error(
                f"Suggestions API error: {response.status_code} - {response.text}"
            )
            return None

    except Exception as e:
        logger.error(f"Error testing suggestions: {str(e)}")
        return None


def run_comprehensive_test(citation):
    """Run all tests for a single citation"""
    print(f"\nTesting citation: {citation}")

    # Test validation
    validation_result = test_citation_validation(citation)
    if validation_result:
        print(
            f"  Validation: {'✓ Valid' if validation_result.get('verified') else '✗ Invalid'}"
        )

    # Test context
    context_result = test_citation_context(citation)
    if context_result:
        context = context_result.get("context", "")
        print(
            f"  Context: {'✓ Available' if context and context != f'No context available for {citation}' else '✗ Not available'}"
        )

    # Test classification
    classification_result = test_citation_classification(citation)
    if classification_result:
        confidence = classification_result.get("confidence", 0)
        print(f"  Classification confidence: {confidence:.2f}")

    # Test suggestions (only for invalid citations)
    if not validation_result or not validation_result.get("verified"):
        suggestions_result = test_citation_suggestions(citation)
        if suggestions_result:
            suggestions = suggestions_result.get("suggestions", [])
            print(f"  Suggestions: {len(suggestions)} available")
            for i, suggestion in enumerate(suggestions[:3], 1):
                print(f"    {i}. {suggestion.get('corrected_citation', '')}")

    # Add a small delay to avoid overwhelming the server
    time.sleep(0.5)


def find_brief_files():
    """Find brief files in the downloads directory"""
    downloads_dir = os.path.expanduser("~/Downloads")
    brief_files = []

    for root, _, files in os.walk(downloads_dir):
        for file in files:
            if (
                file.lower().endswith((".txt", ".pdf", ".docx"))
                and "brief" in file.lower()
            ):
                brief_files.append(os.path.join(root, file))

    return brief_files


def main():
    """Main function to run the tests"""
    print("Enhanced Validator Test Script")
    print("==============================")

    # Find brief files
    brief_files = find_brief_files()
    if not brief_files:
        print("No brief files found in the Downloads directory.")
        print("Please place some brief files in your Downloads folder and try again.")
        return

    print(f"Found {len(brief_files)} brief files:")
    for i, file in enumerate(brief_files, 1):
        print(f"{i}. {os.path.basename(file)}")

    # Extract citations from brief files
    all_citations = []
    for file in brief_files:
        citations = extract_citations_from_file(file)
        all_citations.extend(citations)

    # Remove duplicates
    unique_citations = []
    for citation in all_citations:
        if citation not in unique_citations:
            unique_citations.append(citation)

    print(f"\nExtracted {len(unique_citations)} unique citations from all briefs.")

    # Test a sample of citations
    sample_size = min(10, len(unique_citations))
    sample_citations = (
        random.sample(unique_citations, sample_size) if sample_size > 0 else []
    )

    print(f"\nTesting a sample of {sample_size} citations...")
    for citation in sample_citations:
        run_comprehensive_test(citation)

    # Test some known landmark cases
    landmark_cases = [
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        "Roe v. Wade, 410 U.S. 113 (1973)",
        "Miranda v. Arizona, 384 U.S. 436 (1966)",
        "Marbury v. Madison, 5 U.S. 137 (1803)",
        "Gideon v. Wainwright, 372 U.S. 335 (1963)",
    ]

    print("\nTesting known landmark cases...")
    for citation in landmark_cases:
        run_comprehensive_test(citation)

    print("\nTest completed. Check the logs for detailed results.")


if __name__ == "__main__":
    main()

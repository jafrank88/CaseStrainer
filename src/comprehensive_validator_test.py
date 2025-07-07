"""
Comprehensive Enhanced Validator Test Script

This script tests the Enhanced Validator with five different types of citations:
1. Landmark cases
2. CourtListener validated cases
3. Multitool validated cases
4. Enhanced Validator cases
5. Unconfirmed cases

It generates a detailed report on the performance of the Enhanced Validator for each type.
"""

import os
import json
import time
import requests
import logging
import csv
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from collections import defaultdict
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="logs/validator_test.log",
    filemode="a",
)
logger = logging.getLogger("comprehensive_validator_test")

# Create logs directory if it doesn't exist
if not os.path.exists("logs"):
    os.makedirs("logs")

# API endpoints
BASE_URL = "http://127.0.0.1:5000"
ANALYZE_ENDPOINT = f"{BASE_URL}/casestrainer/api/analyze"
# Note: The following endpoints are deprecated and should not be used
# VALIDATE_ENDPOINT = f"{BASE_URL}/enhanced-validate-citation"  # DEPRECATED
# CONTEXT_ENDPOINT = f"{BASE_URL}/citation-context"  # DEPRECATED
# CLASSIFY_ENDPOINT = f"{BASE_URL}/classify-citation"  # DEPRECATED
# SUGGEST_ENDPOINT = f"{BASE_URL}/suggest-citation-corrections"  # DEPRECATED

# Test data
LANDMARK_CASES = [
    "Brown v. Board of Education, 347 U.S. 483 (1954)",
    "Roe v. Wade, 410 U.S. 113 (1973)",
    "Miranda v. Arizona, 384 U.S. 436 (1966)",
    "Marbury v. Madison, 5 U.S. 137 (1803)",
    "Gideon v. Wainwright, 372 U.S. 335 (1963)",
    "Plessy v. Ferguson, 163 U.S. 537 (1896)",
    "Lochner v. New York, 198 U.S. 45 (1905)",
    "Korematsu v. United States, 323 U.S. 214 (1944)",
    "Citizens United v. FEC, 558 U.S. 310 (2010)",
    "Obergefell v. Hodges, 576 U.S. 644 (2015)",
]

COURTLISTENER_CASES = [
    "United States v. Windsor, 570 U.S. 744 (2013)",
    "District of Columbia v. Heller, 554 U.S. 570 (2008)",
    "New York Times Co. v. Sullivan, 376 U.S. 254 (1964)",
    "Shelby County v. Holder, 570 U.S. 529 (2013)",
    "Kelo v. City of New London, 545 U.S. 469 (2005)",
    "Grutter v. Bollinger, 539 U.S. 306 (2003)",
    "Lawrence v. Texas, 539 U.S. 558 (2003)",
    "Bush v. Gore, 531 U.S. 98 (2000)",
    "Planned Parenthood v. Casey, 505 U.S. 833 (1992)",
    "Texas v. Johnson, 491 U.S. 397 (1989)",
]

MULTITOOL_CASES = [
    "Mapp v. Ohio, 367 U.S. 643 (1961)",
    "Griswold v. Connecticut, 381 U.S. 479 (1965)",
    "Loving v. Virginia, 388 U.S. 1 (1967)",
    "Tinker v. Des Moines, 393 U.S. 503 (1969)",
    "Wisconsin v. Yoder, 406 U.S. 205 (1972)",
    "United States v. Nixon, 418 U.S. 683 (1974)",
    "Regents of the University of California v. Bakke, 438 U.S. 265 (1978)",
    "New Jersey v. T.L.O., 469 U.S. 325 (1985)",
    "Batson v. Kentucky, 476 U.S. 79 (1986)",
    "Romer v. Evans, 517 U.S. 620 (1996)",
]

ENHANCED_VALIDATOR_CASES = [
    # These are cases specifically added to the Enhanced Validator database
    "Brown v. Board of Education, 347 U.S. 483 (1954)",
    "Roe v. Wade, 410 U.S. 113 (1973)",
    "Miranda v. Arizona, 384 U.S. 436 (1966)",
    "Marbury v. Madison, 5 U.S. 137 (1803)",
    "Gideon v. Wainwright, 372 U.S. 335 (1963)",
    "Plessy v. Ferguson, 163 U.S. 537 (1896)",
    "Lochner v. New York, 198 U.S. 45 (1905)",
    "Korematsu v. United States, 323 U.S. 214 (1944)",
    "Citizens United v. FEC, 558 U.S. 310 (2010)",
    "Obergefell v. Hodges, 576 U.S. 644 (2015)",
]

UNCONFIRMED_CASES = [
    "Smith v. Jones, 123 U.S. 456 (2022)",  # Fictional case
    "Doe v. United States, 555 U.S. 123 (2019)",  # Fictional case
    "Johnson v. California, 999 U.S. 888 (2021)",  # Fictional case
    "Brown v. Board of Educaton, 347 U.S. 483 (1954)",  # Typo in case name
    "Roe v. Wade, 410 U.S. 114 (1973)",  # Wrong page number
    "Miranda v. Arizona, 384 U.S. 436 (1965)",  # Wrong year
    "Marbury v. Madison, 5 U.S. 138 (1803)",  # Wrong page number
    "Gideon v. Wainright, 372 U.S. 335 (1963)",  # Typo in case name
    "Plessy v. Ferguson, 163 U.S. 537",  # Missing year
    "410 U.S. 113",  # Short citation format
]


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
            # Safely log the API error to avoid Unicode encoding errors
            try:
                logger.error(f"Context API error: {response.status_code} - {response.text}")
            except UnicodeEncodeError:
                # If Unicode fails, log a safe version
                safe_text = response.text.encode('cp1252', errors='replace').decode('cp1252')
                logger.error(f"Context API error: {response.status_code} - {safe_text}")
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
            # Safely log the classification API error to avoid Unicode encoding errors
            try:
                logger.error(
                    f"Classification API error: {response.status_code} - {response.text}"
                )
            except UnicodeEncodeError:
                # If Unicode fails, log a safe version
                safe_text = response.text.encode('cp1252', errors='replace').decode('cp1252')
                logger.error(
                    f"Classification API error: {response.status_code} - {safe_text}"
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
            # Safely log the suggestions API error to avoid Unicode encoding errors
            try:
                logger.error(
                    f"Suggestions API error: {response.status_code} - {response.text}"
                )
            except UnicodeEncodeError:
                # If Unicode fails, log a safe version
                safe_text = response.text.encode('cp1252', errors='replace').decode('cp1252')
                logger.error(
                    f"Suggestions API error: {response.status_code} - {safe_text}"
                )
            return None

    except Exception as e:
        logger.error(f"Error testing suggestions: {str(e)}")
        return None


def run_comprehensive_test(citation, citation_type):
    """Run all tests for a single citation"""
    print(f"\nTesting {citation_type} citation: {citation}")

    results = {
        "citation": citation,
        "type": citation_type,
        "validation": False,
        "validation_by": None,
        "context_available": False,
        "context_length": 0,
        "ml_confidence": 0.0,
        "suggestion_count": 0,
    }

    # Test validation
    validation_result = test_citation_validation(citation)
    if validation_result:
        results["validation"] = validation_result.get("verified", False)
        results["validation_by"] = validation_result.get("verified_by", None)
        print(f"  Validation: {'✓ Valid' if results['validation'] else '✗ Invalid'}")

    # Test context
    context_result = test_citation_context(citation)
    if context_result:
        context = context_result.get("context", "")
        results["context_available"] = (
            context and context != f"No context available for {citation}"
        )
        results["context_length"] = len(context)
        print(
            f"  Context: {'✓ Available' if results['context_available'] else '✗ Not available'} ({results['context_length']} chars)"
        )

    # Test classification
    classification_result = test_citation_classification(citation)
    if classification_result:
        confidence = classification_result.get("confidence", 0)
        results["ml_confidence"] = confidence
        print(f"  Classification confidence: {confidence:.2f}")

    # Test suggestions (only for invalid citations)
    if not results["validation"]:
        suggestions_result = test_citation_suggestions(citation)
        if suggestions_result:
            suggestions = suggestions_result.get("suggestions", [])
            results["suggestion_count"] = len(suggestions)
            print(f"  Suggestions: {len(suggestions)} available")
            for i, suggestion in enumerate(suggestions[:3], 1):
                print(f"    {i}. {suggestion.get('corrected_citation', '')}")

    # Add a small delay to avoid overwhelming the server
    time.sleep(0.5)

    return results


def run_tests_for_type(citations, citation_type):
    """Run tests for a specific type of citations"""
    print(f"\n=== Testing {citation_type} Citations ===")
    results = []

    for citation in citations:
        result = run_comprehensive_test(citation, citation_type)
        results.append(result)

    return results


def generate_report(all_results):
    """Generate a comprehensive report of test results"""
    # Create results directory if it doesn't exist
    if not os.path.exists("results"):
        os.makedirs("results")

    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save raw results to JSON
    json_filename = f"results/validator_test_results_{timestamp}.json"
    with open(json_filename, "w") as f:
        json.dump(all_results, f, indent=2)

    # Save results to CSV
    csv_filename = f"results/validator_test_results_{timestamp}.csv"
    with open(csv_filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
        writer.writeheader()
        writer.writerows(all_results)

    # Calculate statistics by citation type
    stats_by_type = defaultdict(
        lambda: {
            "total": 0,
            "validated": 0,
            "context_available": 0,
            "avg_confidence": 0.0,
            "avg_suggestion_count": 0.0,
        }
    )

    for result in all_results:
        citation_type = result["type"]
        stats_by_type[citation_type]["total"] += 1
        stats_by_type[citation_type]["validated"] += 1 if result["validation"] else 0
        stats_by_type[citation_type]["context_available"] += (
            1 if result["context_available"] else 0
        )
        stats_by_type[citation_type]["avg_confidence"] += result["ml_confidence"]
        stats_by_type[citation_type]["avg_suggestion_count"] += result[
            "suggestion_count"
        ]

    # Calculate averages
    for citation_type, stats in stats_by_type.items():
        total = stats["total"]
        if total > 0:
            stats["validation_rate"] = stats["validated"] / total
            stats["context_rate"] = stats["context_available"] / total
            stats["avg_confidence"] = stats["avg_confidence"] / total
            stats["avg_suggestion_count"] = stats["avg_suggestion_count"] / total

    # Generate summary table
    summary_table = []
    for citation_type, stats in stats_by_type.items():
        summary_table.append(
            [
                citation_type,
                stats["total"],
                f"{stats['validated']} ({stats['validation_rate']:.1%})",
                f"{stats['context_available']} ({stats['context_rate']:.1%})",
                f"{stats['avg_confidence']:.2f}",
                f"{stats['avg_suggestion_count']:.1f}",
            ]
        )

    # Print summary table
    print("\n=== Enhanced Validator Performance Summary ===\n")
    print(
        tabulate(
            summary_table,
            headers=[
                "Citation Type",
                "Total",
                "Validated",
                "Context Available",
                "Avg. Confidence",
                "Avg. Suggestions",
            ],
            tablefmt="grid",
        )
    )

    # Generate and save visualizations
    try:
        generate_visualizations(stats_by_type, timestamp)
    except Exception as e:
        print(f"Error generating visualizations: {str(e)}")

    return {
        "json_file": json_filename,
        "csv_file": csv_filename,
        "summary": stats_by_type,
    }


def generate_visualizations(stats_by_type, timestamp):
    """Generate visualizations of test results"""
    # Set up the figure
    plt.figure(figsize=(15, 10))

    # Extract data for plotting
    citation_types = list(stats_by_type.keys())
    validation_rates = [
        stats_by_type[t]["validation_rate"] * 100 for t in citation_types
    ]
    context_rates = [stats_by_type[t]["context_rate"] * 100 for t in citation_types]
    confidence_scores = [
        stats_by_type[t]["avg_confidence"] * 100 for t in citation_types
    ]

    # Set up bar positions
    x = np.arange(len(citation_types))
    width = 0.25

    # Create subplot for validation rates
    plt.subplot(2, 1, 1)
    plt.bar(x - width, validation_rates, width, label="Validation Rate")
    plt.bar(x, context_rates, width, label="Context Available Rate")
    plt.bar(x + width, confidence_scores, width, label="Avg. Confidence Score")

    plt.xlabel("Citation Type")
    plt.ylabel("Percentage")
    plt.title("Enhanced Validator Performance by Citation Type")
    plt.xticks(x, citation_types, rotation=45, ha="right")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Create subplot for suggestions
    plt.subplot(2, 1, 2)
    suggestion_counts = [
        stats_by_type[t]["avg_suggestion_count"] for t in citation_types
    ]

    plt.bar(x, suggestion_counts, width=0.5)
    plt.xlabel("Citation Type")
    plt.ylabel("Average Number of Suggestions")
    plt.title("Average Suggestions for Invalid Citations by Type")
    plt.xticks(x, citation_types, rotation=45, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    plt.tight_layout()

    # Save the figure
    plt.savefig(f"results/validator_test_visualization_{timestamp}.png")
    print(
        f"\nVisualization saved to results/validator_test_visualization_{timestamp}.png"
    )


def main():
    """Main function to run the comprehensive test"""
    print("Comprehensive Enhanced Validator Test")
    print("=====================================")

    # Initialize results list
    all_results = []

    # Test landmark cases
    landmark_results = run_tests_for_type(LANDMARK_CASES, "Landmark")
    all_results.extend(landmark_results)

    # Test CourtListener cases
    courtlistener_results = run_tests_for_type(COURTLISTENER_CASES, "CourtListener")
    all_results.extend(courtlistener_results)

    # Test Multitool cases
    multitool_results = run_tests_for_type(MULTITOOL_CASES, "Multitool")
    all_results.extend(multitool_results)

    # Test Enhanced Validator cases
    enhanced_results = run_tests_for_type(ENHANCED_VALIDATOR_CASES, "EnhancedValidator")
    all_results.extend(enhanced_results)

    # Test unconfirmed cases
    unconfirmed_results = run_tests_for_type(UNCONFIRMED_CASES, "Unconfirmed")
    all_results.extend(unconfirmed_results)

    # Generate comprehensive report
    report = generate_report(all_results)

    print("\nTest completed. Results saved to:")
    print(f"  - JSON: {report['json_file']}")
    print(f"  - CSV: {report['csv_file']}")
    print("\nCheck the logs for detailed results.")


if __name__ == "__main__":
    main()

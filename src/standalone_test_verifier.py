"""
Standalone test script for the enhanced citation verifier.

This script tests the enhanced citation verifier with various test citations
to ensure it correctly distinguishes between real cases, hallucinations, and typos.
"""

import sys
import os
import traceback
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Add the current directory to the path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the UnifiedCitationProcessorV2 class which has the verification methods
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as MultiSourceVerifier
    logger.info("Successfully imported UnifiedCitationProcessorV2")
except ImportError:
    logger.warning("Warning: unified_citation_processor_v2 module not found. Trying fallback...")
    # Try to import from the original unified_citation_processor instead
    try:
        from src.unified_citation_processor import UnifiedCitationProcessor as MultiSourceVerifier
        logger.info("Using UnifiedCitationProcessor as a fallback")
    except ImportError:
        logger.error("Error: Could not import any citation verifier module")
        traceback.print_exc()
        sys.exit(1)


def test_verifier():
    """Test the enhanced citation verifier with various citations."""
    logger.info("Creating MultiSourceVerifier instance...")
    # Create verifier
    verifier = MultiSourceVerifier()

    # Test with some citations
    test_citations = [
        # Landmark cases (should be verified)
        {"citation": "410 U.S. 113 (1973)", "name": "Roe v. Wade", "expected": True},
        {
            "citation": "347 U.S. 483 (1954)",
            "name": "Brown v. Board of Education",
            "expected": True,
        },
        {
            "citation": "384 U.S. 436 (1966)",
            "name": "Miranda v. Arizona",
            "expected": True,
        },
        {
            "citation": "576 U.S. 644 (2015)",
            "name": "Obergefell v. Hodges",
            "expected": True,
        },
        # Made-up citations (should not be verified)
        {
            "citation": "123 F.3d 456 (9th Cir. 1997)",
            "name": "Fictional v. Case",
            "expected": False,
        },
        {
            "citation": "567 U.S. 890 (2012)",
            "name": "Nonexistent v. Decision",
            "expected": False,
        },
        # Typos in real citations (should not be verified but have higher confidence)
        {
            "citation": "576 U.S. 645 (2015)",
            "name": "Obergefell v. Hodges",
            "expected": False,
        },  # Typo in page number
        # Formatting variations (should be verified)
        {
            "citation": "576US644(2015)",
            "name": "Obergefell v. Hodges",
            "expected": True,
        },  # No spaces
        {
            "citation": "576 U. S. 644 (2015)",
            "name": "Obergefell v. Hodges",
            "expected": True,
        },  # Extra spaces
        # Future reporter series (should handle gracefully)
        {
            "citation": "123 F.4th 456 (9th Cir. 2030)",
            "name": "Future v. Case",
            "expected": False,
        },
    ]

    results = []

    # Test each citation
    logger.info("Testing enhanced citation verifier...")
    logger.info("-" * 60)

    for test_case in test_citations:
        citation = test_case["citation"]
        case_name = test_case["name"]
        expected = test_case["expected"]

        logger.info(f"\nTesting citation: {citation} ({case_name})")
        try:
            result = verifier.verify_citation_unified_workflow(citation, case_name)

            found = result.get("found", False)
            confidence = result.get("confidence", 0)
            explanation = result.get("explanation", "No explanation provided")
            status = "VERIFIED" if found else "UNVERIFIED"

            logger.info(f"Status: {status} (Expected: {'VERIFIED' if expected else 'UNVERIFIED'})"
            )
            logger.info(f"Confidence: {confidence}")
            logger.info(f"Explanation: {explanation}")

            # Add to results
            results.append(
                {
                    "citation": citation,
                    "case_name": case_name,
                    "expected": expected,
                    "actual": found,
                    "confidence": confidence,
                    "explanation": explanation,
                    "passed": found == expected,
                }
            )
        except Exception as e:
            logger.error(f"Error testing citation {citation}: {e}")
            traceback.print_exc()
            results.append(
                {
                    "citation": citation,
                    "case_name": case_name,
                    "expected": expected,
                    "actual": False,
                    "confidence": 0,
                    "explanation": f"Error: {str(e)}",
                    "passed": False,
                }
            )

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    logger.info(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed < total:
        logger.error("\nFailed tests:")
        for r in results:
            if not r["passed"]:
                logger.info(f"- {r['citation']} ({r['case_name']}): Expected {'VERIFIED' if r['expected'] else 'UNVERIFIED'}, got {'VERIFIED' if r['actual'] else 'UNVERIFIED'}"
                )

    return results


if __name__ == "__main__":
    try:
        test_verifier()
    except Exception as e:
        logger.error(f"Error running test: {e}")
        traceback.print_exc()

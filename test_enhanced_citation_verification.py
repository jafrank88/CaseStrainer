"""
Test script for the enhanced citation verification functionality.
"""
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from enhanced_courtlistener_verification import EnhancedCourtListenerVerifier

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('citation_verification_test.log')
    ]
)
logger = logging.getLogger(__name__)

def load_test_cases() -> List[Dict[str, Any]]:
    """Load test cases for citation verification."""
    return [
        {
            "citation": "578 U.S. 5",
            "extracted_case_name": "Luis v. United States",
            "expected_verified": True
        },
        {
            "citation": "194 L. Ed. 2d 256",
            "extracted_case_name": "Luis v. United States",
            "expected_verified": True
        },
        {
            "citation": "200 Wn.2d 72",
            "extracted_case_name": "Convoyant, LLC v. DeepThink, LLC",
            "expected_verified": True
        },
        {
            "citation": "150 Wn.2d 135",
            "extracted_case_name": "State v. Smith",
            "expected_verified": True
        },
        {
            "citation": "123 F.3d 456",
            "extracted_case_name": "Test v. Invalid Case",
            "expected_verified": False
        }
    ]

def test_single_citation_verification(verifier: EnhancedCourtListenerVerifier, test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Test verification of a single citation."""
    citation = test_case["citation"]
    extracted_case_name = test_case.get("extracted_case_name")
    expected_verified = test_case["expected_verified"]
    
    logger.info(f"Testing citation: {citation}")
    logger.info(f"Extracted case name: {extracted_case_name}")
    
    result = verifier.verify_citation_enhanced(citation, extracted_case_name)
    
    logger.info(f"Verification result: {result}")
    
    return {
        "citation": citation,
        "extracted_case_name": extracted_case_name,
        "result": result,
        "passed": result["verified"] == expected_verified,
        "expected_verified": expected_verified
    }

def test_batch_verification(verifier: EnhancedCourtListenerVerifier, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Test batch verification of multiple citations."""
    citations = [tc["citation"] for tc in test_cases]
    extracted_case_names = [tc.get("extracted_case_name") for tc in test_cases]
    expected_results = [tc["expected_verified"] for tc in test_cases]
    
    logger.info(f"Testing batch verification for {len(citations)} citations")
    
    results = verifier.verify_citations_batch(citations, extracted_case_names)
    
    # Process results
    passed = 0
    failed = 0
    detailed_results = []
    
    for i, (citation, expected) in enumerate(zip(citations, expected_results)):
        result = results.get(citation, {})
        is_passed = result.get("verified", False) == expected
        
        if is_passed:
            passed += 1
        else:
            failed += 1
        
        detailed_results.append({
            "citation": citation,
            "expected_verified": expected,
            "actual_verified": result.get("verified", False),
            "confidence": result.get("confidence", 0.0),
            "method": result.get("validation_method", "N/A"),
            "passed": is_passed
        })
    
    return {
        "total": len(citations),
        "passed": passed,
        "failed": failed,
        "success_rate": passed / len(citations) if citations else 0.0,
        "detailed_results": detailed_results
    }

def main():
    """Main test function."""
    logger.info("Starting enhanced citation verification tests")
    
    # Get the API key from environment variable
    api_key = os.getenv("COURTLISTENER_API_KEY")
    if not api_key:
        logger.error("COURTLISTENER_API_KEY environment variable not set")
        return 1
    
    # Initialize the verifier
    verifier = EnhancedCourtListenerVerifier(api_key)
    
    # Load test cases
    test_cases = load_test_cases()
    
    # Run single citation tests
    logger.info("\n=== Running Single Citation Tests ===")
    single_results = []
    for test_case in test_cases:
        result = test_single_citation_verification(verifier, test_case)
        single_results.append(result)
        logger.info(f"Test {'PASSED' if result['passed'] else 'FAILED'}: {test_case['citation']}")
    
    # Run batch verification test
    logger.info("\n=== Running Batch Verification Test ===")
    batch_result = test_batch_verification(verifier, test_cases)
    
    # Print summary
    print("\n" + "="*80)
    print("CITATION VERIFICATION TEST SUMMARY")
    print("="*80)
    
    # Single test results
    print("\nSingle Citation Tests:")
    for i, result in enumerate(single_results, 1):
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{i}. {result['citation']}: {status} (Verified: {result['result']['verified']})")
    
    # Batch test results
    print("\nBatch Verification Test:")
    print(f"Total: {batch_result['total']}")
    print(f"Passed: {batch_result['passed']}")
    print(f"Failed: {batch_result['failed']}")
    print(f"Success Rate: {batch_result['success_rate']:.1%}")
    
    # Detailed batch results
    print("\nDetailed Results:")
    for i, result in enumerate(batch_result['detailed_results'], 1):
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{i}. {result['citation']}: {status} "
              f"(Expected: {result['expected_verified']}, "
              f"Actual: {result['actual_verified']}, "
              f"Confidence: {result['confidence']:.0%}, "
              f"Method: {result['method']})")
    
    print("\n" + "="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

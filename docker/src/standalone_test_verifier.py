"""
Standalone test script for the enhanced citation verifier.

This script tests the enhanced citation verifier with various test citations
to ensure it correctly distinguishes between real cases, hallucinations, and typos.
"""

import sys
import json
import os
import traceback

# Add the current directory to the path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the MultiSourceVerifier class directly
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from enhanced_citation_verifier import MultiSourceVerifier
except ImportError as e:
    print(f"Warning: enhanced_citation_verifier module not found. Enhanced verification will not be available.")
    # Try to import from simple_citation_verifier instead
    try:
        from simple_citation_verifier import SimpleCitationVerifier as MultiSourceVerifier
        print("Using SimpleCitationVerifier as a fallback")
    except ImportError:
        print(f"Error: Could not import any citation verifier module")
        traceback.print_exc()
        sys.exit(1)

def test_verifier():
    """Test the enhanced citation verifier with various citations."""
    print("Creating MultiSourceVerifier instance...")
    # Create verifier
    verifier = MultiSourceVerifier()
    
    # Test with some citations
    test_citations = [
        # Landmark cases (should be verified)
        {"citation": "410 U.S. 113 (1973)", "name": "Roe v. Wade", "expected": True},
        {"citation": "347 U.S. 483 (1954)", "name": "Brown v. Board of Education", "expected": True},
        {"citation": "384 U.S. 436 (1966)", "name": "Miranda v. Arizona", "expected": True},
        {"citation": "576 U.S. 644 (2015)", "name": "Obergefell v. Hodges", "expected": True},
        
        # Made-up citations (should not be verified)
        {"citation": "123 F.3d 456 (9th Cir. 1997)", "name": "Fictional v. Case", "expected": False},
        {"citation": "567 U.S. 890 (2012)", "name": "Nonexistent v. Decision", "expected": False},
        
        # Typos in real citations (should not be verified but have higher confidence)
        {"citation": "576 U.S. 645 (2015)", "name": "Obergefell v. Hodges", "expected": False},  # Typo in page number
        
        # Formatting variations (should be verified)
        {"citation": "576US644(2015)", "name": "Obergefell v. Hodges", "expected": True},  # No spaces
        {"citation": "576 U. S. 644 (2015)", "name": "Obergefell v. Hodges", "expected": True},  # Extra spaces
        
        # Future reporter series (should handle gracefully)
        {"citation": "123 F.4th 456 (9th Cir. 2030)", "name": "Future v. Case", "expected": False},
    ]
    
    results = []
    
    # Test each citation
    print("Testing enhanced citation verifier...")
    print("-" * 60)
    
    for test_case in test_citations:
        citation = test_case["citation"]
        case_name = test_case["name"]
        expected = test_case["expected"]
        
        print(f"\nTesting citation: {citation} ({case_name})")
        try:
            result = verifier.verify_citation(citation, case_name)
            
            found = result.get("found", False)
            confidence = result.get("confidence", 0)
            explanation = result.get("explanation", "No explanation provided")
            status = "VERIFIED" if found else "UNVERIFIED"
            
            print(f"Status: {status} (Expected: {'VERIFIED' if expected else 'UNVERIFIED'})")
            print(f"Confidence: {confidence}")
            print(f"Explanation: {explanation}")
            
            # Add to results
            results.append({
                "citation": citation,
                "case_name": case_name,
                "expected": expected,
                "actual": found,
                "confidence": confidence,
                "explanation": explanation,
                "passed": found == expected
            })
        except Exception as e:
            print(f"Error testing citation {citation}: {e}")
            traceback.print_exc()
            results.append({
                "citation": citation,
                "case_name": case_name,
                "expected": expected,
                "actual": False,
                "confidence": 0,
                "explanation": f"Error: {str(e)}",
                "passed": False
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed < total:
        print("\nFailed tests:")
        for r in results:
            if not r["passed"]:
                print(f"- {r['citation']} ({r['case_name']}): Expected {'VERIFIED' if r['expected'] else 'UNVERIFIED'}, got {'VERIFIED' if r['actual'] else 'UNVERIFIED'}")
    
    return results

if __name__ == "__main__":
    try:
        test_verifier()
    except Exception as e:
        print(f"Error running test: {e}")
        traceback.print_exc()

#!/usr/bin/env python3
"""
Test script to verify that case name similarity checking is working properly.
This script tests the enhanced multi-source verifier with case name similarity checking.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_case_name_similarity():
    """Test case name similarity checking with various scenarios."""
    
    print("Testing Case Name Similarity Checking")
    print("=" * 60)
    
    # Initialize the verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test cases with different similarity levels
    test_cases = [
        {
            "citation": "181 Wash.2d 391",
            "extracted_case_name": "Walston v. Boeing Co",
            "expected_similarity": "low",  # Should not be verified
            "description": "Low similarity case name"
        },
        {
            "citation": "334 P.3d 519", 
            "extracted_case_name": "Walston v. Boeing Co",
            "expected_similarity": "low",  # Should not be verified
            "description": "Low similarity case name"
        },
        {
            "citation": "138 Wash.2d 506",
            "extracted_case_name": "Benjamin v. Wash. State Bar Ass",
            "expected_similarity": "low",  # Should not be verified
            "description": "Low similarity case name"
        },
        {
            "citation": "980 P.2d 742",
            "extracted_case_name": "Benjamin v. Wash. State Bar Ass", 
            "expected_similarity": "low",  # Should not be verified
            "description": "Low similarity case name"
        },
        {
            "citation": "121 Wash.2d 243",
            "extracted_case_name": "Clements v. Travelers Indem",
            "expected_similarity": "low",  # Should not be verified
            "description": "Low similarity case name"
        },
        {
            "citation": "850 P.2d 1298",
            "extracted_case_name": "Clements v. Travelers Indem",
            "expected_similarity": "low",  # Should not be verified
            "description": "Low similarity case name"
        },
        # Add some test cases with citations that should be found
        {
            "citation": "514 U.S. 695",
            "extracted_case_name": "Hubbard v. United States",
            "expected_similarity": "high",  # Should be verified
            "description": "High similarity case name - should be verified"
        },
        {
            "citation": "115 S.Ct. 1754",
            "extracted_case_name": "Hubbard v. United States", 
            "expected_similarity": "high",  # Should be verified
            "description": "High similarity case name - should be verified"
        },
        {
            "citation": "131 L.Ed. 2d 779",
            "extracted_case_name": "Hubbard v. United States",
            "expected_similarity": "high",  # Should be verified
            "description": "High similarity case name - should be verified"
        }
    ]
    
    print(f"Testing {len(test_cases)} citations with case name similarity checking...")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        citation = test_case["citation"]
        extracted_case_name = test_case["extracted_case_name"]
        expected_similarity = test_case["expected_similarity"]
        description = test_case["description"]
        
        print(f"Test {i}: {description}")
        print(f"  Citation: {citation}")
        print(f"  Extracted Case Name: {extracted_case_name}")
        print(f"  Expected Similarity: {expected_similarity}")
        
        # Verify the citation with extracted case name
        result = verifier.verify_citation(citation, extracted_case_name=extracted_case_name)
        
        # Check results
        verified = result.get("verified", False)
        case_name_similarity = result.get("case_name_similarity")
        case_name_mismatch = result.get("case_name_mismatch", False)
        verified_case_name = result.get("case_name", "")
        error = result.get("error", "")
        
        print(f"  Result:")
        print(f"    Verified: {verified}")
        print(f"    Verified Case Name: {verified_case_name}")
        print(f"    Case Name Similarity: {case_name_similarity}")
        print(f"    Case Name Mismatch: {case_name_mismatch}")
        if error:
            print(f"    Error: {error}")
        
        # Check if the result matches expectations
        if expected_similarity == "low":
            if not verified:
                print(f"    ✅ PASS: Citation correctly NOT verified due to low similarity")
            else:
                print(f"    ❌ FAIL: Citation incorrectly verified despite low similarity")
        else:
            if verified:
                print(f"    ✅ PASS: Citation correctly verified with good similarity")
            else:
                print(f"    ❌ FAIL: Citation incorrectly NOT verified despite good similarity")
        
        print("-" * 60)
    
    print("Test completed!")

if __name__ == "__main__":
    test_case_name_similarity() 
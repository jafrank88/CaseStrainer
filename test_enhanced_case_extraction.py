#!/usr/bin/env python3
"""
Test script to demonstrate enhanced case name extraction capabilities.
This shows how the system can extract case names from both source documents and verification URLs.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_enhanced_case_extraction():
    """Test the enhanced case name extraction capabilities."""
    
    print("Testing Enhanced Case Name Extraction")
    print("=" * 60)
    
    # Initialize the verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Clear cache to ensure fresh verification
    verifier.clear_cache()
    
    # Test cases with known case names from the Washington Supreme Court opinion
    test_cases = [
        {
            "citation": "181 Wash.2d 391",
            "extracted_case_name": "Walston v. Boeing Co.",
            "expected_case_name": "Walston v. Boeing Co."
        },
        {
            "citation": "334 P.3d 519",
            "extracted_case_name": "Walston v. Boeing Co.",
            "expected_case_name": "Walston v. Boeing Co."
        },
        {
            "citation": "127 Wn.2d 853",
            "extracted_case_name": "Birklid v. Boeing Co.",
            "expected_case_name": "Birklid v. Boeing Co."
        },
        {
            "citation": "170 Wn.2d 854",
            "extracted_case_name": "State v. Barber",
            "expected_case_name": "State v. Barber"
        }
    ]
    
    print("\nTesting case name extraction and verification:")
    print("-" * 60)
    
    for test_case in test_cases:
        citation = test_case["citation"]
        extracted_case_name = test_case["extracted_case_name"]
        expected_case_name = test_case["expected_case_name"]
        
        print(f"\nCitation: {citation}")
        print(f"Extracted case name: {extracted_case_name}")
        print(f"Expected case name: {expected_case_name}")
        
        # Verify the citation with the extracted case name
        result = verifier.verify_citation(citation, extracted_case_name=extracted_case_name)
        
        print(f"Verification result:")
        print(f"  Verified: {result.get('verified', False)}")
        print(f"  Source case name: {result.get('case_name', 'N/A')}")
        print(f"  URL: {result.get('url', 'N/A')}")
        print(f"  Similarity: {result.get('case_name_similarity', 'N/A')}")
        print(f"  Case name mismatch: {result.get('case_name_mismatch', 'N/A')}")
        
        if result.get('note'):
            print(f"  Note: {result.get('note')}")
        
        # Test URL-based case name extraction if a URL is found
        if result.get('url'):
            print(f"\n  Testing URL-based case name extraction...")
            extracted_from_url = verifier._extract_case_name_from_url_content(result['url'], citation)
            if extracted_from_url:
                print(f"  Case name extracted from URL: {extracted_from_url}")
                
                # Compare with the extracted case name
                similarity = verifier._calculate_case_name_similarity(extracted_case_name, extracted_from_url)
                print(f"  Similarity with extracted name: {similarity:.2f}")
            else:
                print(f"  No case name could be extracted from URL")
        
        print("-" * 40)

def test_site_specific_extraction():
    """Test site-specific case name extraction patterns."""
    
    print("\n\nTesting Site-Specific Case Name Extraction")
    print("=" * 60)
    
    verifier = EnhancedMultiSourceVerifier()
    
    # Test URLs for different legal sites
    test_urls = [
        {
            "url": "https://www.courtlistener.com/opinion/12345/smith-v-jones/",
            "citation": "123 U.S. 456",
            "description": "CourtListener URL"
        },
        {
            "url": "https://www.justia.com/cases/federal/appellate-courts/ca9/12-34567/smith-v-jones/",
            "citation": "123 F.3d 456",
            "description": "Justia URL"
        },
        {
            "url": "https://caselaw.findlaw.com/us-supreme-court/123/456.html",
            "citation": "123 U.S. 456",
            "description": "FindLaw URL"
        }
    ]
    
    for test_url in test_urls:
        url = test_url["url"]
        citation = test_url["citation"]
        description = test_url["description"]
        
        print(f"\n{description}:")
        print(f"URL: {url}")
        print(f"Citation: {citation}")
        
        # Test site identification
        site_type = verifier._identify_site_type(url)
        print(f"Identified site type: {site_type}")
        
        # Test case name extraction (this would normally fetch the page)
        print(f"Note: Would extract case name using {site_type}-specific patterns")

def test_case_name_validation():
    """Test case name validation and cleaning."""
    
    print("\n\nTesting Case Name Validation and Cleaning")
    print("=" * 60)
    
    verifier = EnhancedMultiSourceVerifier()
    
    test_case_names = [
        "Walston v. Boeing Co.",
        "Smith v. Jones",
        "In re Smith",
        "State ex rel. Smith v. Jones",
        "Unknown Case",
        "Found in State Courts",
        "Some random text that's not a case name",
        "123 U.S. 456 - Smith v. Jones",
        "Smith v. Jones, 123 U.S. 456"
    ]
    
    for case_name in test_case_names:
        is_valid = verifier._is_valid_case_name(case_name)
        cleaned = verifier._clean_case_name(case_name)
        
        print(f"\nCase name: {case_name}")
        print(f"  Valid: {is_valid}")
        print(f"  Cleaned: {cleaned}")

if __name__ == "__main__":
    print("Enhanced Case Name Extraction Test Suite")
    print("=" * 80)
    
    try:
        test_enhanced_case_extraction()
        test_site_specific_extraction()
        test_case_name_validation()
        
        print("\n" + "=" * 80)
        print("Test completed successfully!")
        print("\nKey Features Demonstrated:")
        print("1. Case name extraction from source documents")
        print("2. Case name extraction from verification URLs")
        print("3. Site-specific extraction patterns for major legal websites")
        print("4. Case name validation and cleaning")
        print("5. Similarity comparison between extracted and source case names")
        print("6. Always including URLs when found, regardless of verification status")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc() 
#!/usr/bin/env python3
"""
Test script to verify case name extraction fixes for header contamination.
Tests the enhanced document primary case name detection and header filtering.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.unified_clustering_master import UnifiedClusteringMaster
from src.unified_case_extraction_master import extract_case_name_and_date_unified_master

def test_document_primary_case_extraction():
    """Test that document primary case names are correctly detected."""
    print("\n=== Testing Document Primary Case Name Extraction ===\n")
    
    # Test case 1: Carter v. Jones format
    text1 = """CARTER, Respondent, v. MARY E. JONES, Appellant
No. 103135-1
SUPREME COURT OF THE STATE OF WASHINGTON
FILED: January 15, 2025

This case involves important legal questions about...
"""
    
    clustering_master = UnifiedClusteringMaster()
    primary_case1 = clustering_master._extract_document_primary_case_name(text1)
    print(f"Test 1 - Carter format:")
    print(f"  Input: 'CARTER, Respondent, v. MARY E. JONES, Appellant'")
    print(f"  Extracted: '{primary_case1}'")
    print(f"  Expected: 'CARTER v. MARY E. JONES'")
    print(f"  Result: {'✅ PASS' if primary_case1 == 'CARTER v. MARY E. JONES' else '❌ FAIL'}\n")
    
    # Test case 2: Standard format
    text2 = """Smith v. Johnson
No. 123-456
SUPREME COURT

The plaintiff argues that...
"""
    
    primary_case2 = clustering_master._extract_document_primary_case_name(text2)
    print(f"Test 2 - Standard format:")
    print(f"  Input: 'Smith v. Johnson'")
    print(f"  Extracted: '{primary_case2}'")
    print(f"  Expected: 'Smith v. Johnson'")
    print(f"  Result: {'✅ PASS' if primary_case2 == 'Smith v. Johnson' else '❌ FAIL'}\n")

def test_header_filtering():
    """Test that header contamination is properly filtered."""
    print("\n=== Testing Header Contamination Filtering ===\n")
    
    # Create a mock extractor to test the header filter
    from src.unified_case_extraction_master import UnifiedCaseExtractionMaster
    extractor = UnifiedCaseExtractionMaster()
    
    # Test case 1: Case caption header should be filtered
    context1 = """CARTER, Respondent, v. MARY E. JONES, Appellant
SUPREME COURT OF THE STATE OF WASHINGTON
The court considered whether"""
    
    filtered1 = extractor._filter_header_contamination(context1, debug=True)
    print(f"Test 1 - Case caption filtering:")
    print(f"  Input contains: 'CARTER, Respondent, v. MARY E. JONES, Appellant'")
    print(f"  Filtered: {filtered1}")
    print(f"  Result: {'✅ PASS' if 'CARTER' not in filtered1 else '❌ FAIL'}\n")
    
    # Test case 2: Regular case discussion should be kept
    context2 = """In the case of Brown v. Board of Education, the court held that
segregation was unconstitutional. This precedent was cited in"""
    
    filtered2 = extractor._filter_header_contamination(context2, debug=True)
    print(f"Test 2 - Case discussion preservation:")
    print(f"  Input contains: 'Brown v. Board of Education'")
    print(f"  Filtered: {filtered2}")
    print(f"  Result: {'✅ PASS' if 'Brown v. Board of Education' in filtered2 else '❌ FAIL'}\n")

def test_case_name_cleaning():
    """Test that case names are properly cleaned."""
    print("\n=== Testing Case Name Cleaning ===\n")
    
    from src.unified_case_extraction_master import UnifiedCaseExtractionMaster
    extractor = UnifiedCaseExtractionMaster()
    
    # Test case 1: Remove role words
    name1 = "CARTER, Respondent, v. MARY E. JONES, Appellant"
    cleaned1 = extractor._clean_case_name(name1)
    print(f"Test 1 - Role word removal:")
    print(f"  Input: '{name1}'")
    print(f"  Cleaned: '{cleaned1}'")
    print(f"  Expected: 'CARTER v. MARY E. JONES'")
    print(f"  Result: {'✅ PASS' if cleaned1 == 'CARTER v. MARY E. JONES' else '❌ FAIL'}\n")
    
    # Test case 2: Already clean name should remain
    name2 = "Smith v. Johnson"
    cleaned2 = extractor._clean_case_name(name2)
    print(f"Test 2 - Clean name preservation:")
    print(f"  Input: '{name2}'")
    print(f"  Cleaned: '{cleaned2}'")
    print(f"  Expected: 'Smith v. Johnson'")
    print(f"  Result: {'✅ PASS' if cleaned2 == 'Smith v. Johnson' else '❌ FAIL'}\n")

def test_extraction_with_contamination_filter():
    """Test full extraction pipeline with contamination filtering."""
    print("\n=== Testing Full Extraction Pipeline ===\n")
    
    # Document with header contamination
    text = """CARTER, Respondent, v. MARY E. JONES, Appellant
No. 103135-1
SUPREME COURT OF THE STATE OF WASHINGTON

The court's decision in Carter v. Jones established an important precedent.
This was later cited in Smith v. Johnson, 123 F.3d 456 (2020), which held that...
The ruling was also referenced in Davis v. Wilson, 456 U.S. 789 (2021)."""
    
    # Extract case name for a citation
    result = extract_case_name_and_date_unified_master(
        text=text,
        citation="123 F.3d 456",
        start_index=text.find("123 F.3d 456"),
        document_primary_case_name="CARTER v. MARY E. JONES"
    )
    
    print(f"Test - Full pipeline extraction:")
    print(f"  Document primary case: 'CARTER v. MARY E. JONES'")
    print(f"  Citation: '123 F.3d 456'")
    print(f"  Extracted case name: '{result.get('case_name', 'N/A')}'")
    print(f"  Expected: 'Smith v. Johnson' (not contaminated)")
    print(f"  Result: {'✅ PASS' if result.get('case_name') == 'Smith v. Johnson' else '❌ FAIL'}\n")
    
    # Test extraction near header
    result2 = extract_case_name_and_date_unified_master(
        text=text,
        citation="456 U.S. 789",
        start_index=text.find("456 U.S. 789"),
        document_primary_case_name="CARTER v. MARY E. JONES"
    )
    
    print(f"Test - Extraction near header:")
    print(f"  Citation: '456 U.S. 789'")
    print(f"  Extracted case name: '{result2.get('case_name', 'N/A')}'")
    print(f"  Expected: 'Davis v. Wilson' (not contaminated)")
    print(f"  Result: {'✅ PASS' if result2.get('case_name') == 'Davis v. Wilson' else '❌ FAIL'}\n")

if __name__ == "__main__":
    print("=" * 60)
    print("CASE NAME EXTRACTION FIXES TEST SUITE")
    print("=" * 60)
    
    test_document_primary_case_extraction()
    test_header_filtering()
    test_case_name_cleaning()
    test_extraction_with_contamination_filter()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("\nThese tests verify that:")
    print("1. Document primary case names are correctly detected")
    print("2. Header contamination is properly filtered")
    print("3. Case names are cleaned of role words")
    print("4. Extraction avoids picking up document headers")
    print("\nFixes implemented:")
    print("- Enhanced _extract_document_primary_case_name() to handle role words")
    print("- Improved _filter_header_contamination() to detect case captions")
    print("- Enhanced _clean_case_name() to remove role patterns")
    print("- Better contamination detection throughout pipeline")

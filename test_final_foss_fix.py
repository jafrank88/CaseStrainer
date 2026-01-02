#!/usr/bin/env python3
"""
Final test: Confirm the complete Foss case fix is working
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
from src.unified_verification_master import UnifiedVerificationMaster

def test_complete_foss_fix():
    """Test the complete fix for Foss case verification"""
    
    print("🎯 TESTING COMPLETE FOSS CASE FIX")
    print("=" * 60)
    
    foss_citation = "161 F.3d 584"
    
    # Test 1: Case name extraction (should now use fallback)
    print("\n📋 Test 1: Case name extraction with fallback")
    extraction_result = extract_case_name_and_date_unified_master(
        text="",  # No context to trigger fallback
        citation=foss_citation,
        debug=False
    )
    
    extracted_name = extraction_result.get('case_name', 'N/A')
    print(f"  Extracted case name: {extracted_name}")
    print(f"  Method: {extraction_result.get('method', 'unknown')}")
    
    # Test 2: Verification (should now succeed)
    print(f"\n📋 Test 2: Citation verification")
    verifier = UnifiedVerificationMaster()
    
    verification_result = verifier.verify_citation_sync(
        foss_citation,
        extracted_name,  # Use the extracted fallback name
        None
    )
    
    print(f"  Verified: {verification_result.verified}")
    print(f"  Source: {verification_result.source}")
    print(f"  Canonical name: {verification_result.canonical_name}")
    print(f"  Confidence: {verification_result.confidence:.2f}")
    
    # Test 3: Simulate the pipeline fix
    print(f"\n📋 Test 3: Pipeline fix simulation")
    
    # Create mock citation object
    class MockCitation:
        def __init__(self, citation):
            self.citation = citation
            self.extracted_case_name = "N/A"  # Start with N/A (extraction failed)
            self.verified = False
            self.canonical_name = None
            self.source = None
    
    mock_citation = MockCitation(foss_citation)
    print(f"  Initial state:")
    print(f"    extracted_case_name: {mock_citation.extracted_case_name}")
    print(f"    verified: {mock_citation.verified}")
    
    # Apply the fix: Use fallback name, then verify
    if extracted_name != 'N/A':
        mock_citation.extracted_case_name = extracted_name
        print(f"  ✅ Updated with fallback name: {extracted_name}")
    
    # If verification succeeds, update with canonical name
    if verification_result.verified and verification_result.canonical_name:
        mock_citation.extracted_case_name = verification_result.canonical_name
        mock_citation.verified = True
        mock_citation.canonical_name = verification_result.canonical_name
        mock_citation.source = verification_result.source
        print(f"  ✅ Updated with verified canonical name: {verification_result.canonical_name}")
    
    print(f"  Final state:")
    print(f"    extracted_case_name: {mock_citation.extracted_case_name}")
    print(f"    verified: {mock_citation.verified}")
    print(f"    canonical_name: {mock_citation.canonical_name}")
    print(f"    source: {mock_citation.source}")
    
    # Test 4: Frontend display simulation
    print(f"\n📋 Test 4: Frontend display simulation")
    
    frontend_display = {
        'citation': mock_citation.citation,
        'case_name': mock_citation.extracted_case_name,
        'verified': mock_citation.verified,
        'source': mock_citation.source,
        'status': 'verified' if mock_citation.verified else 'unverified'
    }
    
    print(f"  Frontend will display:")
    print(f"    Citation: {frontend_display['citation']}")
    print(f"    Case name: {frontend_display['case_name']}")
    print(f"    Status: {frontend_display['status']}")
    print(f"    Source: {frontend_display['source']}")
    
    # Test 5: Final success determination
    print(f"\n📋 Test 5: Success determination")
    
    success_criteria = {
        'extraction_not_na': frontend_display['case_name'] != 'N/A',
        'verification_succeeded': frontend_display['verified'],
        'contains_foss': 'FOSS' in frontend_display['case_name'].upper(),
        'has_source': frontend_display['source'] is not None
    }
    
    print(f"  Success criteria:")
    for criterion, passed in success_criteria.items():
        status = "✅" if passed else "❌"
        print(f"    {status} {criterion}: {passed}")
    
    overall_success = all(success_criteria.values())
    print(f"\n  🎯 OVERALL RESULT: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
    
    if overall_success:
        print(f"\n🎉 THE FOSS CASE FIX IS WORKING!")
        print(f"   • No more 'N/A' displays")
        print(f"   • Shows verified status")
        print(f"   • Displays correct case name")
        print(f"   • Uses proper verification source")
    else:
        print(f"\n❌ The fix still needs work")
        failed_criteria = [c for c, p in success_criteria.items() if not p]
        print(f"   Failed criteria: {', '.join(failed_criteria)}")
    
    return overall_success

if __name__ == "__main__":
    success = test_complete_foss_fix()
    sys.exit(0 if success else 1)

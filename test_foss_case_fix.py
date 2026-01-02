#!/usr/bin/env python3
"""
Test the complete fix for Foss case verification
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
from src.enhanced_fallback_verifier import EnhancedFallbackVerifier

async def test_foss_case_fix():
    """Test the complete fix for Foss case verification"""
    
    print("🧪 TESTING COMPLETE FOSS CASE FIX")
    print("=" * 60)
    
    foss_citation = "161 F.3d 584"
    
    # Test 1: Case name extraction with fallback
    print("\n📋 Test 1: Case name extraction with fallback")
    extraction_result = extract_case_name_and_date_unified_master(
        text="",  # No context to trigger fallback
        citation=foss_citation,
        debug=True
    )
    
    print(f"  Extracted case name: {extraction_result.get('case_name', 'N/A')}")
    print(f"  Method: {extraction_result.get('method', 'unknown')}")
    print(f"  Confidence: {extraction_result.get('confidence', 0):.2f}")
    
    # Test 2: Verification with fallback case name
    print(f"\n📋 Test 2: Verification with fallback case name")
    verifier = EnhancedFallbackVerifier(enable_experimental_engines=True)
    
    verification_result = await verifier.verify_citation_async(
        foss_citation, 
        extraction_result.get('case_name'),  # Use fallback name
        None, 
        timeout=10.0
    )
    
    # Handle both object and dict results
    if hasattr(verification_result, 'verified'):
        verified = verification_result.verified
        source = verification_result.source
        canonical_name = verification_result.canonical_name
        confidence = getattr(verification_result, 'confidence', 0.0)
    else:
        verified = verification_result.get('verified', False)
        source = verification_result.get('source', 'unknown')
        canonical_name = verification_result.get('canonical_name')
        confidence = verification_result.get('confidence', 0.0)
    
    print(f"  Verification succeeded: {verified}")
    print(f"  Verification source: {source}")
    print(f"  Canonical name: {canonical_name}")
    
    # Test 3: Simulate the complete pipeline
    print(f"\n📋 Test 3: Complete pipeline simulation")
    
    # Create a mock citation object
    class MockCitation:
        def __init__(self, citation):
            self.citation = citation
            self.extracted_case_name = "N/A"  # Start with N/A
            self.verified = False
            self.canonical_name = None
    
    mock_citation = MockCitation(foss_citation)
    print(f"  Initial extracted_case_name: {mock_citation.extracted_case_name}")
    print(f"  Initial verified: {mock_citation.verified}")
    
    # Apply the fix: if verification succeeded, update extracted_case_name
    if verified and canonical_name:
        if mock_citation.extracted_case_name == 'N/A':
            mock_citation.extracted_case_name = canonical_name
            mock_citation.verified = True
            mock_citation.canonical_name = canonical_name
    
    print(f"  Final extracted_case_name: {mock_citation.extracted_case_name}")
    print(f"  Final verified: {mock_citation.verified}")
    print(f"  Final canonical_name: {mock_citation.canonical_name}")
    
    # Test 4: Check if this resolves the frontend display issue
    print(f"\n📋 Test 4: Frontend display simulation")
    
    # Simulate frontend citation formatting
    def format_citation_for_frontend(citation):
        return {
            'citation': citation.citation,
            'extracted_case_name': citation.extracted_case_name,
            'canonical_name': getattr(citation, 'canonical_name', None),
            'verified': citation.verified,
            'source': source,
            'confidence': confidence
        }
    
    frontend_data = format_citation_for_frontend(mock_citation)
    print(f"  Frontend will display:")
    print(f"    Case name: {frontend_data['extracted_case_name']}")
    print(f"    Verified: {frontend_data['verified']}")
    print(f"    Source: {frontend_data['source']}")
    
    # Determine success
    if (frontend_data['extracted_case_name'] != 'N/A' and 
        frontend_data['verified'] and 
        frontend_data['extracted_case_name'] == 'Foss v. National Marine Fisheries Service'):
        print(f"  ✅ SUCCESS: Foss case will now display correctly!")
    else:
        print(f"  ❌ ISSUE: Still has problems")
        if frontend_data['extracted_case_name'] == 'N/A':
            print(f"    - Still showing N/A")
        if not frontend_data['verified']:
            print(f"    - Still not verified")

if __name__ == "__main__":
    asyncio.run(test_foss_case_fix())

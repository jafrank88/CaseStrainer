#!/usr/bin/env python3
"""
Test VLex verification functionality
"""

import asyncio
from src.unified_verification_master import UnifiedVerificationMaster

async def test_vlex_verification():
    """Test VLex verification with the specific citation"""
    
    # Create verifier
    verifier = UnifiedVerificationMaster()
    
    # Test citations
    test_citations = [
        "146 F.4th 165",  # The user's example
        "123 F.3d 456",  # Another test case
        "987 F.2d 321",  # Another test case
    ]
    
    print("=" * 80)
    print("TESTING VLEX VERIFICATION")
    print("=" * 80)
    print()
    
    for citation in test_citations:
        print(f"Testing citation: {citation}")
        print("-" * 40)
        
        # Test with VLex directly
        result = await verifier._verify_with_vlex(
            citation=citation,
            extracted_case_name=None,
            extracted_date=None,
            timeout=10.0
        )
        
        print(f"Verified: {result.verified}")
        print(f"Canonical Name: {result.canonical_name}")
        print(f"Canonical Date: {result.canonical_date}")
        print(f"URL: {result.canonical_url}")
        print(f"Source: {result.source}")
        print(f"Error: {result.error}")
        print()
    
    # Test the full verification pipeline with VLex enabled
    print("=" * 80)
    print("TESTING FULL VERIFICATION PIPELINE (WITH VLEX)")
    print("=" * 80)
    print()
    
    for citation in test_citations[:1]:  # Just test the first one
        print(f"Testing {citation} through full pipeline...")
        
        result = await verifier.verify_citation(
            citation=citation,
            extracted_case_name=None,
            extracted_date=None,
            timeout=30.0
        )
        
        print(f"Verified: {result.get('verified', False)}")
        print(f"Canonical Name: {result.get('canonical_name')}")
        print(f"Canonical Date: {result.get('canonical_date')}")
        print(f"URL: {result.get('canonical_url')}")
        print(f"Source: {result.get('source')}")
        print()

if __name__ == "__main__":
    asyncio.run(test_vlex_verification())

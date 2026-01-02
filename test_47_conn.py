#!/usr/bin/env python3
"""Debug script to trace 47 Conn. Supp. 113 through batch verification."""
import asyncio
import os

# Set up the path
import sys
sys.path.insert(0, '/app')

from src.unified_verification_master import UnifiedVerificationMaster

async def test_batch():
    verifier = UnifiedVerificationMaster()
    
    # Test the exact citations from Meri-Weather cluster
    citations = ['47 Conn. Supp. 113', '778 A.2d 1006', '63 Conn. App. 695']
    case_names = ['Meri-Weather', 'Meri-Weather', 'Meri-Weather']
    dates = ['2000', '2001', '2001']
    
    print("=" * 60)
    print("Testing batch verification for Meri-Weather citations")
    print("=" * 60)
    
    results = await verifier.verify_citations_batch(
        citations=citations,
        extracted_case_names=case_names,
        extracted_dates=dates
    )
    
    print("\nResults:")
    for i, result in enumerate(results):
        print(f"\n{citations[i]}:")
        print(f"  verified: {result.verified}")
        print(f"  canonical_name: {result.canonical_name}")
        print(f"  canonical_date: {result.canonical_date}")
        print(f"  source: {result.source}")
        print(f"  error: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_batch())

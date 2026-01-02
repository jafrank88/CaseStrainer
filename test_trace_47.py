#!/usr/bin/env python3
"""Trace 47 Conn. Supp. 113 through the full verification flow."""
import sys
sys.path.insert(0, '/app')

import asyncio
from src.unified_verification_master import UnifiedVerificationMaster

async def test():
    verifier = UnifiedVerificationMaster()
    
    # Test with extracted_date=2001 (as in the real pipeline)
    citations = ['47 Conn. Supp. 113']
    case_names = ['Meri-Weather']
    dates = ['2001']  # This is what the pipeline extracts
    
    print("=" * 60)
    print("Testing with extracted_date=2001 (matches real pipeline)")
    print("=" * 60)
    
    results = await verifier.verify_citations_batch(
        citations=citations,
        extracted_case_names=case_names,
        extracted_dates=dates
    )
    
    print("\nResult:")
    for result in results:
        print(f"  verified: {result.verified}")
        print(f"  canonical_name: {result.canonical_name}")
        print(f"  canonical_date: {result.canonical_date}")
        print(f"  source: {result.source}")
        print(f"  error: {result.error}")

if __name__ == "__main__":
    asyncio.run(test())

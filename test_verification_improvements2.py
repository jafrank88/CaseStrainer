#!/usr/bin/env python3
"""
Test the verification improvements:
1. Expanded Justia URL patterns
2. Law Resource.org with F.2d and F.4th support
3. Simple verification cache
"""

import asyncio
from src.unified_verification_master import UnifiedVerificationMaster
from src.verification_cache import get_verification_cache

async def test_improvements():
    """Test the verification improvements"""
    
    print("=" * 80)
    print("TESTING VERIFICATION IMPROVEMENTS")
    print("=" * 80)
    print()
    
    verifier = UnifiedVerificationMaster()
    cache = get_verification_cache()
    
    # Test cases
    test_cases = [
        {
            "citation": "146 F.4th 165",
            "case_name": "Giuffre v. Maxwell",
            "description": "F.4th citation (Justia & Law Resource)"
        },
        {
            "citation": "123 F.2d 456",
            "case_name": None,
            "description": "F.2d citation (Law Resource)"
        },
        {
            "citation": "789 F.3d 123",
            "case_name": None,
            "description": "F.3d citation (Law Resource)"
        },
        {
            "citation": "523 U.S. 751",
            "case_name": None,
            "description": "U.S. citation (Justia)"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'-'*60}")
        print(f"TEST {i}: {test['description']}")
        print(f"Citation: {test['citation']}")
        print(f"{'-'*60}")
        
        # First run (not cached)
        print("\nFirst verification (not cached):")
        result = await verifier.verify_citation(
            citation=test['citation'],
            extracted_case_name=test['case_name'],
            timeout=10.0
        )
        
        print(f"Verified: {result.verified}")
        print(f"Source: {result.source}")
        print(f"URL: {result.canonical_url}")
        print(f"Cached: {getattr(result, 'cached', False)}")
        
        # Second run (should be cached if successful)
        if result.verified:
            print("\nSecond verification (should be cached):")
            result2 = await verifier.verify_citation(
                citation=test['citation'],
                extracted_case_name=test['case_name'],
                timeout=10.0
            )
            
            print(f"Verified: {result2.verified}")
            print(f"Source: {result2.source}")
            print(f"Cached: {getattr(result2, 'cached', False)}")
    
    # Show cache statistics
    print("\n" + "="*80)
    print("CACHE STATISTICS")
    print("="*80)
    stats = cache.get_stats()
    print(f"Total cached entries: {stats['total_entries']}")
    print("\nEntries by source:")
    for source, count in stats['sources'].items():
        print(f"  {source}: {count}")

if __name__ == "__main__":
    asyncio.run(test_improvements())

"""
Test the batch verification method directly
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, 'D:/dev/casestrainer/src')

from unified_verification_master import UnifiedVerificationMaster

print("=" * 80)
print("TESTING BATCH VERIFICATION DIRECTLY")
print("=" * 80)

async def test_batch_verification():
    master = UnifiedVerificationMaster()
    
    # Test the same citations from motion.pdf
    citations = [
        "963 F.3d 130",
        "146 F.3d 1042", 
        "2024 WL 4149252",
        "2024 WL 4003343",
        "346 F.R.D. 102"
    ]
    
    case_names = [None] * len(citations)  # Simulating what happens when extraction fails
    dates = [None] * len(citations)      # Simulating None dates
    
    print("\nTesting batch verification...")
    print(f"Citations: {citations}")
    print(f"Case names: {case_names}")
    print(f"Dates: {dates}")
    
    results = await master.verify_citations_batch(
        citations=citations,
        extracted_case_names=case_names,
        extracted_dates=dates
    )
    
    print(f"\nResults ({len(results)}):")
    print("-" * 40)
    
    for i, result in enumerate(results):
        print(f"\n{i+1}. {result.citation}")
        print(f"   Verified: {result.verified}")
        print(f"   Canonical name: {result.canonical_name}")
        print(f"   Canonical date: {result.canonical_date}")
        print(f"   Source: {result.source}")
        print(f"   Error: {result.error}")
        
        if result.verified:
            print("   ✅ SUCCESS")
        else:
            print("   ❌ FAILED")

# Run the test
try:
    asyncio.run(test_batch_verification())
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("If batch verification works but the API doesn't,")
print("the issue is in how the results are being applied")
print("or how the citations are being processed.")
print("=" * 80)

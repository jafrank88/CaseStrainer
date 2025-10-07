"""
Direct test of the verification system to see what's happening with 521 U.S. 811
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_direct_verification():
    """Test verification directly without the full pipeline."""
    
    print("=" * 80)
    print("DIRECT VERIFICATION TEST: 521 U.S. 811")
    print("=" * 80)
    
    # Test the unified verification master directly
    from src.unified_verification_master import UnifiedVerificationMaster
    
    master = UnifiedVerificationMaster()
    
    print("\n1. Testing single citation verification...")
    result = await master.verify_citation(
        citation="521 U.S. 811",
        extracted_case_name="Branson v. Wash. Fine Wine & Spirits, LLC",  # Wrong extraction
        extracted_date="1997"
    )
    
    print(f"\nResult:")
    print(f"  Citation: {result.citation}")
    print(f"  Verified: {result.verified}")
    print(f"  Canonical Name: {result.canonical_name}")
    print(f"  Canonical Date: {result.canonical_date}")
    print(f"  Canonical URL: {result.canonical_url}")
    print(f"  Source: {result.source}")
    print(f"  Confidence: {result.confidence}")
    print(f"  Method: {result.method}")
    print(f"  Error: {result.error}")
    
    # Check if it's correct
    print("\n" + "=" * 80)
    if result.verified:
        if "Raines" in (result.canonical_name or "") and "Byrd" in (result.canonical_name or ""):
            print("✅ ✅ ✅ SUCCESS! Got 'Raines v. Byrd'")
            print(f"Canonical Name: {result.canonical_name}")
            print(f"Canonical Date: {result.canonical_date}")
        else:
            print(f"❌ WRONG! Got: {result.canonical_name}")
            print(f"Expected: Raines v. Byrd")
    else:
        print(f"❌ NOT VERIFIED! Error: {result.error}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_direct_verification())

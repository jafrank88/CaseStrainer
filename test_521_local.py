"""
Local test that bypasses Docker and tests the fixed code directly
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

async def test_local():
    print("=" * 80)
    print("LOCAL TEST: 521 U.S. 811 with fixed verification")
    print("=" * 80)
    
    # Test verification directly
    from src.unified_verification_master import UnifiedVerificationMaster
    
    master = UnifiedVerificationMaster()
    
    print("\n1. Testing verification for 521 U.S. 811...")
    result = await master.verify_citation(
        citation="521 U.S. 811",
        extracted_case_name="Branson",  # Wrong extraction
        extracted_date="1997"
    )
    
    print(f"\nVerification Result:")
    print(f"  Verified: {result.verified}")
    print(f"  Canonical Name: {result.canonical_name}")
    print(f"  Canonical Date: {result.canonical_date}")
    print(f"  Source: {result.source}")
    
    # Check if correct
    if result.verified and "Raines" in (result.canonical_name or "") and "Byrd" in (result.canonical_name or ""):
        print("\n" + "=" * 80)
        print("SUCCESS! Verification returns correct case name")
        print("=" * 80)
        return True
    else:
        print("\n" + "=" * 80)
        print(f"FAILED! Got: {result.canonical_name}")
        print("Expected: Raines v. Byrd")
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_local())
    sys.exit(0 if success else 1)

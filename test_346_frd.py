"""Test CaseMine verification for 346 F.R.D. 102"""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_verification_master import UnifiedVerificationMaster

async def test_346_frd():
    """Test verification of 346 F.R.D. 102"""
    
    # Create verifier (it will load API key from config)
    verifier = UnifiedVerificationMaster()
    
    # Test citation
    citation = "346 F.R.D. 102"
    extracted_name = "Dakota Hum. Rts. Coal. v. Patriot Front"
    extracted_date = "2024"
    
    print(f"Testing CaseMine verification for: {citation}")
    print(f"Extracted name: {extracted_name}")
    print(f"Extracted date: {extracted_date}")
    print(f"Expected URL: https://www.casemine.com/judgement/us/66e11cf2ab3a454de71ffe6c")
    print()
    
    # Test CaseMine verification
    print("=" * 60)
    print("TESTING CASEMINE VERIFICATION")
    print("=" * 60)
    
    result = await verifier._verify_with_casemine(
        citation=citation,
        extracted_case_name=extracted_name,
        extracted_date=extracted_date,
        timeout=10.0
    )
    
    if result:
        print(f"\nResult:")
        print(f"  Verified: {result.verified}")
        print(f"  Canonical Name: {result.canonical_name}")
        print(f"  Canonical URL: {result.canonical_url}")
        print(f"  Source: {result.source}")
        print(f"  Error: {result.error}")
        
        # Check if URL matches
        if result.canonical_url:
            if '66e11cf2ab3a454de71ffe6c' in result.canonical_url:
                print(f"\n✅ SUCCESS: URL matches expected CaseMine URL!")
            else:
                print(f"\n⚠️  WARNING: URL doesn't match expected CaseMine URL")
                print(f"   Expected: https://www.casemine.com/judgement/us/66e11cf2ab3a454de71ffe6c")
                print(f"   Got: {result.canonical_url}")
    else:
        print(f"\n❌ ERROR: No result returned from CaseMine verification")

if __name__ == "__main__":
    asyncio.run(test_346_frd())

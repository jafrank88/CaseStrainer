"""Test the complete verification flow for 855 F.2d 569"""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_verification_master import UnifiedVerificationMaster

async def test_855_verification():
    """Test verification of 855 F.2d 569"""
    
    # Get API key
    api_key = None
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('COURTLISTENER_API_KEY'):
                api_key = line.split('=')[1].strip()
                break
    
    if not api_key:
        print("No API key found")
        return
    
    # Create verifier
    verifier = UnifiedVerificationMaster(api_key=api_key)
    
    # Test citation
    citation = "855 F.2d 569"
    extracted_name = "In re Search Warrant"
    extracted_date = "1988"
    
    print(f"Testing verification for: {citation}")
    print(f"Extracted name: {extracted_name}")
    print(f"Extracted date: {extracted_date}")
    print()
    
    # Test batch verification (which uses citation-lookup)
    print("=" * 60)
    print("TESTING BATCH VERIFICATION (citation-lookup API)")
    print("=" * 60)
    
    results = await verifier.verify_citations_batch(
        citations=[citation],
        extracted_case_names=[extracted_name],
        extracted_dates=[extracted_date],
        enable_fallback=False  # Disable fallback to see citation-lookup result
    )
    
    if results:
        result = results[0]
        print(f"\nResult:")
        print(f"  Verified: {result.verified}")
        print(f"  Canonical Name: {result.canonical_name}")
        print(f"  Canonical URL: {result.canonical_url}")
        print(f"  Source: {result.source}")
        print(f"  Error: {result.error}")
        
        # Check if URL contains 8971994
        if result.canonical_url:
            if '8971994' in result.canonical_url:
                print(f"\n✅ SUCCESS: URL contains opinion 8971994!")
            elif '511911' in result.canonical_url:
                print(f"\n❌ ERROR: URL contains wrong opinion 511911!")
            else:
                print(f"\n⚠️  WARNING: URL doesn't contain expected opinion IDs")
    
    print("\n" + "=" * 60)
    print("TESTING WITH FALLBACK ENABLED")
    print("=" * 60)
    
    results = await verifier.verify_citations_batch(
        citations=[citation],
        extracted_case_names=[extracted_name],
        extracted_dates=[extracted_date],
        enable_fallback=True  # Enable fallback
    )
    
    if results:
        result = results[0]
        print(f"\nResult:")
        print(f"  Verified: {result.verified}")
        print(f"  Canonical Name: {result.canonical_name}")
        print(f"  Canonical URL: {result.canonical_url}")
        print(f"  Source: {result.source}")
        print(f"  Error: {result.error}")
        
        # Check if URL contains 8971994
        if result.canonical_url:
            if '8971994' in result.canonical_url:
                print(f"\n✅ SUCCESS: URL contains opinion 8971994!")
            elif '511911' in result.canonical_url:
                print(f"\n❌ ERROR: URL contains wrong opinion 511911!")
            else:
                print(f"\n⚠️  WARNING: URL doesn't contain expected opinion IDs")

if __name__ == "__main__":
    asyncio.run(test_855_verification())

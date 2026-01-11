"""
Test U.S. Reports citation verification to debug why Supreme Court cases aren't being verified.
"""
import asyncio
import logging
from src.unified_verification_master import UnifiedVerificationMaster

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_us_reports():
    """Test verification of U.S. Reports citations."""
    
    # Test citations from the user's results
    test_cases = [
        ("606 U.S. 831", "Trump v. CASA, Inc.", "2025"),
        ("385 U.S. 630", "Berenyi v. District Director", "1966"),
        ("600 U.S. 477", "Biden v. Nebraska", "2023"),
        ("442 U.S. 682", "Califano v. Yamasaki", "1979"),
        ("596 U.S. 528", "Kemp v. United States", "2022"),
    ]
    
    verifier = UnifiedVerificationMaster()
    
    print("\n" + "="*80)
    print("TESTING U.S. REPORTS CITATION VERIFICATION")
    print("="*80 + "\n")
    
    for citation, case_name, year in test_cases:
        print(f"\n{'─'*80}")
        print(f"Testing: {citation}")
        print(f"Case: {case_name} ({year})")
        print(f"{'─'*80}")
        
        # Test batch verification (what the system uses)
        print("\n1. BATCH VERIFICATION (CourtListener):")
        batch_results = await verifier._verify_with_courtlistener_lookup_batch(
            [citation], 
            [case_name], 
            [year]
        )
        
        if batch_results and batch_results[0].verified:
            result = batch_results[0]
            print(f"   ✅ VERIFIED")
            print(f"   📝 Name: {result.canonical_name}")
            print(f"   📅 Date: {result.canonical_date}")
            print(f"   🔗 URL: {result.canonical_url}")
            print(f"   📊 Confidence: {result.confidence}")
        else:
            error = batch_results[0].error if batch_results else "No results"
            print(f"   ❌ FAILED: {error}")
        
        # Test Justia direct URL
        print("\n2. JUSTIA DIRECT URL:")
        justia_result = await verifier._verify_with_justia(citation, case_name, year, 10.0)
        
        if justia_result.verified:
            print(f"   ✅ VERIFIED")
            print(f"   📝 Name: {justia_result.canonical_name}")
            print(f"   🔗 URL: {justia_result.canonical_url}")
        else:
            print(f"   ❌ FAILED: {justia_result.error}")
        
        # Test if citation passes validation
        print("\n3. CITATION VALIDATION:")
        from src.unified_verification_master import is_valid_citation
        is_valid = is_valid_citation(citation)
        print(f"   Valid: {is_valid}")
        
        # Test Justia URL builder
        print("\n4. JUSTIA URL BUILDER:")
        url = verifier._build_justia_url(citation)
        print(f"   URL: {url if url else 'None (pattern not matched)'}")

if __name__ == "__main__":
    asyncio.run(test_us_reports())

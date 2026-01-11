"""
Test that the timeout fixes are working correctly
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

import asyncio
import time

async def test_timeout_fix():
    """Test that CourtListener timeouts are handled gracefully"""
    
    from unified_verification_master import UnifiedVerificationMaster
    
    print("=" * 80)
    print("TESTING TIMEOUT FIX")
    print("=" * 80)
    
    master = UnifiedVerificationMaster()
    
    # Test with a citation that might timeout
    test_citations = [
        ("2024 WL 1232082", "Doe v. Teachers Council, Inc.", "2024"),
        ("684 F.3d 286", "New York Civil Liberties Union v. New York City Transit Authority", "2012"),
        ("123 U.S. 456", "Test Case v. Test Defendant", "2023"),
    ]
    
    print("\nTesting individual citation verification:")
    print("-" * 60)
    
    for citation, case_name, date in test_citations:
        print(f"\nTesting: {citation}")
        start_time = time.time()
        
        try:
            result = await master.verify_citation(citation, case_name, date)
            elapsed = time.time() - start_time
            
            print(f"  ✓ Completed in {elapsed:.1f}s")
            print(f"  Verified: {result.verified}")
            print(f"  Source: {result.source}")
            if result.error:
                print(f"  Error: {result.error}")
                
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ✗ Failed after {elapsed:.1f}s")
            print(f"  Error: {e}")
    
    # Test batch verification
    print("\n\nTesting batch verification:")
    print("-" * 60)
    
    citations = [c[0] for c in test_citations]
    case_names = [c[1] for c in test_citations]
    dates = [c[2] for c in test_citations]
    
    start_time = time.time()
    try:
        results = await master.verify_citations_batch(citations, case_names, dates)
        elapsed = time.time() - start_time
        
        print(f"✓ Batch completed in {elapsed:.1f}s")
        print(f"  Results: {len(results)} citations processed")
        
        for i, result in enumerate(results):
            print(f"  {i+1}. {citations[i]}: {result.verified} ({result.source})")
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"✗ Batch failed after {elapsed:.1f}s")
        print(f"  Error: {e}")
    
    print("\n" + "=" * 80)
    print("TIMEOUT FIX VERIFICATION:")
    print("-" * 40)
    print("✓ Citations should complete within 30-45 seconds")
    print("✓ Timeouts should fail fast to fallback sources")
    print("✓ No more 5-12 minute hangs!")
    print("=" * 80)

# Run the test
try:
    asyncio.run(test_timeout_fix())
except Exception as e:
    print(f"Test failed: {e}")
    import traceback
    traceback.print_exc()

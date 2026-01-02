#!/usr/bin/env python3
"""
Test parallel citation verification
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

async def test_parallel_verification():
    """Test parallel citation verification logic"""
    
    # Test text with parallel citations like the user's example
    test_text = """
    In the case of Gresser v. Banner Health, the court considered several issues.
    See Gresser v. Banner Health, 2023 COA 108 and 543 P.3d 1059 for the full opinion.
    The Colorado Court of Appeals addressed medical malpractice claims in 2023 COA 108.
    """
    
    print(f"Testing parallel citation verification...")
    print(f"Test text contains: 2023 COA 108 and 543 P.3d 1059")
    
    processor = UnifiedCitationProcessorV2()
    
    print("🔥🔥🔥 About to call processor.process_text()...")
    
    try:
        result = await processor.process_text(test_text)
        print("🔥🔥🔥 processor.process_text() completed")
        citations = result.get('citations', [])
        
        print(f"\n✅ Found {len(citations)} citations:")
        
        for i, cit in enumerate(citations):
            citation_text = cit.citation
            verified = cit.verified
            true_by_parallel = getattr(cit, 'true_by_parallel', False)
            canonical_name = getattr(cit, 'canonical_name', 'N/A')
            
            print(f"\n{i+1}. Citation: {citation_text}")
            print(f"   Verified: {verified}")
            print(f"   True by parallel: {true_by_parallel}")
            print(f"   Canonical name: {canonical_name}")
            
            # Check if it has parallel citations
            parallels = getattr(cit, 'parallel_citations', [])
            if parallels:
                print(f"   Parallel citations: {parallels}")
        
        # Check if parallel verification is working
        parallel_verified = [cit for cit in citations if getattr(cit, 'true_by_parallel', False)]
        directly_verified = [cit for cit in citations if cit.verified == True]
        
        print(f"\n📊 Verification Summary:")
        print(f"   Directly verified: {len(directly_verified)}")
        print(f"   Verified by parallel: {len(parallel_verified)}")
        print(f"   Total verified: {len(directly_verified) + len(parallel_verified)}")
        
        if len(parallel_verified) > 0:
            print(f"\n✅ Parallel verification is working!")
        else:
            print(f"\n❌ Parallel verification may not be working correctly.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_parallel_verification())

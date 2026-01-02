#!/usr/bin/env python3
"""
Test parallel citation verification by calling propagate_canonical_to_cluster directly
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.models import CitationResult

def test_parallel_direct():
    """Test parallel citation verification by calling the function directly"""
    
    print("Testing parallel verification by calling propagate_canonical_to_cluster directly...")
    
    # Create test citations with position data
    citation1 = CitationResult(
        citation="2023 COA 108",
        start_index=26,
        end_index=38,
        extracted_case_name="Gresser v. Banner Health",
        extracted_date="2023",
        method="clean_pipeline_v1",
        confidence=0.9,
        verified=True,
        canonical_name="Chance Gresser, individually and as parent, natural guardian, next of friend and on behalf of his daughter, C.G., and Erin Gresser, individually and as parent, natural guardian, next of friend and on behalf of her daughter, C.G. v. Banner Health, d/b/a North Colorado Medical Center",
        canonical_date="2023-11-16"
    )
    
    citation2 = CitationResult(
        citation="543 P.3d 1059",
        start_index=40,
        end_index=53,
        extracted_case_name="Gresser v. Banner Health",
        extracted_date="2023",
        method="clean_pipeline_v1",
        confidence=0.9,
        verified=False,
        canonical_name="Chance Gresser, individually and as parent, natural guardian, next of friend and on behalf of his daughter, C.G., and Erin Gresser, individually and as parent, natural guardian, next of friend and on behalf of her daughter, C.G. v. Banner Health, d/b/a North Colorado Medical Center",
        canonical_date="2023-11-16"
    )
    
    citations = [citation1, citation2]
    
    print(f"Created {len(citations)} test citations:")
    for i, cit in enumerate(citations):
        print(f"  {i+1}. {cit.citation}: verified={cit.verified}, true_by_parallel={getattr(cit, 'true_by_parallel', False)}")
    
    processor = UnifiedCitationProcessorV2()
    
    print("🔥🔥🔥 About to call propagate_canonical_to_cluster directly...")
    
    try:
        processor.propagate_canonical_to_cluster(citations)
        print("🔥🔥🔥 propagate_canonical_to_cluster completed")
        
        print(f"\nAfter parallel verification:")
        for i, cit in enumerate(citations):
            print(f"  {i+1}. {cit.citation}: verified={cit.verified}, true_by_parallel={getattr(cit, 'true_by_parallel', False)}")
        
        # Check if parallel verification worked
        parallel_count = sum(1 for c in citations if getattr(c, 'true_by_parallel', False))
        print(f"\n📊 Parallel verification summary:")
        print(f"   Directly verified: {sum(1 for c in citations if c.verified == True)}")
        print(f"   Verified by parallel: {parallel_count}")
        print(f"   Total verified: {sum(1 for c in citations if c.verified == True) + parallel_count}")
        
        if parallel_count > 0:
            print("✅ Parallel verification is working!")
        else:
            print("❌ Parallel verification is not working.")
            
    except Exception as e:
        print(f"❌ Error calling propagate_canonical_to_cluster: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parallel_direct()

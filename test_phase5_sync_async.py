"""
Phase 5: Sync vs Async Consistency Test

Verifies that the clustering fix works correctly in both processing paths.
"""

import sys
sys.path.insert(0, '/app')

import asyncio
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.unified_input_processor import UnifiedInputProcessor

# Real Quinault text
quinault_text = """
The court further noted that Washington courts had similarly upheld a superior 
court's assertion of in rem jurisdiction over tribally owned land in Anderson & 
Middleton Lumber Co. v. Quinault Indian Nation, 130 Wn.2d 862, 929 P.2d 379 (1996), 
and Smale v. Noretep, 150 Wn. App. 476, 208 P.3d 1180 (2009).
"""

async def test_async_path():
    """Test via async path (UnifiedCitationProcessorV2)"""
    print("\n" + "="*80)
    print("ASYNC PATH TEST")
    print("="*80)
    
    processor = UnifiedCitationProcessorV2()
    result = await processor.process_text(text=quinault_text)
    
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"Citations: {len(citations)}, Clusters: {len(clusters)}")
    
    # Check Quinault clustering
    quinault_130 = None
    quinault_929 = None
    
    for cit in citations:
        if '130 Wn.2d 862' in cit.citation:
            quinault_130 = cit
        elif '929 P.2d 379' in cit.citation:
            quinault_929 = cit
    
    if quinault_130 and quinault_929:
        same_cluster = quinault_130.cluster_id == quinault_929.cluster_id
        print(f"  Quinault 130 Wn.2d: {quinault_130.cluster_id}")
        print(f"  Quinault 929 P.2d: {quinault_929.cluster_id}")
        print(f"  {'✅ PASS' if same_cluster else '❌ FAIL'}: Quinault citations {'SAME' if same_cluster else 'DIFFERENT'} cluster")
        return same_cluster
    
    print("  ❌ Could not find Quinault citations")
    return False

def test_sync_path():
    """Test via sync path (UnifiedInputProcessor)"""
    print("\n" + "="*80)
    print("SYNC PATH TEST")
    print("="*80)
    
    processor = UnifiedInputProcessor()
    result = processor.process_text_sync(quinault_text)
    
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"Citations: {len(citations)}, Clusters: {len(clusters)}")
    
    # Check Quinault clustering
    quinault_130 = None
    quinault_929 = None
    
    for cit in citations:
        citation_text = cit.get('citation', '') if isinstance(cit, dict) else getattr(cit, 'citation', '')
        if '130 Wn.2d 862' in citation_text:
            quinault_130 = cit
        elif '929 P.2d 379' in citation_text:
            quinault_929 = cit
    
    if quinault_130 and quinault_929:
        cluster_130 = quinault_130.get('cluster_id') if isinstance(quinault_130, dict) else getattr(quinault_130, 'cluster_id', None)
        cluster_929 = quinault_929.get('cluster_id') if isinstance(quinault_929, dict) else getattr(quinault_929, 'cluster_id', None)
        
        same_cluster = cluster_130 == cluster_929
        print(f"  Quinault 130 Wn.2d: {cluster_130}")
        print(f"  Quinault 929 P.2d: {cluster_929}")
        print(f"  {'✅ PASS' if same_cluster else '❌ FAIL'}: Quinault citations {'SAME' if same_cluster else 'DIFFERENT'} cluster")
        return same_cluster
    
    print("  ❌ Could not find Quinault citations")
    return False

async def main():
    print("\n" + "="*80)
    print("PHASE 5: SYNC VS ASYNC CONSISTENCY TEST")
    print("="*80)
    
    # Test async path
    async_pass = await test_async_path()
    
    # Test sync path
    sync_pass = test_sync_path()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Async Path: {'✅ PASS' if async_pass else '❌ FAIL'}")
    print(f"Sync Path:  {'✅ PASS' if sync_pass else '❌ FAIL'}")
    
    if async_pass and sync_pass:
        print("\n✅ PHASE 5 WORKS IN BOTH SYNC AND ASYNC!")
        return 0
    else:
        print("\n❌ PHASE 5 INCONSISTENT BETWEEN PATHS")
        return 1

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))

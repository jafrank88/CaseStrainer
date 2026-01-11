"""
Test the specific motion.pdf clustering issue
"""

import sys
import asyncio
sys.path.insert(0, 'D:/dev/casestrainer/src')

from unified_citation_processor_v2 import UnifiedCitationProcessorV2

print("=" * 80)
print("TESTING MOTION.PDF CLUSTERING ISSUE")
print("=" * 80)

async def test_motion_issue():
    processor = UnifiedCitationProcessorV2()
    
    # Test the exact text from motion.pdf that had the issue
    test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."
    
    print(f"\nTest text: {test_text}")
    
    print("\nProcessing...")
    result = await processor.process_text(test_text)
    
    print(f"\nResults:")
    print(f"  Citations found: {len(result.get('citations', []))}")
    print(f"  Clusters created: {len(result.get('clusters', []))}")
    
    # Check citations
    citations = result.get('citations', [])
    print("\nCitations:")
    for i, cit in enumerate(citations):
        print(f"\n{i+1}. {cit.get('citation')}")
        print(f"   Case name: {cit.get('case_name', 'N/A')}")
        print(f"   Verified: {cit.get('verified', False)}")
        if cit.get('error'):
            print(f"   Error: {cit.get('error')}")
    
    # Check clusters
    clusters = result.get('clusters', [])
    print("\n\nClusters:")
    for i, cluster in enumerate(clusters):
        cluster_cits = cluster.get('citations', [])
        print(f"\nCluster {i+1}:")
        for cit in cluster_cits:
            print(f"  - {cit.get('citation')} ({cit.get('case_name', 'N/A')})")
    
    # Verify the fix
    print("\n" + "=" * 80)
    print("VERIFICATION:")
    print("-" * 40)
    
    # Check that we have 2 separate clusters (correct)
    if len(clusters) == 2:
        print("✅ CORRECT: Citations are in separate clusters")
        
        # Check that WL citation has proprietary format message
        wl_found = False
        for cit in citations:
            if 'WL' in cit.get('citation', ''):
                wl_found = True
                if cit.get('error') and 'proprietary' in cit.get('error', '').lower():
                    print("✅ CORRECT: WL citation shows proprietary format message")
                else:
                    print("❌ ERROR: WL citation missing proprietary format message")
        
        if not wl_found:
            print("⚠️  WARNING: No WL citation found")
            
    else:
        print(f"❌ ERROR: Expected 2 clusters, found {len(clusters)}")
        if len(clusters) == 1:
            print("   The citations are incorrectly clustered together!")
    
    print("=" * 80)

# Run the test
try:
    asyncio.run(test_motion_issue())
except Exception as e:
    print(f"Test failed: {e}")
    import traceback
    traceback.print_exc()

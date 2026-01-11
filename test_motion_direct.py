"""
Test the fixes by directly processing motion.pdf
"""

import sys
import asyncio
sys.path.insert(0, 'D:/dev/casestrainer/src')

from unified_citation_processor_v2 import UnifiedCitationProcessorV2

print("=" * 80)
print("TESTING MOTION.PDF WITH FIXES")
print("=" * 80)

async def test_motion_pdf():
    processor = UnifiedCitationProcessorV2()
    
    # Test motion.pdf directly
    pdf_path = "D:/dev/casestrainer/motion.pdf"
    
    print("\n1. Processing motion.pdf...")
    print("-" * 60)
    
    try:
        result = await processor.process_file(pdf_path)
        
        print(f"✅ Processing completed")
        print(f"   Citations found: {len(result.get('citations', []))}")
        print(f"   Clusters created: {len(result.get('clusters', []))}")
        
        # Check for WL citations
        print("\n2. Checking WL citations...")
        print("-" * 60)
        
        wl_citations = []
        for citation in result.get('citations', []):
            if 'WL' in citation.get('citation', ''):
                wl_citations.append(citation)
        
        print(f"Found {len(wl_citations)} WL citations:")
        for i, cit in enumerate(wl_citations[:5]):  # Show first 5
            print(f"\n{i+1}. {cit.get('citation')}")
            print(f"   Case name: {cit.get('case_name', 'N/A')}")
            print(f"   Verified: {cit.get('verified', False)}")
            print(f"   Error: {cit.get('error', 'None')}")
            
            # Check for proprietary format message
            error = cit.get('error', '').lower()
            if 'proprietary' in error:
                print(f"   ✅ Shows 'proprietary format' message")
            else:
                print(f"   ❌ Missing 'proprietary format' message")
        
        # Check for clustering issues
        print("\n\n3. Checking clustering...")
        print("-" * 60)
        
        clusters = result.get('clusters', [])
        problem_clusters = []
        
        for cluster in clusters:
            cluster_citations = cluster.get('citations', [])
            if len(cluster_citations) > 1:
                # Check if this cluster has mixed citation types
                has_wl = any('WL' in cit.get('citation', '') for cit in cluster_citations)
                has_reporter = any(any(rep in cit.get('citation', '') for rep in ['F.2d', 'F.3d', 'U.S.', 'S. Ct.']) for cit in cluster_citations)
                
                if has_wl and has_reporter:
                    problem_clusters.append(cluster)
                    print(f"\n⚠️  PROBLEMATIC CLUSTER FOUND:")
                    print(f"   Cluster ID: {cluster.get('cluster_id')}")
                    for cit in cluster_citations:
                        print(f"   - {cit.get('citation')} ({cit.get('case_name', 'N/A')})")
        
        if not problem_clusters:
            print("✅ No problematic clusters found")
            print("   WL and reporter citations are correctly separated")
        
        # Check specific citations mentioned by user
        print("\n\n4. Checking specific citations...")
        print("-" * 60)
        
        target_citations = ['2022 WL 15153410', '855 F.2d 569']
        found_clusters = {}
        
        for cluster in clusters:
            for cit in cluster.get('citations', []):
                cit_text = cit.get('citation', '')
                for target in target_citations:
                    if target in cit_text:
                        found_clusters[target] = cluster.get('cluster_id')
                        print(f"\n{target}:")
                        print(f"   Cluster: {cluster.get('cluster_id')}")
                        print(f"   Case name: {cit.get('case_name', 'N/A')}")
                        print(f"   Verified: {cit.get('verified', False)}")
        
        # Check if they're in different clusters (correct) or same (incorrect)
        if '2022 WL 15153410' in found_clusters and '855 F.2d 569' in found_clusters:
            if found_clusters['2022 WL 15153410'] != found_clusters['855 F.2d 569']:
                print("\n✅ CORRECT: Citations are in different clusters")
            else:
                print("\n❌ INCORRECT: Citations are still in the same cluster")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

# Run the test
try:
    asyncio.run(test_motion_pdf())
except Exception as e:
    print(f"Test failed: {e}")

print("\n" + "=" * 80)
print("SUMMARY:")
print("-" * 40)
print("1. WL citations should show 'proprietary format' message")
print("2. WL and reporter citations should be in separate clusters")
print("3. 2022 WL 15153410 and 855 F.2d 569 should NOT be clustered together")
print("=" * 80)

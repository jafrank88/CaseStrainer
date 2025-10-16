#!/usr/bin/env python
"""Test New Mexico vendor-neutral citation extraction - Fixed"""
import sys
sys.path.insert(0, 'd:/dev/casestrainer')

test_text = """
Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977, 985 (2016)
"""

print("=" * 80)
print("NEW MEXICO VENDOR-NEUTRAL CITATION TEST")
print("=" * 80)
print(f"Test text: {test_text.strip()}")

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
import asyncio

processor = UnifiedCitationProcessorV2()
result = asyncio.run(processor.process_text(test_text))

citations = result.get('citations', [])
clusters = result.get('clusters', [])

print(f"\n📊 RESULTS:")
print(f"   Citations found: {len(citations)}")
print(f"   Clusters found: {len(clusters)}")

print(f"\n📋 CITATIONS:")
for i, cit in enumerate(citations, 1):
    # Handle both dict and object
    if hasattr(cit, 'citation'):
        cit_text = cit.citation
        extracted = cit.extracted_case_name
        method = cit.method
    else:
        cit_text = cit.get('citation', 'N/A')
        extracted = cit.get('extracted_case_name', 'N/A')
        method = cit.get('method', 'N/A')
    
    print(f"\n  [{i}] {cit_text}")
    print(f"      Extracted: {extracted}")
    print(f"      Method: {method}")
    
    # Identify type
    if 'NM' in cit_text and '-' in cit_text:
        print(f"      ✅ VENDOR-NEUTRAL FORMAT")
    elif 'P.3d' in cit_text:
        print(f"      ✅ REPORTER FORMAT")

if clusters:
    print(f"\n🔗 CLUSTERS:")
    for cluster in clusters:
        if hasattr(cluster, 'citations'):
            cluster_cits = cluster.citations
            cluster_id = cluster.cluster_id
        else:
            cluster_cits = cluster.get('citations', [])
            cluster_id = cluster.get('cluster_id', 'N/A')
        
        print(f"\n  Cluster {cluster_id}: {len(cluster_cits)} citations")
        for cit in cluster_cits:
            if hasattr(cit, 'citation'):
                print(f"    - {cit.citation}")
            else:
                print(f"    - {cit.get('citation', 'N/A')}")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

if len(citations) == 2:
    print("✅ SUCCESS: Both citations extracted")
    if len(clusters) == 1:
        print("✅ SUCCESS: Recognized as parallel citations (1 cluster)")
    else:
        print("❌ ISSUE: Should be 1 cluster but found", len(clusters))
else:
    print(f"❌ ISSUE: Expected 2 citations but found {len(citations)}")

print("\n💡 EXPECTED BEHAVIOR:")
print("   - Extract 2017-NM-007 (vendor-neutral)")
print("   - Extract 388 P.3d 977 (reporter)")
print("   - Cluster them as parallel citations")
print("   - Use same extracted case name for both")

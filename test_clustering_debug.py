#!/usr/bin/env python3
"""
Debug script to test clustering functionality
"""

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
from src.enhanced_v2_processor import EnhancedV2Processor

# Test text with known citations
test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""

print("=== TESTING CLUSTERING FUNCTIONALITY ===")
print(f"Test text: {test_text[:100]}...")

# Test 1: Standard v2 processor
print("\n1. Testing Standard v2 Processor:")
v2 = UnifiedCitationProcessorV2()
v2_citations = v2.process_text(test_text)
print(f"   Citations found: {len(v2_citations)}")

# Test clustering
clusters = v2.group_citations_into_clusters(v2_citations, test_text)
print(f"   Clusters found: {len(clusters)}")

for i, cluster in enumerate(clusters):
    print(f"   Cluster {i+1}:")
    for citation in cluster.get('citations', []):
        print(f"     - {citation.get('citation', 'Unknown')}")

# Test 2: Enhanced v2 processor
print("\n2. Testing Enhanced v2 Processor:")
enhanced = EnhancedV2Processor()
enhanced_results = enhanced.process_text(test_text)
print(f"   Enhanced results: {len(enhanced_results)}")

# Test 3: Document processing integration
print("\n3. Testing Document Processing Integration:")
from src.document_processing_unified import process_document
result = process_document(content=test_text)
print(f"   Document processing results: {len(result['citations'])}")

# Show clustering information
print("\n4. Clustering Analysis:")
for i, citation in enumerate(result['citations'], 1):
    is_parallel = citation.get('is_parallel', False)
    parallel_citations = citation.get('parallel_citations', [])
    cluster_id = citation.get('cluster_id')
    
    print(f"   {i}. {citation['citation']}")
    print(f"      Is Parallel: {is_parallel}")
    print(f"      Cluster ID: {cluster_id}")
    print(f"      Parallel Citations: {parallel_citations}")
    print()

print("=== CLUSTERING TEST COMPLETE ===") 
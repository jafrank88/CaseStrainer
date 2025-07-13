#!/usr/bin/env python3

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_cluster_metadata():
    # Initialize processor with debug mode
    processor = UnifiedCitationProcessorV2(ProcessingConfig(debug_mode=True))
    
    # Test text with parallel citations
    text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print("Processing text...")
    results = processor.process_text(text)
    print(f"Extracted {len(results)} citations")
    
    print("\nGrouping into clusters...")
    clusters = processor.group_citations_into_clusters(results)
    print(f"Created {len(clusters)} clusters")
    
    print("\nCluster details:")
    for i, cluster in enumerate(clusters):
        print(f"Cluster {i+1}:")
        print(f"  canonical_name: {cluster.get('canonical_name')}")
        print(f"  canonical_date: {cluster.get('canonical_date')}")
        print(f"  extracted_case_name: {cluster.get('extracted_case_name')}")
        print(f"  extracted_date: {cluster.get('extracted_date')}")
        print(f"  size: {cluster.get('size')}")
        print(f"  citations: {[c.get('citation') for c in cluster.get('citations', [])]}")
        print()

if __name__ == "__main__":
    test_cluster_metadata() 
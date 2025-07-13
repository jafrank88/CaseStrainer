#!/usr/bin/env python3
"""
Direct test of clustering functionality without needing the server.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
import asyncio

def test_clustering_direct():
    """Test clustering directly with the processor."""
    
    # Test text with parallel citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)."""
    
    print("🧪 Testing clustering directly with UnifiedCitationProcessorV2...")
    print(f"Test text: {test_text[:100]}...")
    print("-" * 60)
    
    try:
        # Initialize processor
        config = ProcessingConfig(
            use_eyecite=True,
            use_regex=True,
            extract_case_names=True,
            extract_dates=True,
            enable_clustering=True,
            enable_deduplication=True,
            debug_mode=True,
            min_confidence=0.0
        )
        processor = UnifiedCitationProcessorV2(config)
        
        # Test async processing
        print("📝 Testing async processing...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                processor.process_document_citations(test_text, 'text', {})
            )
        finally:
            loop.close()
        
        citations = result.get('citations', [])
        clusters = result.get('clusters', [])
        
        print(f"\n📊 Results:")
        print(f"  Total citations: {len(citations)}")
        print(f"  Total clusters: {len(clusters)}")
        
        print(f"\n📋 Citations:")
        for i, citation in enumerate(citations):
            print(f"  {i+1}. {citation.get('citation', 'N/A')}")
            print(f"     Case: {citation.get('canonical_name', 'N/A')}")
            print(f"     Extracted: {citation.get('extracted_case_name', 'N/A')}")
            print(f"     Verified: {citation.get('verified', False)}")
            print(f"     Parallel: {citation.get('parallel_citations', [])}")
            print()
        
        print(f"\n🔗 Clusters:")
        for i, cluster in enumerate(clusters):
            print(f"  Cluster {i+1}:")
            print(f"    Case: {cluster.get('canonical_name', 'N/A')}")
            print(f"    Size: {cluster.get('cluster_size', 0)}")
            print(f"    Has parallel: {cluster.get('has_parallel_citations', False)}")
            print(f"    Citations:")
            for j, citation in enumerate(cluster.get('citations', [])):
                print(f"      {j+1}. {citation.get('citation', 'N/A')}")
            print()
        
        # Check if parallel citations are properly clustered
        parallel_citations = [c for c in citations if c.get('parallel_citations')]
        print(f"\n✅ Parallel Citations Found: {len(parallel_citations)}")
        for citation in parallel_citations:
            print(f"  - {citation.get('citation')} (parallel to: {citation.get('parallel_citations')})")
        
        # Check if clusters contain parallel citations
        clusters_with_parallel = [c for c in clusters if c.get('has_parallel_citations')]
        print(f"\n✅ Clusters with Parallel Citations: {len(clusters_with_parallel)}")
        for cluster in clusters_with_parallel:
            print(f"  - {cluster.get('canonical_name')} (size: {cluster.get('cluster_size')})")
        
        # Verify that citations with newlines are fixed
        citations_with_newlines = [c for c in citations if '\n' in c.get('citation', '')]
        print(f"\n⚠️  Citations with newlines: {len(citations_with_newlines)}")
        for citation in citations_with_newlines:
            print(f"  - {repr(citation.get('citation'))}")
        
        # Test sync processing as well
        print(f"\n📝 Testing sync processing...")
        sync_citations = processor.process_text(test_text)
        sync_clusters = processor.group_citations_into_clusters(sync_citations)
        
        print(f"  Sync citations: {len(sync_citations)}")
        print(f"  Sync clusters: {len(sync_clusters)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_clustering_direct()
    if success:
        print("\n🎉 Clustering test completed successfully!")
    else:
        print("\n💥 Clustering test failed!") 
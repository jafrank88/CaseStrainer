import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2

async def test_extracted_data():
    print("Initializing citation processor...")
    processor = UnifiedCitationProcessorV2()
    
    # Test with a simple text containing known citations
    test_text = """
    In State v. Smith, 123 Wash. 2d 1, 864 P.2d 87 (1993), the court held that...
    See also 536 P.3d 191 (Wash. 2023) and 169 Wn.2d 815, 239 P.3d 354 (2010).
    """
    
    print("\nProcessing text...")
    results = await processor.process_document_citations(test_text)
    
    # Print results
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    
    # Print citations
    print("\nCITATIONS:")
    print("-"*40)
    for i, citation in enumerate(results.get('citations', []), 1):
        print(f"\nCitation {i}:")
        print(f"  - Full Citation: {citation.get('citation')}")
        print(f"  - Extracted Case Name: {repr(citation.get('extracted_case_name'))}")
        print(f"  - Extracted Date: {repr(citation.get('extracted_date'))}")
        print(f"  - Canonical Name: {repr(citation.get('canonical_name'))}")
        print(f"  - Canonical Date: {repr(citation.get('canonical_date'))}")
        print(f"  - Verified: {citation.get('verified')}")
        print(f"  - Source: {citation.get('source')}")
    
    # Print clusters
    print("\nCLUSTERS:")
    print("-"*40)
    for i, cluster in enumerate(results.get('clusters', []), 1):
        print(f"\nCluster {i}:")
        print(f"  - Cluster ID: {cluster.get('cluster_id')}")
        print(f"  - Extracted Case Name: {repr(cluster.get('extracted_case_name'))}")
        print(f"  - Extracted Date: {repr(cluster.get('extracted_date'))}")
        print(f"  - Cluster Size: {len(cluster.get('citations', []))}")
        
        # Print citations in this cluster
        print("  Citations:")
        for j, cite in enumerate(cluster.get('citations', []), 1):
            cite_obj = cite if isinstance(cite, dict) else cite.__dict__
            print(f"    {j}. {cite_obj.get('citation')}")
            print(f"       Extracted Name: {repr(cite_obj.get('extracted_case_name'))}")
            print(f"       Extracted Date: {repr(cite_obj.get('extracted_date'))}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    print("Starting test...")
    asyncio.run(test_extracted_data())

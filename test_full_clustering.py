#!/usr/bin/env python3
"""
Test the full backend clustering pipeline with the exact paragraph
"""

import asyncio
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.models import ProcessingConfig

async def test_full_clustering():
    """Test the complete backend clustering pipeline"""
    
    # Exact paragraph from the user
    test_text = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting 
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition 
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is 
substantial when sufficient to persuade a fair-minded person of the truth of the 
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041 
(2017). "Competent evidence sufficient to support the trial court's decision to 
grant . . . a domestic violence protection order may contain hearsay or be wholly 
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233 
(2010)."""

    print("Testing FULL backend clustering pipeline:")
    print("=" * 80)
    print(f"Text: {test_text[:100]}...")
    print("=" * 80)

    # Initialize the processor
    config = ProcessingConfig()
    processor = UnifiedCitationProcessorV2(config)
    
    # Process the text
    print("\n🔄 Processing text through backend pipeline...")
    result = await processor.process_text(test_text)
    
    if not result:
        print("❌ No result returned from processor")
        return
    
    print(f"\n✅ Processing completed!")
    print(f"📊 Citations found: {len(result.get('citations', []))}")
    print(f"🔗 Clusters created: {len(result.get('clusters', []))}")
    
    # Display citations
    print(f"\n📋 CITATIONS:")
    print("-" * 50)
    citations = result.get('citations', [])
    for i, citation in enumerate(citations, 1):
        if hasattr(citation, 'citation'):
            # CitationResult object
            print(f"{i}. {citation.citation}")
            print(f"   Case Name: {getattr(citation, 'extracted_case_name', 'N/A')}")
            print(f"   Date: {getattr(citation, 'extracted_date', 'N/A')}")
            print(f"   Year: {getattr(citation, 'extracted_year', 'N/A')}")
        else:
            # Dictionary
            print(f"{i}. {citation.get('citation', 'N/A')}")
            print(f"   Case Name: {citation.get('extracted_case_name', 'N/A')}")
            print(f"   Date: {citation.get('extracted_date', 'N/A')}")
            print(f"   Year: {citation.get('extracted_year', 'N/A')}")
    
    # Display clusters
    print(f"\n🔗 CLUSTERS:")
    print("-" * 50)
    clusters = result.get('clusters', [])
    for i, cluster in enumerate(clusters, 1):
        if isinstance(cluster, dict):
            # Dictionary format
            print(f"\nCluster {i}:")
            print(f"  Case Name: {cluster.get('case_name', 'N/A')}")
            print(f"  Year: {cluster.get('year', 'N/A')}")
            print(f"  Citations: {len(cluster.get('citations', []))}")
            citations_in_cluster = cluster.get('citations', [])
            for j, citation in enumerate(citations_in_cluster, 1):
                if hasattr(citation, 'citation'):
                    print(f"    {j}. {citation.citation}")
                else:
                    print(f"    {j}. {citation.get('citation', 'N/A')}")
        else:
            # Object format
            print(f"\nCluster {i}:")
            print(f"  Case Name: {getattr(cluster, 'case_name', 'N/A')}")
            print(f"  Year: {getattr(cluster, 'year', 'N/A')}")
            print(f"  Citations: {len(getattr(cluster, 'citations', []))}")
            citations_in_cluster = getattr(cluster, 'citations', [])
            for j, citation in enumerate(citations_in_cluster, 1):
                if hasattr(citation, 'citation'):
                    print(f"    {j}. {citation.citation}")
                else:
                    print(f"    {j}. {citation.get('citation', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("Expected Results:")
    print("1. Knight case: 'In re Vulnerable Adult Petition for Knight' (2014) - 2 citations")
    print("2. Black case: 'In re Marriage of Black' (2017) - 2 citations")  
    print("3. Blackmon case: 'Blackmon v. Blackmon' (2010) - 2 citations")
    print("=" * 80)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_full_clustering())




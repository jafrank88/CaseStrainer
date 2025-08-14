"""
End-to-end test to verify that every citation gets a name, year, and cluster
when processing a real test paragraph with the unified clustering system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_clustering import cluster_citations_unified
from src.unified_citation_processor_v2 import UnifiedCitationProcessor
from src.models import ProcessingConfig

def test_real_paragraph():
    """Test the unified clustering system on a real legal paragraph."""
    
    # Real legal paragraph with multiple citations
    test_paragraph = """
    The Supreme Court's decision in Miranda v. Arizona, 384 U.S. 436, 86 S. Ct. 1602, 16 L. Ed. 2d 694 (1966), 
    established the requirement for police to inform suspects of their rights. This built upon earlier precedent 
    from Gideon v. Wainwright, 372 U.S. 335 (1963), which established the right to counsel. The Court also 
    referenced Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686, 98 L. Ed. 873 (1954), in its analysis 
    of constitutional protections.
    """
    
    print("Testing Unified Clustering on Real Legal Paragraph")
    print("=" * 60)
    print(f"Test paragraph:\n{test_paragraph.strip()}")
    print("=" * 60)
    
    # Process the paragraph through the unified pipeline
    config = ProcessingConfig(
        enable_verification=False,  # Disable to focus on clustering
        enable_clustering=True,
        enable_extraction=True
    )
    
    processor = UnifiedCitationProcessor(config)
    result = processor.process_text(test_paragraph)
    
    print(f"\nExtracted {len(result['citations'])} citations")
    print(f"Created {len(result['clusters'])} clusters")
    
    # Check each citation for name, year, and cluster
    print("\nCitation Analysis:")
    print("-" * 40)
    
    all_have_name = True
    all_have_year = True
    all_have_cluster = True
    
    for i, citation in enumerate(result['citations'], 1):
        name = citation.get('extracted_case_name', 'N/A')
        year = citation.get('extracted_date', 'N/A')
        cluster_id = citation.get('metadata', {}).get('cluster_id', 'None')
        
        print(f"{i}. {citation['citation']}")
        print(f"   Name: {name}")
        print(f"   Year: {year}")
        print(f"   Cluster: {cluster_id}")
        print()
        
        if not name or name == 'N/A':
            all_have_name = False
        if not year or year == 'N/A':
            all_have_year = False
        if not cluster_id or cluster_id == 'None':
            all_have_cluster = False
    
    # Summary
    print("Summary:")
    print(f"✓ All citations have case names: {all_have_name}")
    print(f"✓ All citations have years: {all_have_year}")
    print(f"✓ All citations have clusters: {all_have_cluster}")
    
    if all_have_name and all_have_year and all_have_cluster:
        print("\n🎉 SUCCESS: Every citation has name, year, and cluster!")
    else:
        print("\n❌ ISSUE: Some citations are missing data")
    
    # Show cluster details
    print(f"\nCluster Details:")
    print("-" * 40)
    for i, cluster in enumerate(result['clusters'], 1):
        print(f"Cluster {i}: {cluster['case_name']} ({cluster['year']})")
        print(f"  Size: {cluster['size']} citations")
        print(f"  Citations: {cluster['citations']}")
        print()

if __name__ == "__main__":
    test_real_paragraph()

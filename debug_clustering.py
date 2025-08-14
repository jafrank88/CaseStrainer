"""
Debug script to understand why all citations are getting the same name/year.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_clustering import UnifiedCitationClusterer
from src.models import CitationResult

def debug_clustering_step_by_step():
    """Debug the clustering process step by step."""
    
    citations = [
        # Miranda v. Arizona parallel citations
        CitationResult(
            citation="384 U.S. 436",
            start_index=50,
            end_index=62,
            extracted_case_name="Miranda v. Arizona",
            extracted_date=None,
            parallel_citations=["86 S. Ct. 1602", "16 L. Ed. 2d 694"],
            metadata={}
        ),
        CitationResult(
            citation="86 S. Ct. 1602", 
            start_index=64,
            end_index=78,
            extracted_case_name=None,
            extracted_date=None,
            parallel_citations=["384 U.S. 436", "16 L. Ed. 2d 694"],
            metadata={}
        ),
        CitationResult(
            citation="16 L. Ed. 2d 694",
            start_index=80,
            end_index=97,
            extracted_case_name=None,
            extracted_date="1966",
            parallel_citations=["384 U.S. 436", "86 S. Ct. 1602"],
            metadata={}
        ),
        
        # Gideon v. Wainwright (single citation)
        CitationResult(
            citation="372 U.S. 335",
            start_index=200,
            end_index=212,
            extracted_case_name="Gideon v. Wainwright",
            extracted_date="1963",
            parallel_citations=[],  # No parallel citations
            metadata={}
        ),
        
        # Brown v. Board parallel citations
        CitationResult(
            citation="347 U.S. 483",
            start_index=300,
            end_index=312,
            extracted_case_name="Brown v. Board of Education",
            extracted_date=None,
            parallel_citations=["74 S. Ct. 686", "98 L. Ed. 873"],
            metadata={}
        ),
        CitationResult(
            citation="74 S. Ct. 686",
            start_index=314,
            end_index=327,
            extracted_case_name=None,
            extracted_date=None,
            parallel_citations=["347 U.S. 483", "98 L. Ed. 873"],
            metadata={}
        ),
        CitationResult(
            citation="98 L. Ed. 873",
            start_index=329,
            end_index=342,
            extracted_case_name=None,
            extracted_date="1954",
            parallel_citations=["347 U.S. 483", "74 S. Ct. 686"],
            metadata={}
        ),
    ]
    
    print("DEBUG: Step-by-step clustering analysis")
    print("=" * 50)
    
    clusterer = UnifiedCitationClusterer(config={'debug_mode': True})
    
    # Debug step 1: Check parallel grouping
    print("Step 1: Parallel relationship grouping")
    parallel_groups = clusterer._group_by_parallel_relationships(citations)
    print(f"Found {len(parallel_groups)} parallel groups:")
    for i, group in enumerate(parallel_groups):
        print(f"  Group {i+1}: {[c.citation for c in group]}")
        for citation in group:
            name = getattr(citation, 'extracted_case_name', 'None')
            year = getattr(citation, 'extracted_date', 'None')
            print(f"    {citation.citation}: name='{name}', year='{year}'")
    print()
    
    # Debug step 2: Check what happens during clustering
    print("Step 2: Before clustering - original data:")
    for citation in citations:
        name = getattr(citation, 'extracted_case_name', 'None')
        year = getattr(citation, 'extracted_date', 'None')
        print(f"  {citation.citation}: name='{name}', year='{year}'")
    print()
    
    # Apply clustering
    clusters = clusterer.cluster_citations(citations)
    
    print("Step 3: After clustering - final data:")
    for citation in citations:
        name = getattr(citation, 'extracted_case_name', 'None')
        year = getattr(citation, 'extracted_date', 'None')
        cluster_id = getattr(citation, 'metadata', {}).get('cluster_id', 'None')
        print(f"  {citation.citation}: name='{name}', year='{year}', cluster='{cluster_id}'")
    print()
    
    print(f"Final result: {len(clusters)} clusters")
    for cluster in clusters:
        print(f"  Cluster: {cluster['case_name']} ({cluster['year']}) - {cluster['citations']}")

if __name__ == "__main__":
    debug_clustering_step_by_step()

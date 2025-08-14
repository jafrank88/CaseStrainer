"""
Direct test to verify that every citation gets a name, year, and cluster
using the unified clustering system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_clustering import cluster_citations_unified
from src.models import CitationResult

def create_realistic_citations_from_text():
    """Create realistic citation objects as they would be extracted from text."""
    
    # Simulate citations as they would be extracted from a real paragraph
    citations = [
        # Miranda v. Arizona parallel citations
        CitationResult(
            citation="384 U.S. 436",
            start_index=50,
            end_index=62,
            extracted_case_name="Miranda v. Arizona",  # From first citation
            extracted_date=None,  # Will get from last citation
            parallel_citations=["86 S. Ct. 1602", "16 L. Ed. 2d 694"],
            metadata={}
        ),
        CitationResult(
            citation="86 S. Ct. 1602", 
            start_index=64,
            end_index=78,
            extracted_case_name=None,  # Will get from first citation
            extracted_date=None,
            parallel_citations=["384 U.S. 436", "16 L. Ed. 2d 694"],
            metadata={}
        ),
        CitationResult(
            citation="16 L. Ed. 2d 694",
            start_index=80,
            end_index=97,
            extracted_case_name=None,  # Will get from first citation
            extracted_date="1966",  # Last citation provides year
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
            parallel_citations=[],
            metadata={}
        ),
        
        # Brown v. Board parallel citations
        CitationResult(
            citation="347 U.S. 483",
            start_index=300,
            end_index=312,
            extracted_case_name="Brown v. Board of Education",  # From first citation
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
            extracted_date="1954",  # Last citation provides year
            parallel_citations=["347 U.S. 483", "74 S. Ct. 686"],
            metadata={}
        ),
    ]
    
    return citations

def test_every_citation_has_data():
    """Test that every citation gets a name, year, and cluster."""
    
    print("Testing: Does Every Citation Get Name, Year, and Cluster?")
    print("=" * 60)
    
    citations = create_realistic_citations_from_text()
    
    print(f"Starting with {len(citations)} citations")
    print("\nBEFORE clustering:")
    for i, citation in enumerate(citations, 1):
        name = getattr(citation, 'extracted_case_name', 'None')
        year = getattr(citation, 'extracted_date', 'None')
        print(f"{i}. {citation.citation}: name='{name}', year='{year}'")
    
    # Apply unified clustering
    clusters = cluster_citations_unified(citations)
    
    print(f"\nAFTER clustering: {len(clusters)} clusters created")
    print("\nFinal citation data:")
    print("-" * 40)
    
    all_have_name = True
    all_have_year = True
    all_have_cluster = True
    
    for i, citation in enumerate(citations, 1):
        name = getattr(citation, 'extracted_case_name', 'None')
        year = getattr(citation, 'extracted_date', 'None')
        cluster_id = getattr(citation, 'metadata', {}).get('cluster_id', 'None')
        
        print(f"{i}. {citation.citation}")
        print(f"   Name: '{name}'")
        print(f"   Year: '{year}'")
        print(f"   Cluster: '{cluster_id}'")
        print()
        
        if not name or name in ['None', 'N/A', '']:
            all_have_name = False
            print(f"   ❌ Missing name!")
        if not year or year in ['None', 'N/A', '']:
            all_have_year = False
            print(f"   ❌ Missing year!")
        if not cluster_id or cluster_id in ['None', '']:
            all_have_cluster = False
            print(f"   ❌ Missing cluster!")
    
    print("=" * 60)
    print("RESULTS:")
    print(f"✓ All citations have case names: {all_have_name}")
    print(f"✓ All citations have years: {all_have_year}")
    print(f"✓ All citations have clusters: {all_have_cluster}")
    
    if all_have_name and all_have_year and all_have_cluster:
        print("\n🎉 SUCCESS: Every citation has name, year, and cluster!")
        return True
    else:
        print("\n❌ ISSUE: Some citations are missing data")
        return False

if __name__ == "__main__":
    test_every_citation_has_data()

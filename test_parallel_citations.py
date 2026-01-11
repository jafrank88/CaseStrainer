"""
Test how CaseStrainer handles true parallel citations
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean
from src.unified_clustering_master import cluster_citations_unified_master

# Test with true parallel citations (same case, different reporters)
test_cases = [
    # Supreme Court case with parallel citations
    "Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686, 98 L. Ed. 873 (1954).",
    
    # Federal case with parallel citations
    "United States v. Nixon, 418 U.S. 683, 94 S. Ct. 2781, 41 L. Ed. 2d 939 (1974).",
    
    # State case with parallel citations
    "People v. Smith, 123 Cal. App. 3d 456, 456 Cal. Rptr. 789 (2021).",
    
    # Mixed parallel and series citations
    "See Smith v. Jones, 123 F.3d 456, 456 F. Supp. 2d 789; Doe v. Roe, 789 F.2d 123 (9th Cir. 2020)."
]

print("TESTING PARALLEL CITATION HANDLING")
print("=" * 80)

for i, test_text in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test_text[:50]}...")
    print("-" * 60)
    
    # Extract citations
    citations = extract_citations_clean(test_text)
    
    print(f"Extracted {len(citations)} citations:")
    
    for j, cit in enumerate(citations):
        print(f"\n  {j+1}. {cit.citation}")
        print(f"     Case Name: '{cit.extracted_case_name}'")
        print(f"     Method: {cit.method}")
        
        if hasattr(cit, 'metadata') and cit.metadata:
            print(f"     Metadata: {cit.metadata}")
    
    # Test clustering
    print(f"\nClustering results:")
    clusters = cluster_citations_unified_master(
        citations,
        test_text,
        enable_verification=False,  # Skip verification for this test
        request_id=None,
        progress_callback=None
    )
    
    print(f"  Number of clusters: {len(clusters)}")
    
    for k, cluster in enumerate(clusters):
        cluster_name = cluster.get('best_name', 'Unknown')
        print(f"\n  Cluster {k+1}: '{cluster_name}'")
        print(f"    Citations in cluster:")
        
        for cit in cluster.get('citations', []):
            if isinstance(cit, dict):
                citation_text = cit.get('citation', 'Unknown')
                case_name = cit.get('extracted_case_name', 'N/A')
            else:
                citation_text = getattr(cit, 'citation', 'Unknown')
                case_name = getattr(cit, 'extracted_case_name', 'N/A')
            print(f"      - {citation_text}: '{case_name}'")
    
    print("\n" + "=" * 80)

print("\nANALYSIS:")
print("-" * 60)
print("For true parallel citations:")
print("✅ All citations should have the SAME case name")
print("✅ All citations should be in the SAME cluster")
print("✅ The cluster name should be the case name")
print("\nFor series citations (different cases):")
print("✅ Citations should have different case names or 'N/A'")
print("✅ Citations should be in DIFFERENT clusters")

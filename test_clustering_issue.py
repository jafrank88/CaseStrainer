#!/usr/bin/env python3
"""
Test why these citations are being clustered incorrectly
"""

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_clustering_issue():
    """Test the specific clustering issue with the provided text"""
    
    text = """In particular, courts have concluded that the First Amendment right of access applies to motions to conceal documents or information from public view, including motions to proceed pseudonymously. See Doe v. Teachers Council, Inc., 2024 WL 1232082, at *3 (motion to proceed pseudonymously); Schiller v. City of New York, No. 04 CIV. 7921, 2006 WL 2788256, at *5 (S.D.N.Y. Sept. 27, 2006) (protective order brief); Doe v. City of New York, No. 1:22-CV-7910 (LTS), 2022 WL 15153410, at *1, *3 (letter seeking "leave to file a motion to proceed anonymously or under seal").
The First Amendment right of access calls for an even more demanding test than does the common-law right of access: "The party seeking closure or sealing must show that such a restriction of the first amendment right of public access is necessitated by a compelling government interest." In re Search Warrant (Gunn), 855 F.2d 569, 574 (8th Cir. 1988). For the reasons given above, this test cannot be satisfied here."""
    
    print("Testing citation extraction and clustering:")
    print("=" * 80)
    print()
    
    processor = UnifiedCitationProcessorV2()
    
    # Extract citations
    citations = processor._extract_with_regex_enhanced(text)
    
    print(f"Extracted {len(citations)} citations:")
    for i, cit in enumerate(citations):
        print(f"  {i+1}. {cit.citation}")
        if cit.extracted_case_name:
            print(f"     Case name: {cit.extracted_case_name}")
        if cit.extracted_date:
            print(f"     Date: {cit.extracted_date}")
        print()
    
    # Check clustering
    from src.unified_clustering_master import get_master_clusterer
    clustering = get_master_clusterer()
    clusters = clustering.cluster_citations(citations, text)
    
    print(f"Created {len(clusters)} clusters:")
    for i, cluster in enumerate(clusters):
        print(f"\n  Cluster {i+1}:")
        print(f"    Case name: {cluster.get('cluster_case_name', 'N/A')}")
        print(f"    Year: {cluster.get('cluster_year', 'N/A')}")
        cluster_cits = cluster.get('citations', [])
        for j, cit in enumerate(cluster_cits):
            cit_text = getattr(cit, 'citation', str(cit)) if hasattr(cit, 'citation') else cit.get('citation', str(cit))
            print(f"    {j+1}. {cit_text}")
    
    # Analyze why they might be clustered
    print("\n" + "=" * 80)
    print("ANALYSIS:")
    print("-" * 40)
    print("These citations are likely being clustered because:")
    print("1. They appear in the same paragraph discussing First Amendment rights")
    print("2. Two involve 'Doe' as a party")
    print("3. Two involve 'City of New York'")
    print("4. They're in close proximity to each other")
    print("\nThis is INCORRECT clustering - they are 4 separate cases!")

if __name__ == "__main__":
    test_clustering_issue()

#!/usr/bin/env python3
"""
Test with the original text including all 4 citations
"""

from src.unified_clustering_master import get_master_clusterer

def test_original_text():
    """Test with the original user text"""
    
    text = """In particular, courts have concluded that the First Amendment right of access applies to motions to conceal documents or information from public view, including motions to proceed pseudonymously. See Doe v. Teachers Council, Inc., 2024 WL 1232082, at *3 (motion to proceed pseudonymously); Schiller v. City of New York, No. 04 CIV. 7921, 2006 WL 2788256, at *5 (S.D.N.Y. Sept. 27, 2006) (protective order brief); Doe v. City of New York, No. 1:22-CV-7910 (LTS), 2022 WL 15153410, at *1, *3 (letter seeking "leave to file a motion to proceed anonymously or under seal").
The First Amendment right of access calls for an even more demanding test than does the common-law right of access: "The party seeking closure or sealing must show that such a restriction of the first amendment right of public access is necessitated by a compelling government interest." In re Search Warrant (Gunn), 855 F.2d 569, 574 (8th Cir. 1988). For the reasons given above, this test cannot be satisfied here."""
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    processor = UnifiedCitationProcessorV2()
    citations = processor._extract_with_regex_enhanced(text)
    
    print("=" * 80)
    print("TESTING ORIGINAL TEXT WITH ALL 4 CITATIONS")
    print("=" * 80)
    print()
    
    print(f"Extracted {len(citations)} citations:")
    for i, cit in enumerate(citations):
        print(f"  {i+1}. {cit.citation}")
    print()
    
    config = {"enable_verification": True}
    clustering = get_master_clusterer(config)
    
    # Run the full clustering pipeline
    clusters = clustering.cluster_citations(citations, text)
    
    print(f"\nFinal result: {len(clusters)} clusters")
    
    if len(clusters) < 4:
        print("ERROR: Some citations were incorrectly merged!")
        print("\nCluster contents:")
        for i, cluster in enumerate(clusters):
            cits = cluster.get("citations", [])
            print(f"\nCluster {i+1}: {len(cits)} citations")
            for cit in cits:
                if isinstance(cit, dict):
                    print(f"  - {cit.get('citation', 'N/A')}")
                else:
                    print(f"  - {cit.citation}")
    else:
        print("SUCCESS: All citations remain in separate clusters")
        for i, cluster in enumerate(clusters):
            cits = cluster.get("citations", [])
            print(f"\nCluster {i+1}: {len(cits)} citations")
            for cit in cits:
                if isinstance(cit, dict):
                    print(f"  - {cit.get('citation', 'N/A')}")
                else:
                    print(f"  - {cit.citation}")

if __name__ == "__main__":
    test_original_text()

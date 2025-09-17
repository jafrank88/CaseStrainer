import sys
import os
sys.path.append('src')

def debug_clustering_issue():
    """Debug why clustering isn't working for the user's paragraph."""
    
    # Test text with Bostain parallel citations
    test_text = """'[A]gency interpretations of statutes are accorded deference only if "(1) the particular agency is charged with the administration and enforcement of the statute, (2) the statute is ambiguous, and (3) the statute falls within the agency's special expertise."' Lucid Grp. USA, Inc., 33 Wn. App. 2d at 80 (emphasis omitted) (quoting Fode v. Dep't of Ecology, 22 Wn. App. 2d 22, 33, 509 P.3d 325 (2022) (quoting Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007))). However, courts are not bound by agency interpretation as courts have the '"ultimate authority to interpret a statute."' Id. (quoting Port of Tacoma v. Sacks, 19 Wn. App. 2d 295, 304, 495 P.3d 866 No. 103394-0 12 (2021) (quoting Bostain, 159 Wn.2d at 716))."""
    
    print("=" * 80)
    print("🔍 DEBUGGING CLUSTERING ISSUE")
    print("=" * 80)
    
    # Step 1: Extract citations using the same method as the sync processor
    print("Step 1: Extracting citations...")
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        processor = UnifiedCitationProcessorV2()
        citations = processor._extract_with_regex(test_text)
        
        print(f"Found {len(citations)} citations:")
        for i, citation in enumerate(citations, 1):
            print(f"  {i}. {getattr(citation, 'citation', 'NO_CITATION_ATTR')}")
            print(f"     Case: {getattr(citation, 'extracted_case_name', 'NO_CASE_NAME')}")
            print(f"     Year: {getattr(citation, 'extracted_date', 'NO_DATE')}")
            print(f"     Start: {getattr(citation, 'start_index', 'NO_START_INDEX')}")
            print(f"     Type: {type(citation)}")
            print(f"     Attributes: {dir(citation)[:10]}...")  # First 10 attributes
            print()
        
    except Exception as e:
        print(f"❌ Citation extraction failed: {e}")
        return
    
    # Step 2: Test clustering directly
    print("Step 2: Testing clustering...")
    try:
        from unified_citation_clustering import cluster_citations_unified
        
        clusters = cluster_citations_unified(
            citations, 
            test_text, 
            enable_verification=False  # Disable verification to focus on clustering
        )
        
        print(f"Clustering returned {len(clusters)} clusters")
        for i, cluster in enumerate(clusters, 1):
            print(f"  Cluster {i}: {cluster}")
            print()
            
    except Exception as e:
        print(f"❌ Clustering failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Check for Bostain citations specifically
    print("Step 3: Analyzing Bostain citations...")
    bostain_citations = [c for c in citations if 'bostain' in getattr(c, 'extracted_case_name', '').lower()]
    
    if len(bostain_citations) >= 2:
        print(f"✅ Found {len(bostain_citations)} Bostain citations:")
        for citation in bostain_citations:
            print(f"  - {getattr(citation, 'citation', 'N/A')}")
        
        # Test parallel detection manually
        print("\nTesting parallel detection manually...")
        try:
            from unified_citation_clustering import UnifiedCitationClusterer
            clusterer = UnifiedCitationClusterer()
            
            citation1 = bostain_citations[0]
            citation2 = bostain_citations[1]
            
            is_parallel = clusterer._are_citations_parallel_by_proximity(citation1, citation2, test_text)
            print(f"Are parallel: {is_parallel}")
            
            # Check individual components
            reporter1 = clusterer._extract_reporter_type(getattr(citation1, 'citation', ''))
            reporter2 = clusterer._extract_reporter_type(getattr(citation2, 'citation', ''))
            print(f"Reporter 1: {reporter1}")
            print(f"Reporter 2: {reporter2}")
            
            patterns_match = clusterer._match_parallel_patterns(
                getattr(citation1, 'citation', ''),
                getattr(citation2, 'citation', '')
            )
            print(f"Patterns match: {patterns_match}")
            
        except Exception as e:
            print(f"❌ Manual parallel detection failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"❌ Expected 2+ Bostain citations, found {len(bostain_citations)}")
    
    print("=" * 80)

if __name__ == "__main__":
    debug_clustering_issue()

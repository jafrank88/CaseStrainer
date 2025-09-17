import sys
import os
import logging

# Set up simple logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

sys.path.append('src')

def test_real_citations_clustering():
    """Test clustering with real citation objects from the v2 processor."""
    
    test_text = """'[A]gency interpretations of statutes are accorded deference only if "(1) the particular agency is charged with the administration and enforcement of the statute, (2) the statute is ambiguous, and (3) the statute falls within the agency's special expertise."' Lucid Grp. USA, Inc., 33 Wn. App. 2d at 80 (emphasis omitted) (quoting Fode v. Dep't of Ecology, 22 Wn. App. 2d 22, 33, 509 P.3d 325 (2022) (quoting Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007))). However, courts are not bound by agency interpretation as courts have the '"ultimate authority to interpret a statute."' Id. (quoting Port of Tacoma v. Sacks, 19 Wn. App. 2d 295, 304, 495 P.3d 866 No. 103394-0 12 (2021) (quoting Bostain, 159 Wn.2d at 716))."""
    
    print("=" * 60)
    print("REAL CITATIONS CLUSTERING TEST")
    print("=" * 60)
    
    # Step 1: Extract citations using the real v2 processor
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        citations = processor._extract_with_regex(test_text)
        
        print(f"Extracted {len(citations)} real citations:")
        for i, citation in enumerate(citations, 1):
            print(f"  {i}. {getattr(citation, 'citation', 'NO_CITATION')}")
            print(f"     Case: {getattr(citation, 'extracted_case_name', 'NO_CASE')}")
            print(f"     Year: {getattr(citation, 'extracted_date', 'NO_DATE')}")
            print(f"     Type: {type(citation)}")
            print(f"     Has start_index: {hasattr(citation, 'start_index')}")
            if hasattr(citation, 'start_index'):
                print(f"     Start index: {getattr(citation, 'start_index', 'N/A')}")
            print()
        
        # Step 2: Test clustering with real citations
        from unified_citation_clustering import cluster_citations_unified
        
        print(f"Testing clustering with real citations...")
        result = cluster_citations_unified(citations, test_text, enable_verification=False)
        
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result) if hasattr(result, '__len__') else 'N/A'}")
        
        if isinstance(result, list):
            print(f"Clusters found: {len(result)}")
            for i, cluster in enumerate(result, 1):
                print(f"  Cluster {i}:")
                print(f"    ID: {cluster.get('cluster_id', 'N/A')}")
                print(f"    Citations: {cluster.get('citations', [])}")
                print(f"    Type: {cluster.get('cluster_type', 'N/A')}")
        else:
            print(f"Unexpected result type: {type(result)}")
            print(f"Result: {result}")
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    test_real_citations_clustering()

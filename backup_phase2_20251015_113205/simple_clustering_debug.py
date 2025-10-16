import sys
import os
sys.path.append('src')

def simple_debug():
    """Simple debug to understand why clustering isn't working."""
    
    print("Testing clustering with simple citations...")
    
    # Create simple test citations that should cluster
    class SimpleCitation:
        def __init__(self, citation, case_name, year, start_index):
            self.citation = citation
            self.extracted_case_name = case_name
            self.extracted_date = year
            self.start_index = start_index
            self.verified = False
            self.is_verified = False
    
    # Create Bostain parallel citations
    citation1 = SimpleCitation("159 Wn.2d 700", "Bostain v. Food Express", "2007", 100)
    citation2 = SimpleCitation("153 P.3d 846", "Bostain v. Food Express", "2007", 120)
    
    citations = [citation1, citation2]
    test_text = "Some text with Bostain v. Food Express, 159 Wn.2d 700, 153 P.3d 846 (2007)"
    
    print(f"Created {len(citations)} test citations:")
    for i, c in enumerate(citations, 1):
        print(f"  {i}. {c.citation} - {c.extracted_case_name} ({c.extracted_date})")
    
    # Test clustering
    try:
        from unified_citation_clustering import cluster_citations_unified
        
        print("\nTesting clustering...")
        clusters = cluster_citations_unified(citations, test_text, enable_verification=False)
        
        print(f"Clustering returned: {type(clusters)}")
        print(f"Number of clusters: {len(clusters) if clusters else 0}")
        
        if clusters:
            for i, cluster in enumerate(clusters, 1):
                print(f"  Cluster {i}: {cluster}")
        else:
            print("  No clusters returned")
            
    except Exception as e:
        print(f"Clustering failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_debug()

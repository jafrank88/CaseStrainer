import sys
import os
import logging

# Set up simple logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

sys.path.append('src')

def test_clustering_direct():
    """Test clustering directly to see what's happening."""
    
    test_text = """Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007)"""
    
    print("=" * 60)
    print("DIRECT CLUSTERING TEST")
    print("=" * 60)
    
    # Step 1: Create simple citation objects
    class SimpleCitation:
        def __init__(self, citation, case_name, year, start_index):
            self.citation = citation
            self.extracted_case_name = case_name
            self.extracted_date = year
            self.start_index = start_index
            self.verified = False
            self.is_verified = False
    
    citations = [
        SimpleCitation("159 Wn.2d 700", "Bostain v. Food Express", "2007", 100),
        SimpleCitation("153 P.3d 846", "Bostain v. Food Express", "2007", 120)
    ]
    
    print(f"Created {len(citations)} test citations:")
    for i, c in enumerate(citations, 1):
        print(f"  {i}. {c.citation} - {c.extracted_case_name} ({c.extracted_date})")
    
    # Step 2: Test clustering function
    try:
        from unified_citation_clustering import cluster_citations_unified
        
        print(f"\nCalling cluster_citations_unified...")
        print(f"  Citations: {len(citations)}")
        print(f"  Text: {test_text}")
        print(f"  Verification: False")
        
        result = cluster_citations_unified(citations, test_text, enable_verification=False)
        
        print(f"\nResult type: {type(result)}")
        print(f"Result: {result}")
        
        if isinstance(result, list):
            print(f"Number of clusters: {len(result)}")
            for i, cluster in enumerate(result, 1):
                print(f"  Cluster {i}: {cluster}")
        elif isinstance(result, dict):
            clusters = result.get('clusters', [])
            print(f"Number of clusters in dict: {len(clusters)}")
            for i, cluster in enumerate(clusters, 1):
                print(f"  Cluster {i}: {cluster}")
        else:
            print("Unexpected result type")
            
    except Exception as e:
        print(f"Clustering failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    test_clustering_direct()

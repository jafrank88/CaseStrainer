#!/usr/bin/env python3
"""
Simple Clustering Test
Test just the clustering component to see the specific error
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class SimpleCitation:
    """Simple citation object for testing."""
    def __init__(self, citation, case_name=None, year=None):
        self.citation = citation
        self.case_name = case_name
        self.extracted_case_name = case_name
        self.year = year
        self.extracted_date = year
        self.canonical_name = None
        self.canonical_date = None
        self.verified = False
        self.court = None
        self.confidence = 0.0
        self.method = 'test'
        self.pattern = None
        self.context = ''
        self.start_index = 0
        self.end_index = 0
        self.is_parallel = False
        self.metadata = {}
        self.parallel_citations = []

def test_clustering():
    """Test clustering with simple data."""
    print("🔍 SIMPLE CLUSTERING TEST")
    print("-" * 40)
    
    # Create test citation objects with proper structure
    test_citations = [
        SimpleCitation('578 U.S. 5', 'Luis v. United States', '2016'),
        SimpleCitation('136 S. Ct. 1083', 'Luis v. United States', '2016'),
        SimpleCitation('194 L. Ed. 2d 256', 'Luis v. United States', '2016')
    ]
    
    print(f"Input citations: {len(test_citations)}")
    for citation in test_citations:
        print(f"  - {citation.citation} ({citation.case_name}, {citation.year})")
    
    try:
        print("\nTrying to import UnifiedCitationClusterer...")
        from src.unified_citation_clustering import UnifiedCitationClusterer
        print("✅ Import successful")
        
        print("\nCreating clusterer instance...")
        clusterer = UnifiedCitationClusterer()
        print("✅ Instance created")
        
        print("\nCalling cluster_citations...")
        clusters = clusterer.cluster_citations(test_citations)
        print(f"✅ Clustering completed, got {len(clusters)} clusters")
        
        for i, cluster in enumerate(clusters):
            print(f"  Cluster {i+1}:")
            print(f"    Citations: {len(cluster.get('citations', []))}")
            print(f"    Case name: {cluster.get('case_name', 'N/A')}")
            print(f"    Year: {cluster.get('year', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Clustering failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_clustering()
    sys.exit(0 if success else 1)

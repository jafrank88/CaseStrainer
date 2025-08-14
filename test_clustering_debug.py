#!/usr/bin/env python3
"""
Minimal Clustering Debug Test
Debug the exact clustering failure in step-by-step test
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

def main():
    """Debug clustering step by step."""
    print("🔍 CLUSTERING DEBUG TEST")
    print("-" * 40)
    
    try:
        print("Step 1: Creating citation objects...")
        test_citations = [
            SimpleCitation('578 U.S. 5', 'Luis v. United States', '2016'),
            SimpleCitation('136 S. Ct. 1083', 'Luis v. United States', '2016'),
            SimpleCitation('194 L. Ed. 2d 256', 'Luis v. United States', '2016')
        ]
        print(f"✅ Created {len(test_citations)} citation objects")
        
        print("\nStep 2: Importing UnifiedCitationClusterer...")
        from src.unified_citation_clustering import UnifiedCitationClusterer
        print("✅ Import successful")
        
        print("\nStep 3: Creating clusterer instance...")
        clusterer = UnifiedCitationClusterer()
        print("✅ Clusterer created")
        
        print("\nStep 4: Calling cluster_citations...")
        clusters = clusterer.cluster_citations(test_citations)
        print(f"✅ Got {len(clusters)} clusters")
        
        print("\nStep 5: Examining cluster results...")
        for i, cluster in enumerate(clusters):
            print(f"  Cluster {i+1}:")
            print(f"    Type: {type(cluster)}")
            print(f"    Keys: {list(cluster.keys()) if isinstance(cluster, dict) else 'Not a dict'}")
            if isinstance(cluster, dict):
                citations = cluster.get('citations', [])
                print(f"    Citations count: {len(citations)}")
                print(f"    Case name: {cluster.get('case_name', 'N/A')}")
                print(f"    Year: {cluster.get('year', 'N/A')}")
                if citations:
                    print(f"    First citation type: {type(citations[0])}")
                    if hasattr(citations[0], 'citation'):
                        print(f"    First citation text: {citations[0].citation}")
        
        return True
        
    except Exception as e:
        print(f"❌ Clustering debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

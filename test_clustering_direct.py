"""
Direct test of clustering validation without API
"""
import sys
sys.path.insert(0, 'd:\\dev\\casestrainer\\src')
sys.path.insert(0, 'd:\\dev\\casestrainer')

from src.unified_clustering_master import UnifiedClusteringMaster

# Create test citations with year mismatches
class MockCitation:
    def __init__(self, citation, extracted_date, canonical_date, extracted_case_name, canonical_name):
        self.citation = citation
        self.extracted_date = extracted_date
        self.canonical_date = canonical_date
        self.extracted_case_name = extracted_case_name
        self.canonical_name = canonical_name
        self.cluster_case_name = None
        self.cluster_year = None

print("=" * 80)
print("TESTING CLUSTERING VALIDATION DIRECTLY")
print("=" * 80)

# Test 1: Citations with 19-year gap (should be separated)
print("\nTest 1: 19-year gap (1997 vs 2016)")
print("-" * 80)

citations_test1 = [
    MockCitation("521 U.S. 811", "1997", "1997-06-23", "Branson v. Wash. Fine Wine & Spirits", "Branson v. Wash. Fine Wine & Spirits"),
    MockCitation("136 S. Ct. 1540", "2016", "2016-05-16", "Spokeo, Inc. v. Robins", "Spokeo, Inc. v. Robins")
]

clusterer = UnifiedClusteringMaster({'debug_mode': True})
clusters = clusterer.cluster_citations(citations_test1, original_text="", enable_verification=False)

print(f"Result: {len(clusters)} clusters created")
for i, cluster in enumerate(clusters):
    print(f"  Cluster {i+1}: {cluster.get('size')} citations")
    for cit in cluster.get('citations', []):
        year = getattr(cit, 'extracted_date', 'N/A')
        print(f"    - {getattr(cit, 'citation', 'N/A')} ({year})")

if len(clusters) == 2:
    print("✅ PASSED: Created 2 separate clusters")
else:
    print(f"❌ FAILED: Expected 2 clusters, got {len(clusters)}")

# Test 2: Citations with same year and case name (should be clustered)
print("\nTest 2: Same year and case (should cluster)")
print("-" * 80)

citations_test2 = [
    MockCitation("183 Wash.2d 649", "2015", "2015-07-16", "Lopez Demetrio v. Sakuma Bros. Farms", "Lopez Demetrio v. Sakuma Bros. Farms"),
    MockCitation("355 P.3d 258", "2015", "2015-07-16", "Lopez Demetrio v. Sakuma Bros. Farms", "Lopez Demetrio v. Sakuma Bros. Farms")
]

clusters = clusterer.cluster_citations(citations_test2, original_text="", enable_verification=False)

print(f"Result: {len(clusters)} clusters created")
for i, cluster in enumerate(clusters):
    print(f"  Cluster {i+1}: {cluster.get('size')} citations")
    for cit in cluster.get('citations', []):
        year = getattr(cit, 'extracted_date', 'N/A')
        print(f"    - {getattr(cit, 'citation', 'N/A')} ({year})")

if len(clusters) == 1 and clusters[0].get('size') == 2:
    print("✅ PASSED: Created 1 cluster with 2 citations")
else:
    print(f"❌ FAILED: Expected 1 cluster with 2 citations, got {len(clusters)} clusters")

# Test 3: Different case names (should be separated)
print("\nTest 3: Different case names (should separate)")
print("-" * 80)

citations_test3 = [
    MockCitation("159 Wash.2d 652", "2007", "2007-02-15", "Tingey v. Haisch", "Tingey v. Haisch"),
    MockCitation("148 Wash.2d 723", "2003", "2003-02-20", "State v. Delgado", "State v. Delgado")
]

clusters = clusterer.cluster_citations(citations_test3, original_text="", enable_verification=False)

print(f"Result: {len(clusters)} clusters created")
for i, cluster in enumerate(clusters):
    print(f"  Cluster {i+1}: {cluster.get('size')} citations")
    for cit in cluster.get('citations', []):
        name = getattr(cit, 'extracted_case_name', 'N/A')
        print(f"    - {getattr(cit, 'citation', 'N/A')} ({name})")

if len(clusters) == 2:
    print("✅ PASSED: Created 2 separate clusters")
else:
    print(f"❌ FAILED: Expected 2 clusters, got {len(clusters)}")

print("\n" + "=" * 80)
print("DIRECT CLUSTERING TEST COMPLETE")
print("=" * 80)

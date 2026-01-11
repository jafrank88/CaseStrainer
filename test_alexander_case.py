"""Test the Alexander v. Las Vegas case with different WL years"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_clustering_master import UnifiedClusteringMaster

# Create mock citation objects
class MockCitation:
    def __init__(self, citation_text, extracted_name, extracted_date, start_index):
        self.citation = citation_text
        self.extracted_case_name = extracted_name
        self.extracted_date = extracted_date
        self.start_index = start_index
        self.end_index = start_index + len(citation_text)
        
        # No court metadata for WL citations (proprietary)
        class Metadata:
            def __init__(self):
                self.court = None
                self.plaintiff = None
                self.defendant = None
        
        self.metadata = Metadata()

print("=" * 70)
print("TEST: Alexander v. Las Vegas - Different WL Years")
print("=" * 70)

# Citation 1: 2021 WL 3622166
cit1 = MockCitation(
    citation_text="2021 WL 3622166",
    extracted_name="Alexander v. Las Vegas Metro. Police Dep't",
    extracted_date="2021",  # Year from WL citation
    start_index=5000
)

# Citation 2: 2025 WL 1410708
cit2 = MockCitation(
    citation_text="2025 WL 1410708",
    extracted_name="Alexander v. Las Vegas Metro. Police Dep't",
    extracted_date="2025",  # Year from WL citation
    start_index=5100  # Close proximity
)

clusterer = UnifiedClusteringMaster()
result = clusterer._are_citations_parallel_pair(cit1, cit2, "")

print(f"\nCitation 1: {cit1.citation}")
print(f"  Extracted Name: {cit1.extracted_case_name}")
print(f"  Extracted Date: {cit1.extracted_date}")

print(f"\nCitation 2: {cit2.citation}")
print(f"  Extracted Name: {cit2.extracted_case_name}")
print(f"  Extracted Date: {cit2.extracted_date}")

print(f"\n{'=' * 70}")
print(f"Should these citations cluster together? {result}")
print(f"Expected: False (same reporter WL + different years: 2021 vs 2025)")
print(f"{'=' * 70}")

if not result:
    print("\n✅ SUCCESS! The clustering fix is working correctly!")
    print("   These citations will NOT be clustered together.")
    print("\n   Reasons they were kept separate:")
    print("   1. Same reporter: Both are WL citations")
    print("   2. Different years: 2021 vs 2025 (4-year difference)")
else:
    print("\n❌ FAILURE! These citations are still clustering together.")
    print("   This is a problem - citations from different years should not cluster.")
    print("\n   Possible causes:")
    print("   1. Same reporter check not working for WL citations")
    print("   2. Year validation not being applied")
    print("   3. extracted_date not being set correctly")

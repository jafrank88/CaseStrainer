"""Test the actual Mastriano/Doe case from user's example"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_clustering_master import UnifiedClusteringMaster

# Create mock citation objects matching the real case
class MockCitation:
    def __init__(self, citation_text, court, plaintiff, defendant, extracted_name, extracted_date, start_index):
        self.citation = citation_text
        self.extracted_case_name = extracted_name
        self.extracted_date = extracted_date
        self.start_index = start_index
        self.end_index = start_index + len(citation_text)
        
        class Metadata:
            def __init__(self, court, plaintiff, defendant):
                self.court = court
                self.plaintiff = plaintiff
                self.defendant = defendant
        
        self.metadata = Metadata(court, plaintiff, defendant)

print("=" * 70)
print("REAL-WORLD TEST: Mastriano v. Gregory vs Doe v. Columbia")
print("=" * 70)

# Real Citation 1: 2024 WL 4149252 (Doe v. Columbia, NYSD)
cit1 = MockCitation(
    citation_text="2024 WL 4149252",
    court="nysd",  # Southern District of New York
    plaintiff="Doe",
    defendant="Columbia Univ., No. 23 CIV. 10393 (DEH)",
    extracted_name="Doe v. Columbia University",
    extracted_date="2024",
    start_index=2600  # Approximate position from logs
)

# Real Citation 2: 2024 WL 4003343 (Mastriano v. Gregory, OKWD)
cit2 = MockCitation(
    citation_text="2024 WL 4003343",
    court="okwd",  # Western District of Oklahoma
    plaintiff="Mastriano",
    defendant="Gregory, No. CIV-24-567-F",
    extracted_name="Mastriano v. Gregory",
    extracted_date="2024",
    start_index=2800  # Close proximity (within 200 chars)
)

clusterer = UnifiedClusteringMaster()
result = clusterer._are_citations_parallel_pair(cit1, cit2, "")

print(f"\nCitation 1: {cit1.citation}")
print(f"  Court: {cit1.metadata.court}")
print(f"  Plaintiff: {cit1.metadata.plaintiff}")
print(f"  Defendant: {cit1.metadata.defendant}")
print(f"  Extracted Name: {cit1.extracted_case_name}")

print(f"\nCitation 2: {cit2.citation}")
print(f"  Court: {cit2.metadata.court}")
print(f"  Plaintiff: {cit2.metadata.plaintiff}")
print(f"  Defendant: {cit2.metadata.defendant}")
print(f"  Extracted Name: {cit2.extracted_case_name}")

print(f"\n{'=' * 70}")
print(f"Should these citations cluster together? {result}")
print(f"Expected: False (different courts + different parties + different names)")
print(f"{'=' * 70}")

if not result:
    print("\n✅ SUCCESS! The clustering fix is working correctly!")
    print("   These citations will NOT be clustered together.")
    print("\n   Reasons they were kept separate:")
    print("   1. Different courts: nysd vs okwd")
    print("   2. Different plaintiffs: Doe vs Mastriano")
    print("   3. Different defendants: Columbia Univ. vs Gregory")
    print("   4. Different extracted names")
else:
    print("\n❌ FAILURE! These citations are still clustering together.")
    print("   The fix needs more work.")

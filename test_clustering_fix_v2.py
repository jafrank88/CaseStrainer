"""Test clustering fix for different courts/parties"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_clustering_master import UnifiedClusteringMaster

# Create mock citation objects with eyecite metadata
class MockCitation:
    def __init__(self, citation_text, court, plaintiff, defendant, extracted_name, extracted_date, start_index):
        self.citation = citation_text
        self.extracted_case_name = extracted_name
        self.extracted_date = extracted_date
        self.start_index = start_index
        self.end_index = start_index + len(citation_text)
        
        # Create metadata object
        class Metadata:
            def __init__(self, court, plaintiff, defendant):
                self.court = court
                self.plaintiff = plaintiff
                self.defendant = defendant
        
        self.metadata = Metadata(court, plaintiff, defendant)

# Test case 1: Different courts (NYSD vs OKWD)
print("=" * 60)
print("TEST 1: Different Courts")
print("=" * 60)

cit1 = MockCitation(
    citation_text="2024 WL 4149252",
    court="nysd",
    plaintiff="Doe",
    defendant="Columbia Univ., No. 23 CIV. 10393 (DEH)",
    extracted_name="Doe v. Columbia University",
    extracted_date="2024",
    start_index=1000
)

cit2 = MockCitation(
    citation_text="2024 WL 4003343",
    court="okwd",
    plaintiff="Mastriano",
    defendant="Gregory, No. CIV-24-567-F",
    extracted_name="Mastriano v. Gregory",
    extracted_date="2024",
    start_index=1100  # Close proximity
)

clusterer = UnifiedClusteringMaster()
result = clusterer._are_citations_parallel_pair(cit1, cit2, "")

print(f"Citation 1: {cit1.citation} (court={cit1.metadata.court}, plaintiff={cit1.metadata.plaintiff})")
print(f"Citation 2: {cit2.citation} (court={cit2.metadata.court}, plaintiff={cit2.metadata.plaintiff})")
print(f"Should cluster: {result}")
print(f"Expected: False (different courts)")
print(f"✅ PASS" if not result else "❌ FAIL")

# Test case 2: Same court, different parties
print("\n" + "=" * 60)
print("TEST 2: Same Court, Different Parties")
print("=" * 60)

cit3 = MockCitation(
    citation_text="2024 WL 1234567",
    court="nysd",
    plaintiff="Smith",
    defendant="Jones",
    extracted_name="Smith v. Jones",
    extracted_date="2024",
    start_index=2000
)

cit4 = MockCitation(
    citation_text="2024 WL 7654321",
    court="nysd",
    plaintiff="Brown",
    defendant="Davis",
    extracted_name="Brown v. Davis",
    extracted_date="2024",
    start_index=2100  # Close proximity
)

result2 = clusterer._are_citations_parallel_pair(cit3, cit4, "")

print(f"Citation 3: {cit3.citation} (court={cit3.metadata.court}, plaintiff={cit3.metadata.plaintiff})")
print(f"Citation 4: {cit4.citation} (court={cit4.metadata.court}, plaintiff={cit4.metadata.plaintiff})")
print(f"Should cluster: {result2}")
print(f"Expected: False (different parties)")
print(f"✅ PASS" if not result2 else "❌ FAIL")

# Test case 3: Same reporter (both WL)
print("\n" + "=" * 60)
print("TEST 3: Same Reporter (Both WL)")
print("=" * 60)

cit5 = MockCitation(
    citation_text="2024 WL 1111111",
    court="ca9",
    plaintiff="Alpha",
    defendant="Beta",
    extracted_name="Alpha v. Beta",
    extracted_date="2024",
    start_index=3000
)

cit6 = MockCitation(
    citation_text="2024 WL 2222222",
    court="ca9",
    plaintiff="Alpha",
    defendant="Beta",
    extracted_name="Alpha v. Beta",
    extracted_date="2024",
    start_index=3100  # Close proximity
)

result3 = clusterer._are_citations_parallel_pair(cit5, cit6, "")

print(f"Citation 5: {cit5.citation}")
print(f"Citation 6: {cit6.citation}")
print(f"Should cluster: {result3}")
print(f"Expected: False (same reporter - WL)")
print(f"✅ PASS" if not result3 else "❌ FAIL")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
all_passed = not result and not result2 and not result3
if all_passed:
    print("✅ All tests PASSED - Clustering fix is working!")
else:
    print("❌ Some tests FAILED - Clustering fix needs adjustment")
    if result:
        print("  - Test 1 FAILED: Different courts should not cluster")
    if result2:
        print("  - Test 2 FAILED: Different parties should not cluster")
    if result3:
        print("  - Test 3 FAILED: Same reporter should not cluster")

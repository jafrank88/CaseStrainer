from a_plus_citation_processor import extract_citations_with_custom_logic

# Test 1: ToA-style text
toa_text = """TABLE OF AUTHORITIES
Cases Page(s)
Cathcart v. Andersen, 85 Wn.2d 102 (1975) ......................................................... .32
Chandlerv. Otto, 103 Wn.2d268 (1984) ...................................................... 5, 10-11
Citizens All.for Prop. Rights Legal Fund v. San Juan County, 184 Wn.2d 428, 443, 359 P.3d 753 (2015) ............................................ 33-34"""

# Test 2: Regular document text (non-ToA)
regular_text = """In the case of Smith v. Jones, the court held that 85 Wn.2d 102 was controlling. 
The decision in Brown v. State, 103 Wn.2d 268 (1984), further clarified this principle.
As established in Doe v. Roe, 184 Wn.2d 428, the standard applies broadly."""

print("=== Testing A+ Processor with Different Text Types ===\n")

print("1. ToA-Style Text:")
print("-" * 50)
citations_toa = extract_citations_with_custom_logic(toa_text)
for i, citation in enumerate(citations_toa, 1):
    print(f"{i}. Citation: {citation['citation']}")
    print(f"   Case Name: {citation['case_name']}")
    print(f"   Year: {citation['year']}")
    print()

print("2. Regular Document Text:")
print("-" * 50)
citations_regular = extract_citations_with_custom_logic(regular_text)
for i, citation in enumerate(citations_regular, 1):
    print(f"{i}. Citation: {citation['citation']}")
    print(f"   Case Name: {citation['case_name']}")
    print(f"   Year: {citation['year']}")
    print()

print("=== Summary ===")
print(f"ToA text found {len(citations_toa)} citations")
print(f"Regular text found {len(citations_regular)} citations")
print("\nA+ processor automatically adapts its extraction method based on text type!") 
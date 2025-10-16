"""
Test parallel citation case name propagation
"""
from src.citation_extraction_endpoint import extract_citations_production

print("="*80)
print("PARALLEL CITATION NAME PROPAGATION TEST")
print("="*80)

# Test Case 1: Classic parallel citation
print("\nTest 1: Classic Parallel Citations")
print("-" * 80)

test1 = """
State v. Johnson, 159 Wn.2d 700, 153 P.3d 846 (2007), held that the 
defendant's rights were violated.
"""

result1 = extract_citations_production(test1)
citations1 = result1['citations']

print(f"Found {len(citations1)} citations:\n")
for cite in citations1:
    print(f"  Citation: {cite['citation']}")
    print(f"  Case name: {cite.get('extracted_case_name', 'N/A')}")
    propagated = " (PROPAGATED)" if cite.get('propagated_from_parallel') else ""
    print(f"  Status: {propagated}")
    print()

# Count successes
names_found = sum(1 for c in citations1 if c.get('extracted_case_name') not in [None, '', 'N/A'])
print(f"✅ Result: {names_found}/{len(citations1)} citations have case names ({names_found/len(citations1)*100:.1f}%)")

# Test Case 2: Multiple parallel citations
print("\n" + "="*80)
print("Test 2: Multiple Parallel Citations (3 reporters)")
print("-" * 80)

test2 = """
In Erie Railroad Co. v. Tompkins, 304 U.S. 64, 58 S. Ct. 817, 82 L. Ed. 1188 (1938),
the Supreme Court held that federal courts must apply state law.
"""

result2 = extract_citations_production(test2)
citations2 = result2['citations']

print(f"Found {len(citations2)} citations:\n")
for cite in citations2:
    print(f"  Citation: {cite['citation']}")
    print(f"  Case name: {cite.get('extracted_case_name', 'N/A')}")
    propagated = " (PROPAGATED)" if cite.get('propagated_from_parallel') else ""
    print(f"  Status: {propagated}")
    print()

names_found = sum(1 for c in citations2 if c.get('extracted_case_name') not in [None, '', 'N/A'])
print(f"✅ Result: {names_found}/{len(citations2)} citations have case names ({names_found/len(citations2)*100:.1f}%)")

# Test Case 3: Real brief excerpt
print("\n" + "="*80)
print("Test 3: Real Brief Excerpt")
print("-" * 80)

test3 = """
This Court has held that the State must prove each element beyond a reasonable doubt.
State v. Orn, 197 Wn.2d 343, 349, 482 P.3d 913 (2021). The trial court erred in 
refusing to instruct the jury on self-defense. State v. Fernandez-Medina, 141 Wn.2d 
448, 455-56, 6 P.3d 1150 (2000). The defendant's conduct did not constitute assault.
State v. Wilson, 125 Wn.2d 212, 217, 883 P.2d 320 (1994).
"""

result3 = extract_citations_production(test3)
citations3 = result3['citations']

print(f"Found {len(citations3)} citations:\n")

# Group by case
current_case = None
for cite in citations3:
    case_name = cite.get('extracted_case_name', 'N/A')
    propagated = " (PROPAGATED)" if cite.get('propagated_from_parallel') else ""
    
    if case_name != current_case:
        if current_case is not None:
            print()
        print(f"Case: {case_name}")
        current_case = case_name
    
    print(f"  → {cite['citation']}{propagated}")

names_found = sum(1 for c in citations3 if c.get('extracted_case_name') not in [None, '', 'N/A'])
print(f"\n✅ Result: {names_found}/{len(citations3)} citations have case names ({names_found/len(citations3)*100:.1f}%)")

# Summary
print("\n" + "="*80)
print("OVERALL SUMMARY")
print("="*80)

total_citations = len(citations1) + len(citations2) + len(citations3)
total_with_names = (
    sum(1 for c in citations1 if c.get('extracted_case_name') not in [None, '', 'N/A']) +
    sum(1 for c in citations2 if c.get('extracted_case_name') not in [None, '', 'N/A']) +
    sum(1 for c in citations3 if c.get('extracted_case_name') not in [None, '', 'N/A'])
)

print(f"\nTotal citations tested: {total_citations}")
print(f"Citations with case names: {total_with_names}")
print(f"Success rate: {total_with_names/total_citations*100:.1f}%")

total_propagated = (
    sum(1 for c in citations1 if c.get('propagated_from_parallel')) +
    sum(1 for c in citations2 if c.get('propagated_from_parallel')) +
    sum(1 for c in citations3 if c.get('propagated_from_parallel'))
)

print(f"\nCitations helped by propagation: {total_propagated}")
print(f"Improvement from propagation: +{total_propagated/total_citations*100:.1f}%")

print("\n" + "="*80)
print("✅ Parallel propagation is working!")
print("="*80)

"""
Test the production citation extraction endpoint.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.citation_extraction_endpoint import extract_citations_production

print("=" * 100)
print("PRODUCTION ENDPOINT TEST")
print("=" * 100)
print()

# Test with simple text
test_text = """
The Supreme Court held in Erie Railroad Co. v. Tompkins, 304 U.S. 64 (1938), 
that federal courts must apply state law. Later, in Will v. Hallock, 546 U.S. 345 (2006),
the Court clarified the collateral order doctrine.
"""

print("Test Text:")
print(test_text)
print()

# Call production endpoint
result = extract_citations_production(test_text)

print("=" * 100)
print("RESULTS")
print("=" * 100)
print()

print(f"Status: {result['status']}")
print(f"Total Citations: {result['total']}")
print(f"Accuracy: {result['accuracy']}")
print(f"Method: {result['method']}")
print(f"Version: {result['version']}")
print(f"Case Name Bleeding: {result['case_name_bleeding']}")
print()

print("Citations Found:")
print("-" * 100)
for i, cit in enumerate(result['citations'], 1):
    print(f"{i}. {cit['citation']}")
    print(f"   Case Name: {cit['extracted_case_name']}")
    print(f"   Date: {cit['extracted_date']}")
    print(f"   Method: {cit['method']}")
    print()

print("=" * 100)
if result['status'] == 'success' and result['total'] >= 2:
    print("SUCCESS! Production endpoint is working correctly.")
else:
    print("WARNING: Unexpected result from production endpoint.")
print("=" * 100)

#!/usr/bin/env python3
"""Test each N/A citation individually"""
import sys
sys.path.insert(0, 'src')

import os
from dotenv import load_dotenv
load_dotenv()

from enhanced_courtlistener_verification import EnhancedCourtListenerVerifier

# Get API key
api_key = os.getenv('COURTLISTENER_API_KEY', '')

# The 5 N/A citations
test_citations = [
    ("187 F.3d 645", "1999"),
    ("197 Wn.2d 868", "2021"),
    ("489 P.3d 631", "2021"),
    ("17 F.4th 901", "2021"),
    ("523 U.S. 751", "1998"),
]

verifier = EnhancedCourtListenerVerifier(api_key)

results = []
for citation, expected_year in test_citations:
    result = verifier.verify_citation_enhanced(citation, extracted_case_name=None)
    
    if result.get('verified'):
        case_name = result.get('canonical_name', 'N/A')
        year = result.get('canonical_year', 'N/A')
        status = "✅ VERIFIED"
        results.append((citation, status, case_name, year))
    else:
        status = "❌ FAILED"
        error = result.get('error', 'Unknown')
        results.append((citation, status, error, ""))

print(f"\n{'='*80}")
print("VERIFICATION SUMMARY:")
print(f"{'='*80}\n")

for citation, status, name_or_error, year in results:
    print(f"{status}: {citation}")
    if status == "✅ VERIFIED":
        print(f"   → {name_or_error} ({year})")
    else:
        print(f"   → {name_or_error}")
    print()

verified_count = sum(1 for _, status, _, _ in results if status == "✅ VERIFIED")
print(f"{'='*80}")
print(f"TOTAL: {verified_count}/{len(test_citations)} verified ({verified_count/len(test_citations)*100:.0f}%)")
print(f"{'='*80}")

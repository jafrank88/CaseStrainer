#!/usr/bin/env python3
"""Test CourtListener verification for the 5 N/A citations"""
import sys
sys.path.insert(0, 'src')

import os
from dotenv import load_dotenv
load_dotenv()

from enhanced_courtlistener_verification import EnhancedCourtListenerVerifier

# Get API key
api_key = os.getenv('COURTLISTENER_API_KEY', '')
if not api_key:
    print("ERROR: No CourtListener API key found!")
    sys.exit(1)

print(f"Using API key: {api_key[:10]}...")

# The 5 N/A citations
test_citations = [
    "187 F.3d 645",  # 1999
    "197 Wn.2d 868",  # 2021 - Should be "In re Dependency of G.J.A."
    "489 P.3d 631",   # 2021 - Parallel to 197 Wn.2d 868
    "17 F.4th 901",   # 2021
    "523 U.S. 751",   # Should be "Kiowa Tribe v. Mfg. Techs., Inc."
]

verifier = EnhancedCourtListenerVerifier(api_key)

print(f"\n{'='*80}")
print("TESTING COURTLISTENER VERIFICATION FOR 5 N/A CITATIONS")
print(f"{'='*80}\n")

for citation in test_citations:
    print(f"\n{'='*80}")
    print(f"Verifying: {citation}")
    print(f"{'='*80}\n")
    
    # Try verification
    result = verifier.verify_citation_enhanced(citation, extracted_case_name=None)
    
    if result.get('verified'):
        case_name = result.get('canonical_name', 'N/A')
        year = result.get('canonical_year', 'N/A')
        print(f"✅ VERIFIED: '{case_name}' ({year})")
        print(f"   Method: {result.get('verification_method', 'unknown')}")
        print(f"   Confidence: {result.get('confidence', 0)}")
    else:
        print(f"❌ VERIFICATION FAILED")
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print(f"\n{'-'*80}\n")

print(f"\n{'='*80}")
print("VERIFICATION TESTING COMPLETE")
print(f"{'='*80}")

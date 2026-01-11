"""
Test script to investigate F.2d, F.3d, and F.4th verification issues
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("F.2d, F.3d, F.4th VERIFICATION INVESTIGATION")
print("=" * 60)

# Test citations from the web interface
test_citations = [
    "146 F.4th 165",      # From Giuffre v. Maxwell
    "585 F.3d 1061",      # From Bond v. Utreras
    "750 F.3d 776",       # From Courthouse News Serv. v. Planet
    "684 F.3d 286",       # From C.L. Union v. N.Y. Transit Auth
    "710 F.2d 1165",      # From Brown & Williamson Tobacco Corp. v. F.T.C
    "732 F.2d 1302",      # From Brown & Williamson Tobacco Corp. v. F.T.C (second)
    "855 F.2d 569",       # From In re Search Warrant
    "749 F.3d 246",       # From Doe v. Pub. Citizen
    "24 F.3d 893",        # From Grove Fresh Distributors v. Everfresh Juice Co.
    "963 F.3d 130",       # From League of Women Voters v. Brian Newby
    "2 F.4th 318",        # From Courthouse News Service v. George Schaefer
    "28 F.4th 292",       # From In re L.A. Times Commc'ns LLC
]

print("\nTesting individual verification sources:")
print("-" * 50)

from src.enhanced_fallback_verifier import EnhancedFallbackVerifier

verifier = EnhancedFallbackVerifier()

for cit in test_citations:
    print(f"\n{cit}:")
    print("-" * 30)
    
    # Test CourtListener API
    try:
        result = verifier._verify_with_courtlistener_lookup(cit, timeout=5)
        if result and result.get('status') == 'found':
            print(f"  CourtListener: ✅ FOUND - {result.get('case_name', 'N/A')}")
        else:
            print(f"  CourtListener: ❌ Not found")
    except Exception as e:
        print(f"  CourtListener: ❌ Error - {str(e)[:50]}")
    
    # Test Justia
    try:
        result = verifier._verify_with_justia(cit, timeout=5)
        if result and result.get('found'):
            print(f"  Justia: ✅ FOUND - {result.get('name', 'N/A')}")
        else:
            print(f"  Justia: ❌ Not found")
    except Exception as e:
        print(f"  Justia: ❌ Error - {str(e)[:50]}")
    
    # Test Google Scholar
    try:
        result = verifier._verify_with_google_scholar(cit, timeout=5)
        if result and result.get('found'):
            print(f"  Google Scholar: ✅ FOUND - {result.get('title', 'N/A')}")
        else:
            print(f"  Google Scholar: ❌ Not found")
    except Exception as e:
        print(f"  Google Scholar: ❌ Error - {str(e)[:50]}")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)

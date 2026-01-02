"""
Verify the specific problematic citations from the test results
"""

import requests
import json

BASE_URL = "http://localhost:8080/casestrainer"  # Using Nginx proxy with /casestrainer prefix

def test_citation_text(text, description):
    """Test a small piece of text with specific citations"""
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"{'='*80}")
    print(f"Text: {text[:200]}...")
    
    response = requests.post(
        f"{BASE_URL}/api/analyze",
        json={"text": text},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        citations = data.get('citations', [])
        
        print(f"\n✅ Found {len(citations)} citation(s)")
        
        for cit in citations:
            print(f"\n  Citation: {cit.get('citation')}")
            print(f"    Extracted Name: {cit.get('extracted_case_name')}")
            print(f"    Canonical Name: {cit.get('canonical_name')}")
            print(f"    Verified: {cit.get('verified')}")
            print(f"    true_by_parallel: {cit.get('true_by_parallel')}")
            print(f"    Source: {cit.get('source')}")
            if cit.get('name_mismatch'):
                print(f"    ⚠️  NAME MISMATCH!")
        
        return citations
    else:
        print(f"\n❌ Error: HTTP {response.status_code}")
        print(response.text)
        return []

# Test Case 1: 636 F.2d 1267 - Should be Env't Def Fund, NOT Erickson
print("\n" + "="*80)
print("TESTING PROBLEMATIC CITATIONS")
print("="*80)

test1 = """
Environmental Defense Fund, Inc. v. Environmental Protection Agency, 636 F.2d 1267.
This case addressed environmental regulations and agency procedures.
"""

citations1 = test_citation_text(test1, "636 F.2d 1267 - Should be Env't Def Fund")

# Test Case 2: 498 U.S. 941 - Should find Christine Mahne case
test2 = """
Christine Mahne v. Ford Motor Company Donald Petersen and Harold MacDonald, 498 U.S. 941 (1990).
This case involved product liability claims against Ford Motor Company.
"""

citations2 = test_citation_text(test2, "498 U.S. 941 - Should find Christine Mahne")

# Test Case 3: Singh citations - WL should get true_by_parallel
test3 = """
Singh v. Edwards Lifesciences Corp., 151 Wn. App. 137, 210 P.3d 337 (2009).
The same case is also reported at 2011 WL 3298912.
This Washington case addressed medical device liability.
"""

citations3 = test_citation_text(test3, "Singh - WL should be true_by_parallel")

# Test Case 4: Recent 2024 citations
test4 = """
Erickson v. Pharmacia LLC, 548 P.3d 226, 3 Wn.3d 1018 (2024).
This is a recent Washington Supreme Court case from 2024.
"""

citations4 = test_citation_text(test4, "Erickson 2024 - Recent citations")

print("\n" + "="*80)
print("VERIFICATION SUMMARY")
print("="*80)

def check_result(citations, expected_name_fragment, test_name):
    """Check if any citation contains the expected name"""
    if not citations:
        print(f"❌ {test_name}: No citations found")
        return False
    
    found = False
    for cit in citations:
        canonical = cit.get('canonical_name') or ''
        extracted = cit.get('extracted_case_name') or ''
        
        if expected_name_fragment.lower() in canonical.lower() or expected_name_fragment.lower() in extracted.lower():
            found = True
            break
    
    if found:
        print(f"✅ {test_name}: Found expected case name")
    else:
        print(f"❌ {test_name}: Expected '{expected_name_fragment}' not found")
        print(f"   Got: {[c.get('canonical_name') or c.get('extracted_case_name') for c in citations]}")
    
    return found

check_result(citations1, "Environmental Defense", "636 F.2d 1267")
check_result(citations2, "Mahne", "498 U.S. 941")

# Check Singh true_by_parallel
singh_wl_verified = False
for cit in citations3:
    if "WL" in cit.get('citation', ''):
        if cit.get('true_by_parallel'):
            singh_wl_verified = True
            print(f"✅ Singh WL: true_by_parallel is set")
        else:
            print(f"❌ Singh WL: true_by_parallel NOT set")
            print(f"   WL Citation: {cit}")

check_result(citations4, "Erickson", "Erickson 2024")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)

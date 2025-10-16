"""
Standalone test for CourtListener verification API
Tests a few well-known citations to ensure the verification system is working
"""

import logging
logging.basicConfig(level=logging.INFO)

print("="*80)
print("COURTLISTENER VERIFICATION API TEST")
print("="*80)

# Test 1: Import the verification master
print("\n1. Testing import of verification master...")
try:
    from src.unified_verification_master import verify_citation_unified_master_sync
    print("   [OK] Import successful")
except Exception as e:
    print(f"   [FAIL] Import failed: {e}")
    exit(1)

# Test 2: Verify a well-known citation
print("\n2. Testing verification of well-known citations...")
test_citations = [
    {
        'citation': '304 U.S. 64',
        'case_name': 'Erie Railroad Co. v. Tompkins',
        'date': '1938',
        'expected': True  # This is a famous case, should verify
    },
    {
        'citation': '546 U.S. 345',
        'case_name': 'Will v. Hallock',
        'date': '2006',
        'expected': True
    },
    {
        'citation': '999 U.S. 999',  # Fake citation
        'case_name': 'Nonexistent v. Case',
        'date': '2099',
        'expected': False  # Should not verify
    }
]

results = []
for idx, test in enumerate(test_citations, 1):
    print(f"\n   Test {idx}: {test['citation']}")
    print(f"   Expected case: {test['case_name']}")
    print(f"   Expected date: {test['date']}")
    
    try:
        result = verify_citation_unified_master_sync(
            citation=test['citation'],
            extracted_case_name=test['case_name'],
            extracted_date=test['date'],
            timeout=10.0
        )
        
        print(f"   Result:")
        print(f"     Verified: {result.get('verified', False)}")
        print(f"     Canonical name: {result.get('canonical_name')}")
        print(f"     Canonical date: {result.get('canonical_date')}")
        print(f"     Source: {result.get('source')}")
        print(f"     Error: {result.get('error')}")
        
        verified = result.get('verified', False)
        expected = test['expected']
        
        if verified == expected:
            print(f"   [OK] PASS - Verification result matches expected ({expected})")
            results.append(('PASS', test['citation']))
        else:
            print(f"   [FAIL] FAIL - Expected {expected}, got {verified}")
            results.append(('FAIL', test['citation']))
            
    except Exception as e:
        print(f"   [ERROR] ERROR: {e}")
        results.append(('ERROR', test['citation']))
        import traceback
        traceback.print_exc()

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

passed = sum(1 for r in results if r[0] == 'PASS')
failed = sum(1 for r in results if r[0] == 'FAIL')
errors = sum(1 for r in results if r[0] == 'ERROR')

print(f"\nTests run: {len(results)}")
print(f"  PASS:  {passed}")
print(f"  FAIL:  {failed}")
print(f"  ERROR: {errors}")

if passed == len(results):
    print("\n[OK] ALL TESTS PASSED - Verification API is working correctly!")
elif passed > 0:
    print(f"\n[WARN] PARTIAL SUCCESS - {passed}/{len(results)} tests passed")
else:
    print("\n[FAIL] ALL TESTS FAILED - Verification API has issues")

print("="*80)

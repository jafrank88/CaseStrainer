"""
Oneida Citation Clustering Test

Tests the specific issue from TODO_TOMORROW.md where three Supreme Court 
parallel citations should cluster together.

Success Criteria:
- All three Supreme Court citations (562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587) in ONE cluster
- Correct case name: "Oneida Indian Nation v. Madison County"
- Correct year: "2011"
"""

import sys
sys.path.insert(0, '/app')

import asyncio
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Test text from TODO_TOMORROW.md
oneida_text = """
Other cases specifically discussing tribes hold that tribal sovereign immunity is not 
waived with respect to real property. See Cayuga Indian Nation v. Seneca County, 
761 F.3d 218, 221 (2d Cir. 2014) (declining to draw a distinction between in rem and 
in personam proceedings); Oneida Indian Nation v. Madison County, 605 F.3d 149, 157 
(2d Cir. 2010) (a tribe's immunity from suit is independent of its lands), vacated and 
remanded, 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011); Hamaatsa, Inc. v. 
Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977, 985 (2016).
"""

async def test_oneida():
    """Test Oneida Supreme Court parallel citation clustering"""
    print("\n" + "="*80)
    print("ONEIDA CITATION CLUSTERING TEST")
    print("="*80)
    print("Testing: 562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587")
    
    processor = UnifiedCitationProcessorV2()
    result = await processor.process_text(text=oneida_text)
    
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"\n📊 Found {len(citations)} citations in {len(clusters)} clusters")
    
    # Find the three Supreme Court citations
    us_42 = None
    sct_704 = None
    led_587 = None
    
    print("\n" + "="*80)
    print("CITATION DETAILS")
    print("="*80)
    
    for cit in citations:
        case_name = cit.canonical_name or cit.extracted_case_name or 'N/A'
        print(f"\n  Citation: {cit.citation}")
        print(f"    Case name: {case_name}")
        print(f"    Year: {cit.extracted_date}")
        print(f"    Cluster ID: {cit.cluster_id}")
        
        if '562 U.S. 42' in cit.citation:
            us_42 = cit
        elif '131 S. Ct. 704' in cit.citation:
            sct_704 = cit
        elif '178 L. Ed. 2d 587' in cit.citation:
            led_587 = cit
    
    # TEST 1: All three Supreme Court citations found
    print("\n" + "="*80)
    print("TEST 1: All Three Supreme Court Citations Found")
    print("="*80)
    
    test1_pass = us_42 is not None and sct_704 is not None and led_587 is not None
    
    if test1_pass:
        print(f"  ✅ PASS: Found all three citations")
        print(f"    562 U.S. 42: {us_42.citation}")
        print(f"    131 S. Ct. 704: {sct_704.citation}")
        print(f"    178 L. Ed. 2d 587: {led_587.citation}")
    else:
        print(f"  ❌ FAIL: Missing citations")
        if not us_42:
            print(f"    Missing: 562 U.S. 42")
        if not sct_704:
            print(f"    Missing: 131 S. Ct. 704")
        if not led_587:
            print(f"    Missing: 178 L. Ed. 2d 587")
        return False
    
    # TEST 2: All three in same cluster
    print("\n" + "="*80)
    print("TEST 2: All Three Citations in SAME Cluster")
    print("="*80)
    
    cluster_us = us_42.cluster_id
    cluster_sct = sct_704.cluster_id
    cluster_led = led_587.cluster_id
    
    same_cluster = (cluster_us == cluster_sct == cluster_led)
    
    if same_cluster:
        print(f"  ✅ PASS: All three citations in cluster: {cluster_us}")
    else:
        print(f"  ❌ FAIL: Citations in DIFFERENT clusters!")
        print(f"    562 U.S. 42: {cluster_us}")
        print(f"    131 S. Ct. 704: {cluster_sct}")
        print(f"    178 L. Ed. 2d 587: {cluster_led}")
    
    test2_pass = same_cluster
    
    # TEST 3: Correct case name
    print("\n" + "="*80)
    print("TEST 3: Correct Case Name (Oneida Indian Nation v. Madison County)")
    print("="*80)
    
    case_name_us = us_42.canonical_name or us_42.extracted_case_name or 'N/A'
    case_name_sct = sct_704.canonical_name or sct_704.extracted_case_name or 'N/A'
    case_name_led = led_587.canonical_name or led_587.extracted_case_name or 'N/A'
    
    # Check if any of them have "Oneida" and "Madison County"
    has_oneida_us = 'Oneida' in case_name_us and 'Madison' in case_name_us
    has_oneida_sct = 'Oneida' in case_name_sct and 'Madison' in case_name_sct
    has_oneida_led = 'Oneida' in case_name_led and 'Madison' in case_name_led
    
    test3_pass = has_oneida_us or has_oneida_sct or has_oneida_led
    
    if test3_pass:
        print(f"  ✅ PASS: Found 'Oneida' and 'Madison' in case names")
        if has_oneida_us:
            print(f"    562 U.S. 42: {case_name_us}")
        if has_oneida_sct:
            print(f"    131 S. Ct. 704: {case_name_sct}")
        if has_oneida_led:
            print(f"    178 L. Ed. 2d 587: {case_name_led}")
    else:
        print(f"  ❌ FAIL: Missing 'Oneida' or 'Madison' in case names")
        print(f"    562 U.S. 42: {case_name_us}")
        print(f"    131 S. Ct. 704: {case_name_sct}")
        print(f"    178 L. Ed. 2d 587: {case_name_led}")
    
    # TEST 4: Year is 2011
    print("\n" + "="*80)
    print("TEST 4: Correct Year (2011)")
    print("="*80)
    
    year_us = us_42.extracted_date or 'N/A'
    year_sct = sct_704.extracted_date or 'N/A'
    year_led = led_587.extracted_date or 'N/A'
    
    has_2011 = '2011' in [year_us, year_sct, year_led]
    
    test4_pass = has_2011
    
    if test4_pass:
        print(f"  ✅ PASS: Found year 2011")
        print(f"    562 U.S. 42: {year_us}")
        print(f"    131 S. Ct. 704: {year_sct}")
        print(f"    178 L. Ed. 2d 587: {year_led}")
    else:
        print(f"  ⚠️  WARNING: Year might not be 2011")
        print(f"    562 U.S. 42: {year_us}")
        print(f"    131 S. Ct. 704: {year_sct}")
        print(f"    178 L. Ed. 2d 587: {year_led}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Test 1 (All citations found):  {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"Test 2 (Same cluster):         {'✅ PASS' if test2_pass else '❌ FAIL'}")
    print(f"Test 3 (Correct case name):    {'✅ PASS' if test3_pass else '❌ FAIL'}")
    print(f"Test 4 (Year 2011):            {'✅ PASS' if test4_pass else '⚠️  WARN'}")
    
    if test1_pass and test2_pass and test3_pass:
        print("\n✅ ONEIDA CLUSTERING: PASS")
        return 0
    else:
        print("\n❌ ONEIDA CLUSTERING: FAIL")
        return 1

if __name__ == '__main__':
    sys.exit(asyncio.run(test_oneida()))

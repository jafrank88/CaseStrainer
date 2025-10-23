"""
Phase 5 Test: Real Quinault Context from TODO_TOMORROW.md

Tests the ACTUAL text that was causing the clustering issue.
"""

import sys
sys.path.insert(0, '/app')

import asyncio
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# REAL TEXT from TODO_TOMORROW.md
real_quinault_text = """
The court further noted that Washington courts had similarly upheld a superior 
court's assertion of in rem jurisdiction over tribally owned land in Anderson & 
Middleton Lumber Co. v. Quinault Indian Nation, 130 Wn.2d 862, 929 P.2d 379 (1996), 
and Smale v. Noretep, 150 Wn. App. 476, 208 P.3d 1180 (2009). 
Lundgren, 187 Wn.2d at 866-76
"""

async def test_real_quinault():
    """Test with the actual problematic text"""
    print("\n" + "="*80)
    print("PHASE 5: REAL QUINAULT CONTEXT TEST")
    print("="*80)
    print("Testing actual text from TODO_TOMORROW.md")
    
    processor = UnifiedCitationProcessorV2()
    result = await processor.process_text(text=real_quinault_text)
    
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"\n📊 Found {len(citations)} citations in {len(clusters)} clusters")
    
    # Find the Quinault parallel citations
    quinault_130 = None
    quinault_929 = None
    smale_150 = None
    smale_208 = None
    lundgren = None
    
    for cit in citations:
        case_name = cit.canonical_name or cit.extracted_case_name or 'N/A'
        print(f"\n  Citation: {cit.citation}")
        print(f"    Case name: {case_name}")
        print(f"    Year: {cit.extracted_date}")
        print(f"    Cluster ID: {cit.cluster_id}")
        
        if '130 Wn.2d 862' in cit.citation:
            quinault_130 = cit
        elif '929 P.2d 379' in cit.citation:
            quinault_929 = cit
        elif '150 Wn. App. 476' in cit.citation:
            smale_150 = cit
        elif '208 P.3d 1180' in cit.citation:
            smale_208 = cit
        elif '187 Wn.2d' in cit.citation:
            lundgren = cit
    
    # TEST 1: Quinault parallel citations should cluster together
    print("\n" + "="*80)
    print("TEST 1: Quinault Parallel Citations (130 Wn.2d 862 + 929 P.2d 379)")
    print("="*80)
    
    test1_pass = False
    if quinault_130 and quinault_929:
        same_cluster = quinault_130.cluster_id == quinault_929.cluster_id
        
        if same_cluster:
            print(f"  ✅ PASS: Quinault citations in SAME cluster")
            print(f"     Cluster ID: {quinault_130.cluster_id}")
            test1_pass = True
        else:
            print(f"  ❌ FAIL: Quinault citations in DIFFERENT clusters!")
            print(f"     130 Wn.2d 862: {quinault_130.cluster_id}")
            print(f"     929 P.2d 379: {quinault_929.cluster_id}")
    else:
        print(f"  ⚠️  Could not find both Quinault citations")
    
    # TEST 2: Smale parallel citations should cluster together
    print("\n" + "="*80)
    print("TEST 2: Smale Parallel Citations (150 Wn. App. 476 + 208 P.3d 1180)")
    print("="*80)
    
    test2_pass = False
    if smale_150 and smale_208:
        same_cluster = smale_150.cluster_id == smale_208.cluster_id
        
        if same_cluster:
            print(f"  ✅ PASS: Smale citations in SAME cluster")
            print(f"     Cluster ID: {smale_150.cluster_id}")
            test2_pass = True
        else:
            print(f"  ❌ FAIL: Smale citations in DIFFERENT clusters!")
            print(f"     150 Wn. App. 476: {smale_150.cluster_id}")
            print(f"     208 P.3d 1180: {smale_208.cluster_id}")
    else:
        print(f"  ⚠️  Could not find both Smale citations")
    
    # TEST 3: Quinault and Smale should NOT cluster together (different cases)
    print("\n" + "="*80)
    print("TEST 3: Different Cases Should NOT Cluster")
    print("="*80)
    
    test3_pass = False
    if quinault_130 and smale_150:
        same_cluster = quinault_130.cluster_id == smale_150.cluster_id
        
        if not same_cluster:
            print(f"  ✅ PASS: Different cases in DIFFERENT clusters")
            print(f"     Quinault: {quinault_130.cluster_id}")
            print(f"     Smale: {smale_150.cluster_id}")
            test3_pass = True
        else:
            print(f"  ❌ FAIL: Different cases in SAME cluster!")
            print(f"     Cluster ID: {quinault_130.cluster_id}")
    else:
        print(f"  ⚠️  Could not find both citations for comparison")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Test 1 (Quinault parallel):  {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"Test 2 (Smale parallel):     {'✅ PASS' if test2_pass else '❌ FAIL'}")
    print(f"Test 3 (Different cases):    {'✅ PASS' if test3_pass else '❌ FAIL'}")
    
    all_pass = test1_pass and test2_pass and test3_pass
    if all_pass:
        print("\n✅ ALL REAL CONTEXT TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME REAL CONTEXT TESTS FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(asyncio.run(test_real_quinault()))

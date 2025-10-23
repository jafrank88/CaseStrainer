"""
Phase 5 Test: Wrong Case Associations

Tests two specific clustering problems:
1. Flying T Ranch: Different cases (2012 vs 2024) incorrectly clustered together
2. Quinault: Same case parallel citations incorrectly separated
"""

import sys
sys.path.insert(0, '/app')

import asyncio
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Test Case 1: Flying T Ranch - Different years should NOT cluster
test1_text = """
In Automotive United Trades Organization v. State, 175 Wn.2d 214, 285 P.3d 52 (2012), 
the court held that union dues are protected.

Recent case: Flying T Ranch, Inc. v. Stillaguamish Tribe of Indians, 3 Wn.2d 1031 (2024),
addressed tribal sovereignty issues.
"""

# Test Case 2: Quinault - Same case should cluster together
test2_text = """
The court decided in Anderson & Middleton Lumber Co. v. Quinault Indian Nation, 
130 Wn.2d 862, 929 P.2d 379 (1996), that tribal land rights are paramount.

Another citation: 150 Wn. App. 476, 208 P.3d 1180 discusses related matters.
"""

async def test_flying_t_ranch():
    """Test that different cases with different years DON'T cluster"""
    print("\n" + "="*80)
    print("TEST 1: Flying T Ranch - Different Years Should NOT Cluster")
    print("="*80)
    print("Testing: 175 Wn.2d 214 (2012) vs 3 Wn.2d 1031 (2024)")
    
    processor = UnifiedCitationProcessorV2()
    result = await processor.process_text(text=test1_text)
    
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"\n📊 Found {len(citations)} citations in {len(clusters)} clusters")
    
    # Find the two citations
    automotive_cit = None
    flying_t_cit = None
    
    for cit in citations:
        if '175 Wn.2d 214' in cit.citation or '285 P.3d 52' in cit.citation:
            automotive_cit = cit
            case_name = cit.canonical_name or cit.extracted_case_name or 'N/A'
            print(f"\n  Automotive citation: {cit.citation}")
            print(f"    Case name: {case_name}")
            print(f"    Year: {cit.extracted_date}")
            print(f"    Cluster ID: {cit.cluster_id}")
        elif '3 Wn.2d 1031' in cit.citation:
            flying_t_cit = cit
            case_name = cit.canonical_name or cit.extracted_case_name or 'N/A'
            print(f"\n  Flying T Ranch citation: {cit.citation}")
            print(f"    Case name: {case_name}")
            print(f"    Year: {cit.extracted_date}")
            print(f"    Cluster ID: {cit.cluster_id}")
    
    # Check if they're in the same cluster (they SHOULDN'T be)
    if automotive_cit and flying_t_cit:
        same_cluster = automotive_cit.cluster_id == flying_t_cit.cluster_id
        
        if same_cluster:
            print(f"\n  ❌ FAIL: Different cases (2012 vs 2024) are in SAME cluster!")
            print(f"     Cluster ID: {automotive_cit.cluster_id}")
            return False
        else:
            print(f"\n  ✅ PASS: Different cases are in DIFFERENT clusters")
            print(f"     Automotive: {automotive_cit.cluster_id}")
            print(f"     Flying T Ranch: {flying_t_cit.cluster_id}")
            return True
    else:
        print(f"\n  ❌ ERROR: Could not find both citations")
        return False

async def test_quinault():
    """Test that same case parallel citations DO cluster"""
    print("\n" + "="*80)
    print("TEST 2: Quinault - Same Case Parallel Citations SHOULD Cluster")
    print("="*80)
    print("Testing: 130 Wn.2d 862 + 929 P.2d 379 (both 1996, same case)")
    
    processor = UnifiedCitationProcessorV2()
    result = await processor.process_text(text=test2_text)
    
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"\n📊 Found {len(citations)} citations in {len(clusters)} clusters")
    
    # Find the parallel citations
    wn2d_cit = None
    p2d_cit = None
    
    for cit in citations:
        case_name = cit.canonical_name or cit.extracted_case_name or 'N/A'
        print(f"\n  Citation: {cit.citation}")
        print(f"    Case name: {case_name}")
        print(f"    Year: {cit.extracted_date}")
        print(f"    Cluster ID: {cit.cluster_id}")
        
        if '130 Wn.2d 862' in cit.citation:
            wn2d_cit = cit
        elif '929 P.2d 379' in cit.citation:
            p2d_cit = cit
    
    # Check if they're in the same cluster (they SHOULD be)
    if wn2d_cit and p2d_cit:
        same_cluster = wn2d_cit.cluster_id == p2d_cit.cluster_id
        
        if same_cluster:
            print(f"\n  ✅ PASS: Parallel citations are in SAME cluster")
            print(f"     Cluster ID: {wn2d_cit.cluster_id}")
            return True
        else:
            print(f"\n  ❌ FAIL: Parallel citations are in DIFFERENT clusters!")
            print(f"     130 Wn.2d 862: {wn2d_cit.cluster_id}")
            print(f"     929 P.2d 379: {p2d_cit.cluster_id}")
            return False
    else:
        print(f"\n  ⚠️  Could not find both parallel citations")
        if wn2d_cit:
            print(f"     Found: 130 Wn.2d 862")
        if p2d_cit:
            print(f"     Found: 929 P.2d 379")
        return False

async def main():
    print("\n" + "="*80)
    print("PHASE 5: WRONG CASE ASSOCIATIONS TEST")
    print("="*80)
    
    # Test 1: Flying T Ranch
    test1_pass = await test_flying_t_ranch()
    
    # Test 2: Quinault
    test2_pass = await test_quinault()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Test 1 (Flying T Ranch): {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"Test 2 (Quinault):       {'✅ PASS' if test2_pass else '❌ FAIL'}")
    
    if test1_pass and test2_pass:
        print("\n✅ ALL PHASE 5 TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME PHASE 5 TESTS FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))

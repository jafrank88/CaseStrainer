"""
Test Phases 3 & 4 Fixes in Both Sync and Async Modes

Phase 3: Supreme Court parallel clustering
Phase 4: Case name contamination cleaning
"""

import sys
sys.path.insert(0, '/app')

import asyncio
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Test text includes both Phase 3 and Phase 4 issues
test_text = """
COMPREHENSIVE TEST FOR PHASES 3 & 4

Phase 3 Test: Supreme Court Parallel Citations
Oneida Indian Nation v. Madison County, 605 F.3d 149, 157 (2d Cir. 2010) 
(a tribe's immunity from suit is independent of its lands), vacated and remanded, 
562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011); see also Oneida Indian 
Nation New York v. County of Oneida, 414 U.S. 661 (1974); County Oneida v. 
Oneida Indian Nation of New York, 470 U.S. 226 (1985).

Phase 4 Test: Case Name Contamination
If in Worcester v. Georgia, the Court held that the Cherokee Nation 
was a distinct political community. See Martin v. Lessee of Waddell, 
16 Pet. 367, 10 L. Ed. 997 (1842).

Following the precedent in State v. Lazcano, 136 Wn.2d 188 (1998), 
the court in Gorman v. City of Woodinville, 175 Wn.2d 68, 283 P.3d 1082 (2012), 
further clarified the standard.

The parties are Outsource Services Management, LLC v. Nooksack Business Corp., 
181 Wn.2d 272, 333 P.3d 380 (2014).
"""

def test_sync_processing():
    """Test processing (Run 1)"""
    print("\n" + "="*80)
    print("TESTING RUN 1")
    print("="*80)
    
    processor = UnifiedCitationProcessorV2()
    # Sync processing happens automatically for process_text (not async)
    result = asyncio.run(processor.process_text(text=test_text))
    
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"\n📊 Results: {len(citations)} citations, {len(clusters)} clusters")
    
    # Phase 3 Check: Supreme Court parallel clustering
    print("\n🔍 Phase 3: Checking Supreme Court clustering...")
    supreme_court_cits = [c for c in citations if any(rep in c.citation for rep in ['U.S.', 'S. Ct.', 'L. Ed.'])]
    sc_clusters = set()
    for cit in supreme_court_cits:
        case_name = cit.canonical_name or cit.extracted_case_name or ''
        if 'Madison County' in case_name:
            sc_clusters.add(cit.cluster_id)
    
    print(f"   Found {len(supreme_court_cits)} Supreme Court citations")
    print(f"   Madison County SC citations in {len(sc_clusters)} cluster(s)")
    
    if len(sc_clusters) == 1:
        print("   ✅ PASS: All Madison County SC citations clustered together")
    else:
        print(f"   ❌ FAIL: SC citations in {len(sc_clusters)} clusters (expected 1)")
    
    # Phase 4 Check: Case name contamination
    print("\n🔍 Phase 4: Checking case name extraction...")
    test_cases = {
        '16 Pet. 367': 'Martin v. Lessee of Waddell',
        '175 Wn.2d 68': 'Gorman v. City of Woodinville',
        '181 Wn.2d 272': 'Outsource Services Management'
    }
    
    phase4_pass = 0
    phase4_total = len(test_cases)
    
    for citation_str, expected_name_part in test_cases.items():
        matching_cits = [c for c in citations if citation_str in c.citation]
        if matching_cits:
            actual_name = matching_cits[0].canonical_name or matching_cits[0].extracted_case_name or 'N/A'
            if expected_name_part in actual_name and 'Worcester' not in actual_name and 'Lazcano' not in actual_name and 'parties are' not in actual_name.lower():
                print(f"   ✅ {citation_str}: {actual_name}")
                phase4_pass += 1
            else:
                print(f"   ❌ {citation_str}: {actual_name} (expected: {expected_name_part})")
        else:
            print(f"   ❌ {citation_str}: NOT FOUND")
    
    if phase4_pass == phase4_total:
        print(f"   ✅ PASS: All {phase4_total} case names correct")
    else:
        print(f"   ❌ FAIL: {phase4_pass}/{phase4_total} case names correct")
    
    return {
        'citations': len(citations),
        'clusters': len(clusters),
        'phase3_pass': len(sc_clusters) == 1,
        'phase4_pass': phase4_pass == phase4_total
    }

async def test_async_processing():
    """Test processing (Run 2)"""
    print("\n" + "="*80)
    print("TESTING RUN 2")
    print("="*80)
    
    processor = UnifiedCitationProcessorV2()
    result = await processor.process_text(text=test_text)
    
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"\n📊 Results: {len(citations)} citations, {len(clusters)} clusters")
    
    # Phase 3 Check: Supreme Court parallel clustering
    print("\n🔍 Phase 3: Checking Supreme Court clustering...")
    supreme_court_cits = [c for c in citations if any(rep in c.citation for rep in ['U.S.', 'S. Ct.', 'L. Ed.'])]
    sc_clusters = set()
    for cit in supreme_court_cits:
        case_name = cit.canonical_name or cit.extracted_case_name or ''
        if 'Madison County' in case_name:
            sc_clusters.add(cit.cluster_id)
    
    print(f"   Found {len(supreme_court_cits)} Supreme Court citations")
    print(f"   Madison County SC citations in {len(sc_clusters)} cluster(s)")
    
    if len(sc_clusters) == 1:
        print("   ✅ PASS: All Madison County SC citations clustered together")
    else:
        print(f"   ❌ FAIL: SC citations in {len(sc_clusters)} clusters (expected 1)")
    
    # Phase 4 Check: Case name contamination
    print("\n🔍 Phase 4: Checking case name extraction...")
    test_cases = {
        '16 Pet. 367': 'Martin v. Lessee of Waddell',
        '175 Wn.2d 68': 'Gorman v. City of Woodinville',
        '181 Wn.2d 272': 'Outsource Services Management'
    }
    
    phase4_pass = 0
    phase4_total = len(test_cases)
    
    for citation_str, expected_name_part in test_cases.items():
        matching_cits = [c for c in citations if citation_str in c.citation]
        if matching_cits:
            actual_name = matching_cits[0].canonical_name or matching_cits[0].extracted_case_name or 'N/A'
            if expected_name_part in actual_name and 'Worcester' not in actual_name and 'Lazcano' not in actual_name and 'parties are' not in actual_name.lower():
                print(f"   ✅ {citation_str}: {actual_name}")
                phase4_pass += 1
            else:
                print(f"   ❌ {citation_str}: {actual_name} (expected: {expected_name_part})")
        else:
            print(f"   ❌ {citation_str}: NOT FOUND")
    
    if phase4_pass == phase4_total:
        print(f"   ✅ PASS: All {phase4_total} case names correct")
    else:
        print(f"   ❌ FAIL: {phase4_pass}/{phase4_total} case names correct")
    
    return {
        'citations': len(citations),
        'clusters': len(clusters),
        'phase3_pass': len(sc_clusters) == 1,
        'phase4_pass': phase4_pass == phase4_total
    }

def main():
    print("\n" + "="*80)
    print("PHASES 3 & 4 - COMPREHENSIVE VALIDATION TEST")
    print("="*80)
    print("Testing Supreme Court clustering + case name cleaning")
    print("="*80)
    
    # Test sync
    sync_results = test_sync_processing()
    
    # Test async
    async_results = asyncio.run(test_async_processing())
    
    # Compare results
    print("\n" + "="*80)
    print("COMPARISON")
    print("="*80)
    
    print(f"\nCitation Count:")
    print(f"  Run 1: {sync_results['citations']}")
    print(f"  Run 2: {async_results['citations']}")
    if sync_results['citations'] == async_results['citations']:
        print("  ✅ CONSISTENT")
    else:
        print("  ❌ INCONSISTENT")
    
    print(f"\nCluster Count:")
    print(f"  Run 1: {sync_results['clusters']}")
    print(f"  Run 2: {async_results['clusters']}")
    if sync_results['clusters'] == async_results['clusters']:
        print("  ✅ CONSISTENT")
    else:
        print("  ❌ INCONSISTENT")
    
    print(f"\nPhase 3 (SC Clustering):")
    print(f"  Run 1: {'✅ PASS' if sync_results['phase3_pass'] else '❌ FAIL'}")
    print(f"  Run 2: {'✅ PASS' if async_results['phase3_pass'] else '❌ FAIL'}")
    if sync_results['phase3_pass'] and async_results['phase3_pass']:
        print("  ✅ BOTH PASS")
    else:
        print("  ❌ FAILED")
    
    print(f"\nPhase 4 (Case Names):")
    print(f"  Run 1: {'✅ PASS' if sync_results['phase4_pass'] else '❌ FAIL'}")
    print(f"  Run 2: {'✅ PASS' if async_results['phase4_pass'] else '❌ FAIL'}")
    if sync_results['phase4_pass'] and async_results['phase4_pass']:
        print("  ✅ BOTH PASS")
    else:
        print("  ❌ FAILED")
    
    # Final verdict
    print("\n" + "="*80)
    all_pass = (
        sync_results['phase3_pass'] and async_results['phase3_pass'] and
        sync_results['phase4_pass'] and async_results['phase4_pass'] and
        sync_results['citations'] == async_results['citations'] and
        sync_results['clusters'] == async_results['clusters']
    )
    
    if all_pass:
        print("✅ ALL TESTS PASSED - SYNC AND ASYNC CONSISTENT!")
        print("="*80)
        return 0
    else:
        print("❌ SOME TESTS FAILED OR INCONSISTENT")
        print("="*80)
        return 1

if __name__ == '__main__':
    sys.exit(main())

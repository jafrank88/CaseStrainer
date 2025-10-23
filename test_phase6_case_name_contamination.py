"""
Phase 6: Multiple Case Name Extraction Issue

Diagnoses why citations are getting the wrong case name from earlier citations
in the same text block.

ISSUE: In the Oneida test:
- 605 F.3d 149 should be "Oneida Indian Nation v. Madison County"
  BUT extracted as "Cayuga Indian Nation v. Seneca County"
- 2017-NM-007 should be "Hamaatsa, Inc. v. Pueblo of San Felipe"
  BUT extracted as "Cayuga Indian Nation v. Seneca County"

The first case name (Cayuga) is contaminating later citations.
"""

import sys
sys.path.insert(0, '/app')

import asyncio
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Problematic text with multiple cases
test_text = """
See Cayuga Indian Nation v. Seneca County, 761 F.3d 218, 221 (2d Cir. 2014); 
Oneida Indian Nation v. Madison County, 605 F.3d 149, 157 (2d Cir. 2010); 
Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977, 985 (2016).
"""

async def test_case_name_extraction():
    """Test case name extraction for multiple citations"""
    print("\n" + "="*80)
    print("PHASE 6: CASE NAME CONTAMINATION DIAGNOSTIC")
    print("="*80)
    
    processor = UnifiedCitationProcessorV2()
    result = await processor.process_text(text=test_text)
    
    citations = result.get('citations', [])
    
    print(f"\n📊 Found {len(citations)} citations")
    print("\n" + "="*80)
    print("EXPECTED vs ACTUAL")
    print("="*80)
    
    # Expected case names
    expected = {
        '761 F.3d 218': 'Cayuga Indian Nation v. Seneca County',
        '605 F.3d 149': 'Oneida Indian Nation v. Madison County',
        '2017-NM-007': 'Hamaatsa, Inc. v. Pueblo of San Felipe',
        '388 P.3d 977': 'Hamaatsa, Inc. v. Pueblo of San Felipe'
    }
    
    results = []
    
    for cit in citations:
        citation_text = cit.citation
        extracted = cit.extracted_case_name or 'N/A'
        canonical = cit.canonical_name or 'N/A'
        
        # Find expected name
        expected_name = None
        for key in expected:
            if key in citation_text:
                expected_name = expected[key]
                break
        
        if not expected_name:
            continue
        
        # Use canonical if available, otherwise extracted
        actual = canonical if canonical != 'N/A' else extracted
        
        # Check if correct
        is_correct = expected_name.lower() in actual.lower() if actual != 'N/A' else False
        
        print(f"\n  Citation: {citation_text}")
        print(f"    Expected:  {expected_name}")
        print(f"    Extracted: {extracted}")
        print(f"    Canonical: {canonical}")
        print(f"    Result:    {'✅ CORRECT' if is_correct else '❌ WRONG'}")
        
        results.append({
            'citation': citation_text,
            'expected': expected_name,
            'extracted': extracted,
            'canonical': canonical,
            'correct': is_correct
        })
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    correct_count = sum(1 for r in results if r['correct'])
    total_count = len(results)
    
    print(f"\nCorrect: {correct_count}/{total_count}")
    
    for r in results:
        status = '✅' if r['correct'] else '❌'
        print(f"  {status} {r['citation'][:30]:30s} -> {r['extracted'][:40]}")
    
    # Identify the contamination pattern
    print("\n" + "="*80)
    print("CONTAMINATION ANALYSIS")
    print("="*80)
    
    # Check if later citations have the first case name
    first_case_name = "Cayuga Indian Nation v. Seneca County"
    contaminated = []
    
    for r in results:
        if not r['correct'] and first_case_name.lower() in r['extracted'].lower():
            contaminated.append(r['citation'])
    
    if contaminated:
        print(f"\n⚠️  CONTAMINATION DETECTED!")
        print(f"  First case name '{first_case_name}' is contaminating:")
        for cit in contaminated:
            print(f"    - {cit}")
        print(f"\n  ROOT CAUSE: Case name extraction is not properly isolating")
        print(f"  the context for each citation. It's picking up the first case")
        print(f"  name in the text instead of the closest one.")
    else:
        print(f"\n✅ No obvious contamination pattern detected")
    
    if correct_count == total_count:
        print("\n✅ ALL CASE NAMES CORRECT!")
        return 0
    else:
        print(f"\n❌ {total_count - correct_count} CASE NAME(S) INCORRECT")
        return 1

if __name__ == '__main__':
    sys.exit(asyncio.run(test_case_name_extraction()))

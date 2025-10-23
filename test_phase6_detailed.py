"""
Phase 6: Detailed diagnostic to show citation positions and extraction
"""

import sys
sys.path.insert(0, '/app')

import asyncio
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Full test with pinpoints
test_text = """See Cayuga Indian Nation v. Seneca County, 761 F.3d 218, 221 (2d Cir. 2014); Oneida Indian Nation v. Madison County, 605 F.3d 149, 157 (2d Cir. 2010); Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977, 985 (2016)."""

async def test():
    print("\n" + "="*80)
    print("PHASE 6: DETAILED POSITION ANALYSIS")
    print("="*80)
    print(f"\nFull text:\n{test_text}\n")
    
    processor = UnifiedCitationProcessorV2()
    result = await processor.process_text(text=test_text)
    
    citations = result.get('citations', [])
    
    print(f"\n{len(citations)} citations found:\n")
    
    for cit in citations:
        citation_str = cit.citation
        extracted_name = cit.extracted_case_name
        start_pos = cit.start_index if hasattr(cit, 'start_index') else 'N/A'
        
        # Find position in text
        if start_pos != 'N/A':
            # Show context
            context_start = max(0, start_pos - 50)
            context_end = min(len(test_text), start_pos + len(citation_str) + 50)
            context = test_text[context_start:context_end]
            
            # Mark the citation position
            mark_pos = start_pos - context_start
            marked_context = context[:mark_pos] + "[" + citation_str + "]" + context[mark_pos+len(citation_str):]
            
            print(f"Citation: {citation_str}")
            print(f"  Position: {start_pos}")
            print(f"  Extracted: {extracted_name}")
            print(f"  Context: ...{marked_context}...")
            print()
        else:
            print(f"Citation: {citation_str}")
            print(f"  Position: {start_pos}")
            print(f"  Extracted: {extracted_name}")
            print()
    
    # Summary of contamination
    print("="*80)
    print("CONTAMINATION CHECK")
    print("="*80)
    
    cayuga_count = sum(1 for cit in citations if 'Cayuga' in (cit.extracted_case_name or ''))
    oneida_count = sum(1 for cit in citations if 'Oneida' in (cit.extracted_case_name or ''))
    hamaatsa_count = sum(1 for cit in citations if 'Hamaatsa' in (cit.extracted_case_name or ''))
    
    print(f"\nCayuga extractions: {cayuga_count} (should be 1)")
    print(f"Oneida extractions: {oneida_count} (should be 1)")
    print(f"Hamaatsa extractions: {hamaatsa_count} (should be 2)")
    
    if cayuga_count == 1 and oneida_count == 1 and hamaatsa_count == 2:
        print("\n✅ NO CONTAMINATION!")
    else:
        print("\n❌ CONTAMINATION DETECTED!")

if __name__ == '__main__':
    asyncio.run(test())

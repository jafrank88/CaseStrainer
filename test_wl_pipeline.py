#!/usr/bin/env python3
"""
Test WL extraction pipeline step by step
"""

import sys
from pathlib import Path
import re

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def main():
    # Sample text with WL citations from the actual PDF
    test_text = """
    In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), the court ruled that evidence 
    regarding the defendant's prior bad acts was inadmissible. See also Johnson v. State, 2018 WL 3037217 
    (Wyo. 2018), where the court held that motions in limine are proper procedural tools.
    """
    
    print("🧪 Testing WL Citation Pipeline")
    print("=" * 50)
    print(f"Test text: {test_text.strip()}")
    print()
    
    # Step 1: Manual regex
    wl_pattern = r'\b\d{4}\s+WL\s+\d+\b'
    manual_matches = re.findall(wl_pattern, test_text, re.IGNORECASE)
    print(f"1. Manual regex: {len(manual_matches)} matches")
    for match in manual_matches:
        print(f"   - {match}")
    print()
    
    # Step 2: Test CaseStrainer
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        result = processor.process_text_sync(test_text)
        
        citations = result.get('citations', [])
        wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
        
        print(f"2. CaseStrainer: {len(citations)} total, {len(wl_citations)} WL citations")
        for citation in citations:
            wl_flag = "🟢 WL" if 'WL' in citation.get('citation', '') else "🔵"
            print(f"   {wl_flag} {citation.get('citation')} (source: {citation.get('source')})")
        
        if len(manual_matches) > len(wl_citations):
            print(f"❌ PROBLEM: Manual found {len(manual_matches)}, CaseStrainer found {len(wl_citations)}")
        else:
            print(f"✅ SUCCESS: CaseStrainer found all WL citations")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

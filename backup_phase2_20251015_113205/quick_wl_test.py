#!/usr/bin/env python3
"""
Quick WL citation test using correct API methods
"""

import sys
from pathlib import Path
import re

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def main():
    print("🔍 Quick WL Citation Test")
    print("=" * 40)
    
    # Sample text with WL citations
    test_text = "In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), the court ruled."
    
    print(f"Test text: {test_text}")
    print()
    
    # Manual regex test
    wl_pattern = r'\b\d{4}\s+WL\s+\d+\b'
    manual_matches = re.findall(wl_pattern, test_text, re.IGNORECASE)
    print(f"Manual regex: {len(manual_matches)} WL citations")
    for match in manual_matches:
        print(f"  - {match}")
    print()
    
    # Test UnifiedSyncProcessor
    try:
        from unified_sync_processor import UnifiedSyncProcessor
        
        processor = UnifiedSyncProcessor()
        result = processor.process_text_unified(test_text)
        
        citations = result.get('citations', [])
        wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
        
        print(f"UnifiedSyncProcessor:")
        print(f"  Total citations: {len(citations)}")
        print(f"  WL citations: {len(wl_citations)}")
        
        if wl_citations:
            print("  ✅ WL Citations found:")
            for citation in wl_citations:
                print(f"    - {citation.get('citation')}")
        else:
            print("  ❌ No WL citations found")
            print("  All citations:")
            for citation in citations:
                print(f"    - {citation.get('citation')}")
        
        # Check if the issue is found
        if len(manual_matches) > len(wl_citations):
            print(f"\n❌ ISSUE CONFIRMED:")
            print(f"   Manual regex found {len(manual_matches)} WL citations")
            print(f"   CaseStrainer found {len(wl_citations)} WL citations")
            print(f"   WL citations are being lost in the processing pipeline")
        else:
            print(f"\n✅ WL extraction working correctly")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

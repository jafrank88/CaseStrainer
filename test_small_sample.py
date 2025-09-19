#!/usr/bin/env python3
"""
Test with small text sample to force sync processing
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def main():
    print("🔍 Testing Small Sample (Force Sync Processing)")
    print("=" * 60)
    
    # Small text sample with WL citation (under 5KB threshold)
    small_text = """
    PLAINTIFFS' MOTIONS IN LIMINE
    
    Plaintiffs move this Court for an Order in limine to exclude evidence.
    In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), 
    the court ruled that evidence regarding the defendant's prior bad acts 
    was inadmissible. See also Johnson v. State, 2018 WL 3037217 (Wyo. 2018).
    
    The Federal Rules of Evidence, particularly Rules 401, 402, and 403, 
    govern the admissibility of evidence.
    """
    
    print(f"📝 Sample text ({len(small_text)} bytes - under 5KB threshold):")
    print(f'"{small_text.strip()}"')
    print()
    
    # Test with UnifiedSyncProcessor
    try:
        from unified_sync_processor import UnifiedSyncProcessor
        
        processor = UnifiedSyncProcessor()
        result = processor.process_text_unified(small_text)
        
        citations = result.get('citations', [])
        wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
        
        print(f"📊 UnifiedSyncProcessor Results:")
        print(f"  Total citations: {len(citations)}")
        print(f"  WL citations: {len(wl_citations)}")
        
        if wl_citations:
            print("  ✅ WL Citations found:")
            for citation in wl_citations:
                print(f"    - {citation.get('citation')} (source: {citation.get('source')})")
        else:
            print("  ❌ No WL citations found")
            
        print(f"  All citations found:")
        for citation in citations:
            print(f"    - {citation.get('citation')} (source: {citation.get('source')})")
            
        # Check processing strategy
        strategy = result.get('processing_strategy', 'unknown')
        print(f"  Processing strategy: {strategy}")
        
        if len(wl_citations) == 2:
            print(f"\n🎉 SUCCESS: Found both expected WL citations!")
            print(f"   The fix is working for sync processing")
        elif len(wl_citations) > 0:
            print(f"\n⚠️  PARTIAL: Found {len(wl_citations)}/2 expected WL citations")
        else:
            print(f"\n❌ FAILURE: No WL citations found even in small sample")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

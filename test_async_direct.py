#!/usr/bin/env python3
"""
Test async processing directly to debug the issue
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def main():
    print("🔍 Testing Async Processing Directly")
    print("=" * 50)
    
    # Test text with WL citations
    test_text = """
    In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), 
    the court ruled. See also Johnson v. State, 2018 WL 3037217 (Wyo. 2018).
    Additional cases include Smith v. Jones, 2019 WL 2516279 (Fed. Cir. 2019).
    """ * 10  # Make it large enough for async
    
    print(f"📝 Test text length: {len(test_text)} bytes")
    
    try:
        # Test the async processing function directly
        from progress_manager import process_citation_task_direct
        import uuid
        
        task_id = str(uuid.uuid4())
        input_data = {'text': test_text}
        
        print(f"🧪 Calling process_citation_task_direct directly...")
        print(f"  Task ID: {task_id}")
        print(f"  Input type: text")
        print(f"  Text length: {len(test_text)}")
        
        result = process_citation_task_direct(task_id, 'text', input_data)
        
        print(f"\n📊 Direct async processing result:")
        print(f"  Success: {result.get('success', False)}")
        
        if result.get('success'):
            final_result = result.get('result', {})
            citations = final_result.get('citations', [])
            wl_citations = [c for c in citations if 'WL' in str(c.get('citation', ''))]
            
            print(f"  Total citations: {len(citations)}")
            print(f"  WL citations: {len(wl_citations)}")
            
            if wl_citations:
                print("  ✅ WL Citations found:")
                for citation in wl_citations:
                    print(f"    - {citation.get('citation')}")
            else:
                print("  ❌ No WL citations found")
                
            if citations:
                print("  All citations found:")
                for citation in citations[:10]:  # Show first 10
                    print(f"    - {citation.get('citation', 'N/A')}")
                if len(citations) > 10:
                    print(f"    ... and {len(citations) - 10} more")
        else:
            print(f"  ❌ Processing failed")
            if 'error' in result:
                print(f"  Error: {result['error']}")
                
    except Exception as e:
        print(f"❌ Error in direct async processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

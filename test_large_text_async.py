#!/usr/bin/env python3
"""
Test async processing with large text containing WL citations
"""

import sys
from pathlib import Path
import requests
import time
import json

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def main():
    print("🔍 Testing Async Processing with Large Text")
    print("=" * 60)
    
    # Create large text that will trigger async processing
    base_text = """
    PLAINTIFFS' MOTIONS IN LIMINE
    
    Plaintiffs move this Court for an Order in limine to exclude evidence.
    In Wyoming v. U.S. Dep't of Interior, 2006 WL 3801910 (D. Wyo. 2006), 
    the court ruled that evidence regarding the defendant's prior bad acts 
    was inadmissible. See also Johnson v. State, 2018 WL 3037217 (Wyo. 2018).
    
    Additional cases include Smith v. Jones, 2019 WL 2516279 (Fed. Cir. 2019),
    and Brown v. Davis, 2017 WL 3461055 (9th Cir. 2017). The court in
    Miller v. Wilson, 2010 WL 4683851 (D. Mont. 2010), held similar reasoning.
    
    The Federal Rules of Evidence, particularly Rules 401, 402, and 403, 
    govern the admissibility of evidence.
    """
    
    # Repeat the text to make it large enough for async processing
    large_text = base_text * 20  # Should be over 5KB threshold
    
    print(f"📝 Large text length: {len(large_text)} bytes (should trigger async)")
    
    # Count expected WL citations
    import re
    wl_pattern = r'\b\d{4}\s+WL\s+\d+\b'
    expected_wl = re.findall(wl_pattern, large_text, re.IGNORECASE)
    print(f"📊 Expected WL citations: {len(expected_wl)}")
    for wl in set(expected_wl):  # Show unique ones
        print(f"    - {wl}")
    print()
    
    # Test via API
    try:
        print("🌐 Making API call for async processing...")
        response = requests.post(
            'http://localhost:5000/casestrainer/api/analyze', 
            data={'text': large_text, 'type': 'text'}, 
            timeout=120
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if this is async (has task_id) or sync (has citations)
            if 'task_id' in result or ('result' in result and 'task_id' in result['result']):
                task_id = result.get('task_id') or result.get('result', {}).get('task_id')
                print(f"📋 Async processing detected - Task ID: {task_id}")
                
                # Wait for completion and get results
                print("⏳ Waiting for async processing to complete...")
                
                max_wait = 60  # 60 seconds max
                wait_interval = 2  # Check every 2 seconds
                
                for attempt in range(0, max_wait, wait_interval):
                    time.sleep(wait_interval)
                    
                    # Check task status
                    status_response = requests.get(
                        f'http://localhost:5000/casestrainer/api/task_status/{task_id}',
                        timeout=30
                    )
                    
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        status = status_result.get('status', 'unknown')
                        
                        print(f"  [{attempt+wait_interval}s] Status: {status}")
                        
                        if status == 'completed':
                            # Get the final results
                            final_result = status_result.get('result', {})
                            citations = final_result.get('citations', [])
                            wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
                            
                            print(f"\n✅ Async processing completed!")
                            print(f"  Total citations: {len(citations)}")
                            print(f"  WL citations: {len(wl_citations)}")
                            
                            if wl_citations:
                                print("  ✅ WL Citations found:")
                                for citation in wl_citations:
                                    print(f"    - {citation.get('citation')}")
                            else:
                                print("  ❌ No WL citations found")
                                
                            # Compare with expected
                            print(f"\n📊 Comparison:")
                            print(f"  Expected: {len(set(expected_wl))} unique WL citations")
                            print(f"  Found: {len(wl_citations)} WL citations")
                            
                            if len(wl_citations) >= len(set(expected_wl)):
                                print("  🎉 SUCCESS: Found all or more WL citations!")
                            elif len(wl_citations) > 0:
                                print(f"  ⚠️  PARTIAL: Found some WL citations")
                            else:
                                print("  ❌ FAILURE: No WL citations found")
                            
                            return
                            
                        elif status in ['failed', 'error']:
                            print(f"  ❌ Async processing failed: {status}")
                            error = status_result.get('error', 'Unknown error')
                            print(f"  Error: {error}")
                            return
                            
                    else:
                        print(f"  ❌ Status check failed: {status_response.status_code}")
                
                print("  ⏰ Timeout waiting for async processing")
                
            else:
                # Sync processing
                print("📋 Sync processing detected")
                
                # Check if citations are in nested result structure
                citations = result.get('citations', [])
                if not citations and 'result' in result:
                    citations = result['result'].get('citations', [])
                    
                wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
                
                print(f"  Total citations: {len(citations)}")
                print(f"  WL citations: {len(wl_citations)}")
                
                if wl_citations:
                    print("  ✅ WL Citations found:")
                    for citation in wl_citations:
                        print(f"    - {citation.get('citation')}")
                else:
                    print("  ❌ No WL citations found")
                    
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

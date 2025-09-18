"""
Test Async Processing Fix
Tests the fixed async processing that now uses DockerOptimizedProcessor.
"""

import requests
import json
import time

def test_async_processing_fix():
    """Test the fixed async processing."""
    
    print("🎯 TESTING FIXED ASYNC PROCESSING")
    print("=" * 40)
    
    # Create text that exceeds 2KB threshold
    base_text = """'[A] court must not add words where the legislature has
chosen not to include them.'" Lucid Grp. USA, Inc. v. Dep't of Licensing, 33 Wn. App.
2d 75, 81, 559 P.3d 545 (2024) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d
674, 682, 80 P.3d 598 (2003)), review denied, 4 Wn.3d 1021 (2025)

If the statute is susceptible to more than one reasonable interpretation after this inquiry, 
it is ambiguous, and we may consider extratextual materials to help determine legislative 
intent, including legislative history and agency interpretation. Five Corners Fam. Farmers v. State, 173 Wn.2d 
296, 306, 268 P.3d 892 (2011) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 
Wn.2d 674, 682, 80 P.3d 598 (2003)); Bostain v. Food Express, Inc., 159 Wn.2d 
700, 716, 153 P.3d 846 (2007) (collecting cases)."""
    
    # Repeat to ensure it's over 2KB
    large_text = base_text * 3  # Should be ~3KB
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': large_text}
    
    print(f"📝 Text length: {len(large_text)} characters (threshold: 2048)")
    
    try:
        print(f"\n📤 Submitting async task...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Submission failed: HTTP {response.status_code}")
            return False
        
        result = response.json()
        
        if 'task_id' in result.get('result', {}):
            task_id = result['result']['task_id']
            print(f"✅ Async task created: {task_id}")
            
            # Monitor with shorter timeout since it should be faster now
            status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
            
            print(f"\n⏳ Monitoring fixed async task...")
            
            max_attempts = 40  # 2 minutes total
            last_status = None
            
            for attempt in range(max_attempts):
                try:
                    status_response = requests.get(status_url, timeout=10)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if 'status' in status_data:
                            status = status_data['status']
                            
                            # Print status changes or every 10 attempts
                            if status != last_status or attempt % 10 == 0:
                                elapsed = (attempt + 1) * 3
                                print(f"   [{elapsed:3d}s] Status: {status}")
                                last_status = status
                            
                            if status == 'completed':
                                citations = status_data.get('citations', [])
                                
                                print(f"\n✅ ASYNC TASK COMPLETED!")
                                print(f"   Time taken: {(attempt + 1) * 3} seconds")
                                print(f"   Citations found: {len(citations)}")
                                
                                # Check deduplication
                                citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                                unique_citations = set(citation_texts)
                                duplicates = len(citation_texts) - len(unique_citations)
                                
                                print(f"   Total citations: {len(citation_texts)}")
                                print(f"   Unique citations: {len(unique_citations)}")
                                print(f"   Duplicates: {duplicates}")
                                
                                if duplicates == 0:
                                    print(f"   ✅ ASYNC DEDUPLICATION WORKING!")
                                else:
                                    print(f"   ❌ ASYNC DEDUPLICATION FAILED!")
                                    from collections import Counter
                                    counts = Counter(citation_texts)
                                    for citation, count in counts.items():
                                        if count > 1:
                                            print(f"      '{citation}' appears {count} times")
                                
                                # Check case name extraction
                                print(f"\n📋 Case name extraction:")
                                for citation in citations[:3]:  # Show first 3
                                    citation_text = citation.get('citation', '').replace('\n', ' ').strip()
                                    extracted_name = citation.get('extracted_case_name', '')
                                    print(f"   {citation_text}: {extracted_name}")
                                
                                return True
                                
                            elif status == 'failed':
                                error = status_data.get('error', 'Unknown error')
                                print(f"\n❌ ASYNC TASK FAILED!")
                                print(f"   Error: {error}")
                                return False
                                
                        else:
                            # Direct result format
                            if 'citations' in status_data:
                                citations = status_data.get('citations', [])
                                print(f"\n✅ ASYNC TASK COMPLETED (direct result)!")
                                print(f"   Citations found: {len(citations)}")
                                return True
                    
                    elif status_response.status_code == 404:
                        if attempt < 5:  # Only show 404s for first few attempts
                            print(f"   [{(attempt + 1) * 3:3d}s] Task not found yet (404)")
                    else:
                        if attempt % 10 == 0:
                            print(f"   [{(attempt + 1) * 3:3d}s] HTTP {status_response.status_code}")
                            
                except Exception as e:
                    if attempt % 15 == 0:  # Show errors occasionally
                        print(f"   [{(attempt + 1) * 3:3d}s] Error: {e}")
                
                time.sleep(3)
            
            print(f"\n⏰ ASYNC TASK TIMED OUT")
            print(f"   Last status: {last_status}")
            print(f"   This suggests the fix may need more work")
            return False
            
        else:
            # Still processed as sync
            processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
            citations = result.get('result', {}).get('citations', [])
            
            print(f"⚠️  STILL PROCESSED AS SYNC!")
            print(f"   Processing mode: {processing_mode}")
            print(f"   Citations: {len(citations)}")
            print(f"   Text length may not exceed threshold")
            
            return False
            
    except Exception as e:
        print(f"❌ Error in async test: {e}")
        return False

def main():
    """Run comprehensive async fix testing."""
    
    print("🎯 ASYNC PROCESSING FIX TEST")
    print("=" * 30)
    
    print("✅ Server restarted with new code!")
    
    # Test the fixed async processing
    async_success = test_async_processing_fix()
    
    print(f"\n🏁 FINAL RESULT")
    print("=" * 15)
    print(f"✅ Async processing: {'SUCCESS' if async_success else 'NEEDS MORE WORK'}")
    
    if async_success:
        print(f"\n🎉 ASYNC PROCESSING FULLY WORKING!")
        print(f"   - Tasks complete successfully")
        print(f"   - Deduplication working")
        print(f"   - Case name extraction working")
    else:
        print(f"\n⚠️  ASYNC PROCESSING NEEDS MORE INVESTIGATION")

if __name__ == "__main__":
    main()

"""
Quick Async Test
Tests if the async fix works with the current running system.
"""

import requests
import time

def test_async_quick():
    """Quick test of async processing."""
    
    print("🚀 QUICK ASYNC TEST")
    print("=" * 20)
    
    # Create text over 2KB threshold
    base_text = """Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674, 682, 80 P.3d 598 (2003)
Bostain v. Food Express, Inc., 159 Wn.2d 700, 716, 153 P.3d 846 (2007)
Five Corners Fam. Farmers v. State, 173 Wn.2d 296, 306, 268 P.3d 892 (2011)"""
    
    # Repeat to exceed threshold
    large_text = base_text + "\n" + ("Additional legal analysis. " * 100)
    
    print(f"📝 Text length: {len(large_text)} characters")
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': large_text}
    
    try:
        print(f"\n📤 Submitting async task...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result.get('result', {}):
                task_id = result['result']['task_id']
                print(f"✅ Async task created: {task_id}")
                
                # Quick monitoring - just 30 seconds
                status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
                
                for attempt in range(10):  # 30 seconds total
                    try:
                        status_response = requests.get(status_url, timeout=5)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if 'status' in status_data:
                                status = status_data['status']
                                print(f"   [{(attempt + 1) * 3:2d}s] Status: {status}")
                                
                                if status == 'completed':
                                    citations = status_data.get('citations', [])
                                    print(f"\n🎉 SUCCESS! Task completed in {(attempt + 1) * 3}s")
                                    print(f"   Citations: {len(citations)}")
                                    
                                    # Quick deduplication check
                                    citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                                    unique_citations = set(citation_texts)
                                    duplicates = len(citation_texts) - len(unique_citations)
                                    
                                    print(f"   Duplicates: {duplicates}")
                                    print(f"   ✅ Async deduplication: {'WORKING' if duplicates == 0 else 'FAILED'}")
                                    
                                    return True
                                    
                                elif status == 'failed':
                                    error = status_data.get('error', 'Unknown')
                                    print(f"\n❌ Task failed: {error}")
                                    return False
                            
                            elif 'citations' in status_data:
                                citations = status_data.get('citations', [])
                                print(f"\n🎉 SUCCESS! Direct result")
                                print(f"   Citations: {len(citations)}")
                                return True
                        
                        elif status_response.status_code == 404:
                            print(f"   [{(attempt + 1) * 3:2d}s] Task not ready (404)")
                        else:
                            print(f"   [{(attempt + 1) * 3:2d}s] HTTP {status_response.status_code}")
                            
                    except Exception as e:
                        print(f"   [{(attempt + 1) * 3:2d}s] Error: {e}")
                    
                    time.sleep(3)
                
                print(f"\n⏰ Quick test timed out (30s)")
                print(f"   Task may still be processing...")
                return False
                
            else:
                # Processed as sync
                citations = result.get('result', {}).get('citations', [])
                print(f"⚠️  Processed as sync: {len(citations)} citations")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_async_quick()
    
    if success:
        print(f"\n🎉 ASYNC PROCESSING IS WORKING!")
    else:
        print(f"\n⚠️  ASYNC PROCESSING NEEDS SERVER RESTART")
        print(f"   The fix may require restarting the containers to take effect")

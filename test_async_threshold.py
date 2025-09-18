"""
Test Async Processing Threshold
Creates text that definitely exceeds the 2KB threshold to force async processing.
"""

import requests
import json
import time

def create_large_text():
    """Create text that definitely exceeds 2KB threshold."""
    
    base_text = """'[A] court must not add words where the legislature has
chosen not to include them.'" Lucid Grp. USA, Inc. v. Dep't of Licensing, 33 Wn. App.
2d 75, 81, 559 P.3d 545 (2024) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d
674, 682, 80 P.3d 598 (2003)), review denied, 4 Wn.3d 1021 (2025)

If the statute is susceptible to more than one reasonable interpretation after this inquiry, 
it is ambiguous, and we may consider extratextual materials to help determine legislative 
intent, including legislative history and agency interpretation. Five Corners Fam. Farmers v. State, 173 Wn.2d 
296, 306, 268 P.3d 892 (2011) (quoting Rest. Dev., Inc. v. Cananwill, Inc., 150 
Wn.2d 674, 682, 80 P.3d 598 (2003)); Bostain v. Food Express, Inc., 159 Wn.2d 
700, 716, 153 P.3d 846 (2007) (collecting cases).

Additional legal analysis follows. The court's reasoning in this case demonstrates the importance
of careful statutory interpretation and the role of precedent in legal decision-making.
This analysis continues with more detailed examination of the legal principles involved."""
    
    # Calculate how many repetitions we need to exceed 2KB
    threshold = 2048
    base_length = len(base_text)
    repetitions_needed = (threshold // base_length) + 2  # Add 2 for safety margin
    
    large_text = base_text * repetitions_needed
    
    print(f"📏 Base text length: {base_length} characters")
    print(f"📏 Repetitions: {repetitions_needed}")
    print(f"📏 Final text length: {len(large_text)} characters")
    print(f"📏 Threshold: {threshold} characters")
    print(f"📏 Exceeds threshold: {'YES' if len(large_text) > threshold else 'NO'}")
    
    return large_text

def test_async_with_proper_threshold():
    """Test async processing with text that definitely exceeds threshold."""
    
    print("🎯 TESTING ASYNC WITH PROPER THRESHOLD")
    print("=" * 45)
    
    large_text = create_large_text()
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': large_text}
    
    try:
        print(f"\n📤 Submitting large text for async processing...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Submission failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        print(f"✅ Response received")
        
        # Check if it's async or sync
        if 'task_id' in result.get('result', {}):
            task_id = result['result']['task_id']
            print(f"✅ ASYNC PROCESSING TRIGGERED!")
            print(f"   Task ID: {task_id}")
            
            # Monitor the task with reasonable timeout
            return monitor_async_task(task_id)
            
        else:
            # Still processed as sync
            processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
            citations = result.get('result', {}).get('citations', [])
            
            print(f"⚠️  STILL PROCESSED AS SYNC!")
            print(f"   Processing mode: {processing_mode}")
            print(f"   Citations: {len(citations)}")
            print(f"   This suggests the threshold logic might not be working as expected")
            
            return False
            
    except Exception as e:
        print(f"❌ Error in threshold test: {e}")
        return False

def monitor_async_task(task_id, max_wait_minutes=5):
    """Monitor an async task with reasonable timeout."""
    
    print(f"\n⏳ MONITORING ASYNC TASK: {task_id}")
    print("-" * 40)
    
    status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
    
    max_attempts = max_wait_minutes * 20  # 3 second intervals
    last_status = None
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'status' in data:
                    status = data['status']
                    
                    # Only print on status change or every 20 attempts (1 minute)
                    if status != last_status or attempt % 20 == 0:
                        elapsed_time = (attempt + 1) * 3
                        print(f"   [{elapsed_time:3d}s] Status: {status}")
                        last_status = status
                    
                    if status == 'completed':
                        citations = data.get('citations', [])
                        
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
                        
                        return True
                        
                    elif status == 'failed':
                        error = data.get('error', 'Unknown error')
                        print(f"\n❌ ASYNC TASK FAILED!")
                        print(f"   Error: {error}")
                        return False
                        
                else:
                    # Direct result format
                    if 'citations' in data:
                        citations = data.get('citations', [])
                        print(f"\n✅ ASYNC TASK COMPLETED (direct result)!")
                        print(f"   Citations found: {len(citations)}")
                        return True
            
            elif response.status_code == 404:
                if attempt < 10:  # Only show 404s for first 30 seconds
                    if attempt % 5 == 0:
                        print(f"   [{(attempt + 1) * 3:3d}s] Task not found yet (404)")
            else:
                if attempt % 10 == 0:  # Show other errors occasionally
                    print(f"   [{(attempt + 1) * 3:3d}s] HTTP {response.status_code}")
                    
        except Exception as e:
            if attempt % 20 == 0:  # Show connection errors occasionally
                print(f"   [{(attempt + 1) * 3:3d}s] Connection error: {e}")
        
        time.sleep(3)
    
    print(f"\n⏰ ASYNC TASK TIMED OUT")
    print(f"   Waited: {max_wait_minutes} minutes")
    print(f"   Last status: {last_status}")
    
    return False

def test_sync_vs_async_comparison():
    """Compare sync and async processing with different text sizes."""
    
    print(f"\n📊 SYNC VS ASYNC COMPARISON")
    print("-" * 30)
    
    # Test 1: Small text (should be sync)
    small_text = "Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674 (2003)"
    
    print(f"Test 1: Small text ({len(small_text)} chars)")
    result1 = test_text_processing(small_text, "small")
    
    # Test 2: Medium text (right at threshold)
    medium_text = "A" * 2050  # Just over 2KB
    medium_text += " Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674 (2003)"
    
    print(f"\nTest 2: Medium text ({len(medium_text)} chars)")
    result2 = test_text_processing(medium_text, "medium")
    
    print(f"\n📋 COMPARISON RESULTS:")
    print(f"   Small text: {'SYNC' if result1 else 'ASYNC/FAILED'}")
    print(f"   Medium text: {'SYNC' if result2 else 'ASYNC/FAILED'}")

def test_text_processing(text, label):
    """Test a specific text and return True if processed as sync."""
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': text}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result.get('result', {}):
                print(f"   → ASYNC (task_id: {result['result']['task_id']})")
                return False
            else:
                processing_mode = result.get('result', {}).get('metadata', {}).get('processing_mode', 'unknown')
                citations = result.get('result', {}).get('citations', [])
                print(f"   → SYNC (mode: {processing_mode}, citations: {len(citations)})")
                return True
        else:
            print(f"   → ERROR (HTTP {response.status_code})")
            return False
            
    except Exception as e:
        print(f"   → ERROR ({e})")
        return False

def main():
    """Run comprehensive async threshold testing."""
    
    print("🎯 ASYNC PROCESSING THRESHOLD TEST")
    print("=" * 40)
    
    # Test the threshold logic
    test_sync_vs_async_comparison()
    
    # Test actual async processing
    async_success = test_async_with_proper_threshold()
    
    print(f"\n🏁 FINAL RESULT")
    print("=" * 15)
    print(f"✅ Async processing: {'SUCCESS' if async_success else 'NEEDS WORK'}")

if __name__ == "__main__":
    main()

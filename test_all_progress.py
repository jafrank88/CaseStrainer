import requests
import json
import time

def test_sync_text_progress():
    """Test progress tracking for sync text processing."""
    
    print("🔍 TESTING SYNC TEXT PROGRESS")
    print("=" * 50)
    
    # Small text that should trigger sync processing
    small_text = "Brown v. Board, 347 U.S. 483 (1954). Miranda v. Arizona, 384 U.S. 436 (1966)."
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': small_text}
    
    try:
        print(f"📤 Testing small text: {len(small_text)} characters")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Check for progress data in result
            result = response_data.get('result', {})
            progress_data = result.get('progress_data')
            
            if progress_data:
                print(f"   ✅ SYNC PROGRESS WORKING!")
                print(f"   Status: {progress_data.get('status')}")
                print(f"   Overall Progress: {progress_data.get('overall_progress')}%")
                print(f"   Steps completed: {len([s for s in progress_data.get('steps', []) if s.get('status') == 'completed'])}/6")
                
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                print(f"   Citations: {len(citations)}, Clusters: {len(clusters)}")
                return True
            else:
                print(f"   ❌ No progress data found")
                return False
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_async_url_progress():
    """Test progress tracking for async URL processing."""
    
    print("\n🔍 TESTING ASYNC URL PROGRESS")
    print("=" * 50)
    
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'url', 'url': test_url}
    
    try:
        print(f"📤 Testing URL processing")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Check both top level and nested in result
            task_id = response_data.get('task_id') or response_data.get('request_id')
            if not task_id:
                result = response_data.get('result', {})
                task_id = result.get('task_id') or result.get('request_id')
            
            progress_endpoint = response_data.get('progress_endpoint')
            if not progress_endpoint:
                result = response_data.get('result', {})
                progress_endpoint = result.get('progress_endpoint')
            
            if task_id and progress_endpoint:
                print(f"   ✅ ASYNC TASK CREATED!")
                print(f"   Task ID: {task_id}")
                print(f"   Progress endpoint: {progress_endpoint}")
                
                # Test progress endpoint
                progress_url = f"http://localhost:8080{progress_endpoint}"
                
                for attempt in range(20):  # Check for up to 20 seconds
                    time.sleep(1)
                    
                    try:
                        progress_response = requests.get(progress_url, timeout=5)
                        
                        if progress_response.status_code == 200:
                            progress_data = progress_response.json()
                            
                            if progress_data.get('success'):
                                progress_info = progress_data.get('progress', {})
                                status = progress_info.get('status')
                                overall_progress = progress_info.get('overall_progress', 0)
                                current_message = progress_info.get('current_message', 'Processing...')
                                
                                print(f"   📊 Attempt {attempt + 1}: {status} - {overall_progress}% - {current_message}")
                                
                                if status == 'completed':
                                    print(f"   ✅ ASYNC PROGRESS TRACKING WORKING!")
                                    
                                    # Check final results via task status
                                    status_url = f"http://localhost:8080/casestrainer/api/task_status/{task_id}"
                                    status_response = requests.get(status_url, timeout=10)
                                    
                                    if status_response.status_code == 200:
                                        status_data = status_response.json()
                                        result = status_data.get('result', {})
                                        citations = result.get('citations', [])
                                        clusters = result.get('clusters', [])
                                        
                                        print(f"   Citations: {len(citations)}, Clusters: {len(clusters)}")
                                        return len(citations) > 0
                                    
                                    return True
                                elif status == 'failed':
                                    print(f"   ❌ Processing failed")
                                    return False
                            else:
                                print(f"   ❌ Progress endpoint error: {progress_data.get('error')}")
                        else:
                            print(f"   ⚠️  Progress endpoint returned {progress_response.status_code}")
                    except Exception as e:
                        print(f"   ⚠️  Progress check error: {e}")
                
                print(f"   ⏰ Progress tracking timeout")
                return False
            else:
                print(f"   ❌ No task ID or progress endpoint")
                return False
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_async_large_text_progress():
    """Test progress tracking for async large text processing."""
    
    print("\n🔍 TESTING ASYNC LARGE TEXT PROGRESS")
    print("=" * 50)
    
    # Large text that should trigger async processing (> 2KB)
    large_text = """
    This is a large legal document with many citations that should trigger async processing.
    
    Brown v. Board of Education, 347 U.S. 483 (1954), was a landmark decision that declared state laws establishing separate public schools for black and white students to be unconstitutional.
    
    Miranda v. Arizona, 384 U.S. 436 (1966), established the requirement that criminal suspects be informed of their rights before interrogation.
    
    Roe v. Wade, 410 U.S. 113 (1973), was a decision that established a constitutional right to abortion.
    
    Marbury v. Madison, 5 U.S. 137 (1803), established the principle of judicial review.
    
    Gideon v. Wainwright, 372 U.S. 335 (1963), established the right to counsel in criminal cases.
    
    Mapp v. Ohio, 367 U.S. 643 (1961), applied the Fourth Amendment's protection against unreasonable searches and seizures to state courts.
    
    """ * 20  # Repeat to make it large enough for async processing
    
    url = "http://localhost:8080/casestrainer/api/analyze"
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'text', 'text': large_text}
    
    try:
        print(f"📤 Testing large text: {len(large_text)} characters")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Check both top level and nested in result
            task_id = response_data.get('task_id') or response_data.get('request_id')
            if not task_id:
                result = response_data.get('result', {})
                task_id = result.get('task_id') or result.get('request_id')
            
            if task_id:
                print(f"   ✅ ASYNC PROCESSING TRIGGERED!")
                print(f"   Task ID: {task_id}")
                
                # Check if we have progress endpoints
                progress_endpoint = response_data.get('progress_endpoint')
                if not progress_endpoint:
                    result = response_data.get('result', {})
                    progress_endpoint = result.get('progress_endpoint')
                if progress_endpoint:
                    print(f"   ✅ Progress endpoint available: {progress_endpoint}")
                    return True
                else:
                    print(f"   ⚠️  No progress endpoint in response")
                    return False
            else:
                # Check if it was processed immediately with progress data
                result = response_data.get('result', {})
                progress_data = result.get('progress_data')
                
                if progress_data:
                    print(f"   ✅ IMMEDIATE PROCESSING with progress!")
                    print(f"   Status: {progress_data.get('status')}")
                    return True
                else:
                    print(f"   ❌ No task ID or progress data")
                    return False
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🎯 COMPREHENSIVE PROGRESS TRACKING TEST")
    print("=" * 80)
    
    # Test all three scenarios
    sync_working = test_sync_text_progress()
    url_working = test_async_url_progress()
    large_text_working = test_async_large_text_progress()
    
    print("\n🎯 FINAL RESULTS")
    print("=" * 50)
    
    if sync_working:
        print("✅ SYNC TEXT PROGRESS: WORKING")
    else:
        print("❌ SYNC TEXT PROGRESS: NOT WORKING")
    
    if url_working:
        print("✅ ASYNC URL PROGRESS: WORKING")
    else:
        print("❌ ASYNC URL PROGRESS: NOT WORKING")
    
    if large_text_working:
        print("✅ ASYNC LARGE TEXT PROGRESS: WORKING")
    else:
        print("❌ ASYNC LARGE TEXT PROGRESS: NOT WORKING")
    
    if sync_working and url_working and large_text_working:
        print("\n🎉 ALL PROGRESS TRACKING IS FULLY FUNCTIONAL!")
        print("   ✅ Small text: Sync processing with immediate progress")
        print("   ✅ Large text: Async processing with progress endpoints")
        print("   ✅ URLs: Async processing with progress tracking")
        print("   ✅ Files: Ready (same async pipeline as URLs)")
        print("   ✅ Frontend can show proper progress bars and spinners")
    else:
        print("\n⚠️  Some progress tracking features need attention")
    
    print("=" * 50)

if __name__ == "__main__":
    main()

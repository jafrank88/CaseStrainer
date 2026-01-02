#!/usr/bin/env python3
"""
Force async processing test
"""

import requests
import json
import time

def test_force_async():
    """Test async processing with very large document"""
    
    # Create a very large document (100KB) to definitely trigger async
    large_text = "This is a test legal document with many citations. " * 5000
    large_text += """
    In Smith v. Jones, 123 F.3d 456 (9th Cir. 1998), the court ruled on corporate liability.
    In Johnson v. Smith, 789 F.2d 234 (D.C. Cir. 1986), constitutional questions were addressed.
    In Brown v. Board of Education, 347 U.S. 483 (1954), civil rights precedent was established.
    """ * 1000
    
    print("🧪 Testing force async processing...")
    print(f"📝 Test text length: {len(large_text)} characters")
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": large_text, "extract_case_names": True}
    
    try:
        print("\n📡 Submitting request (expecting async)...")
        
        start_time = time.time()
        response = requests.post(url, json=data, timeout=10)  # Should return quickly for async
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Request completed in {elapsed_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📄 Response keys: {list(result.keys())}")
            
            task_id = result.get("task_id")
            processing_mode = result.get("metadata", {}).get("processing_mode", "unknown")
            
            print(f"🆔 Task ID: {task_id}")
            print(f"📊 Processing mode: {processing_mode}")
            
            if task_id and (processing_mode == "async" or processing_mode == "queued"):
                print("✅ Async processing triggered!")
                
                # Test progress polling
                progress_url = f"https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{task_id}"
                
                for i in range(10):  # Poll for 10 seconds
                    try:
                        progress_response = requests.get(progress_url, timeout=5)
                        if progress_response.status_code == 200:
                            progress_data = progress_response.json()
                            progress = progress_data.get("progress_data", {}).get("progress", 0)
                            message = progress_data.get("progress_data", {}).get("message", "")
                            status = progress_data.get("progress_data", {}).get("status", "")
                            
                            print(f"📊 Progress check {i+1}: {progress}% - {status} - {message}")
                        else:
                            print(f"❌ Progress check {i+1} failed: {progress_response.status_code}")
                    except Exception as e:
                        print(f"⚠️  Progress check {i+1} error: {e}")
                    
                    time.sleep(1)
                
                return True
            else:
                print(f"❌ Expected async processing but got: {processing_mode}")
                if task_id:
                    print(f"   Task ID: {task_id}")
                return False
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - likely falling back to sync processing")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_force_async()

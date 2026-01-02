#!/usr/bin/env python3
"""
Test async with smaller document to avoid timeout
"""

import requests
import json
import time
import threading

def monitor_progress_async(task_id, stop_event, results):
    """Monitor progress in real-time during async processing"""
    progress_url = f"https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{task_id}"
    
    while not stop_event.is_set():
        try:
            progress_response = requests.get(progress_url, timeout=2)
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                progress = progress_data.get("progress_data", {}).get("progress", 0)
                message = progress_data.get("progress_data", {}).get("message", "")
                status = progress_data.get("progress_data", {}).get("status", "")
                
                result = f"Progress: {progress}% - {status} - {message}"
                results.append(result)
                print(f"📊 {result}")
        except Exception as e:
            print(f"⚠️  Progress polling error: {e}")
        
        time.sleep(2)

def test_medium_async():
    """Test async with medium-sized document"""
    
    # Create a document just above the 5KB threshold
    medium_text = """
    This is a comprehensive legal analysis document that contains numerous citations from various jurisdictions and time periods. 
    In the landmark case of Smith v. Jones, 123 F.3d 456 (9th Cir. 1998), the court established important precedent regarding corporate liability.
    The Supreme Court in Johnson v. Smith, 789 F.2d 234 (D.C. Cir. 1986), addressed constitutional questions that would shape future jurisprudence.
    Brown v. Board of Education, 347 U.S. 483 (1954), represents one of the most significant civil rights decisions in American history.
    United States v. Carpenter, 585 U.S. ___ (2018), demonstrates the Court's modern approach to digital privacy rights.
    Circuit City v. Adams, 456 F.3d 789 (3d Cir. 2011), considered complex contractual disputes under federal law.
    Miller v. California, 413 U.S. 15 (1973), established the three-pronged test for obscenity that remains influential today.
    Roe v. Wade, 410 U.S. 113 (1973), recognized a woman's constitutional right to privacy in reproductive decisions.
    District Court v. Plaintiff, 234 F. Supp. 567 (N.D. Cal. 2000), made an important ruling on civil procedure matters.
    Circuit Appeal v. Defendant, 345 F.3d 890 (5th Cir. 2003), affirmed the lower court's decision on statutory interpretation.
    Marbury v. Madison, 5 U.S. (1 Cranch) 137 (1803), established the principle of judicial review that underpins American constitutional law.
    """ * 100  # About 30KB - should trigger async but not timeout
    
    print("🧪 Testing medium async document...")
    print(f"📝 Test text length: {len(medium_text)} characters")
    
    # Submit request
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": medium_text, "extract_case_names": True}
    
    try:
        print("\n📡 Submitting request...")
        
        # Submit the main request
        start_time = time.time()
        response = requests.post(url, json=data, timeout=10)  # Short timeout for async
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Request completed in {elapsed_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id") or result.get("request_id")
            processing_mode = result.get("metadata", {}).get("processing_mode", "unknown")
            
            print(f"🆔 Task ID: {task_id}")
            print(f"📊 Processing mode: {processing_mode}")
            
            if processing_mode == "async" or "async" in processing_mode.lower():
                print("✅ Async processing triggered! Starting progress monitoring...")
                
                # Start progress monitoring in background
                stop_event = threading.Event()
                results = []
                monitor_thread = threading.Thread(target=monitor_progress_async, args=(task_id, stop_event, results))
                monitor_thread.start()
                
                # Monitor for up to 30 seconds
                for i in range(30):
                    time.sleep(1)
                    
                    # Check if task is complete by getting final result
                    try:
                        progress_response = requests.get(f"https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{task_id}", timeout=5)
                        if progress_response.status_code == 200:
                            progress_data = progress_response.json()
                            status = progress_data.get("progress_data", {}).get("status", "")
                            progress = progress_data.get("progress_data", {}).get("progress", 0)
                            
                            if status == "completed" or progress >= 100:
                                print(f"\n✅ Task completed!")
                                break
                    except:
                        pass
                
                # Stop monitoring
                stop_event.set()
                monitor_thread.join(timeout=2)
                
                print(f"\n📈 Total progress updates captured: {len(results)}")
                unique_results = list(set(results))  # Remove duplicates
                print(f"📈 Unique progress updates: {len(unique_results)}")
                
                for i, result in enumerate(unique_results[:5]):  # Show first 5
                    print(f"  {i+1}. {result}")
                
                return len(unique_results) > 1
            else:
                print(f"⚠️  Expected async processing but got: {processing_mode}")
                return False
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - this might indicate sync processing instead of async")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_medium_async()
    
    if success:
        print("\n✅ Async progress test completed!")
    else:
        print("\n❌ Async progress test failed!")

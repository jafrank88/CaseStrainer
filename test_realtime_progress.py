#!/usr/bin/env python3
"""
Test if progress updates are available DURING sync processing
"""

import requests
import json
import time
import threading

def monitor_progress_sync(task_id, stop_event, results):
    """Monitor progress in real-time during sync processing"""
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
        except:
            pass
        
        time.sleep(0.5)

def test_sync_progress_realtime():
    """Test if we can get progress updates DURING sync processing"""
    
    # Create a medium-sized document
    test_text = """
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
    """ * 2
    
    print("🧪 Testing real-time progress during sync processing...")
    print(f"📝 Test text length: {len(test_text)} characters")
    
    # Submit request
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": test_text, "extract_case_names": True}
    
    try:
        print("\n📡 Submitting request and starting progress monitoring...")
        
        # Start progress monitoring in background
        stop_event = threading.Event()
        results = []
        monitor_thread = threading.Thread(target=monitor_progress_sync, args=("placeholder", stop_event, results))
        monitor_thread.start()
        
        # Submit the main request
        start_time = time.time()
        response = requests.post(url, json=data, timeout=120)
        elapsed_time = time.time() - start_time
        
        # Stop monitoring
        stop_event.set()
        monitor_thread.join(timeout=1)
        
        if response.status_code == 200:
            result = response.json()
            request_id = result.get("request_id")
            
            print(f"\n✅ Request completed in {elapsed_time:.2f} seconds")
            print(f"🆔 Request ID: {request_id}")
            print(f"📊 Processing mode: {result.get('metadata', {}).get('processing_mode', 'unknown')}")
            print(f"📊 Found {len(result.get('citations', []))} citations")
            
            # Now get the final progress
            progress_url = f"https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{request_id}"
            progress_response = requests.get(progress_url, timeout=5)
            
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                print(f"\n📊 Final progress: {progress_data}")
            
            print(f"\n📈 Total progress updates captured: {len(results)}")
            unique_results = list(set(results))  # Remove duplicates
            print(f"📈 Unique progress updates: {len(unique_results)}")
            
            for i, result in enumerate(unique_results):
                print(f"  {i+1}. {result}")
            
            return len(unique_results) > 1
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_sync_progress_realtime()
    
    if success:
        print("\n✅ Real-time progress test completed!")
    else:
        print("\n❌ Real-time progress test failed!")

#!/usr/bin/env python3
"""
Test sync progress tracking
"""

import requests
import json
import time
import threading

def monitor_progress(task_id, stop_event):
    """Monitor progress updates in a separate thread"""
    progress_url = f"http://localhost:5000/casestrainer/api/analyze/progress/{task_id}"
    updates = []
    
    while not stop_event.is_set():
        try:
            response = requests.get(progress_url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                progress = data.get('progress', 0)
                message = data.get('message', '')
                status = data.get('status', '')
                
                update = f"Progress: {progress}% - {status} - {message}"
                if update not in updates:  # Avoid duplicate updates
                    updates.append(update)
                    print(f" {update}")
            
        except Exception as e:
            pass  # Ignore errors during polling
        
        time.sleep(0.5)  # Poll every 500ms
    
    return updates

def test_sync_progress():
    """Test sync processing with progress monitoring"""
    
    # Create a medium-sized document that will take some time but process synchronously
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
    """ * 5  # Repeat to make it larger but not too large
    
    print(" Testing sync processing with progress monitoring...")
    print(f" Test text length: {len(test_text)} characters")
    
    # Send to API
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": test_text, "extract_case_names": True}
    
    try:
        print("\n Sending request to API...")
        start_time = time.time()
        
        response = requests.post(url, json=data, timeout=120)
        response.raise_for_status()
        
        elapsed_time = time.time() - start_time
        result = response.json()
        
        print(f"\n  Request completed in {elapsed_time:.2f} seconds")
        
        # Check results
        processing_mode = result.get("metadata", {}).get("processing_mode", "unknown")
        print(f" Processing mode: {processing_mode}")
        
        citations = result.get("citations", [])
        print(f" Found {len(citations)} citations")
        
        # Check if there's a task ID for progress tracking
        task_id = result.get("task_id") or result.get("metadata", {}).get("request_id")
        
        if task_id:
            print(f" Task ID: {task_id}")
            
            # Now test the progress endpoint
            progress_url = f"http://localhost:5000/casestrainer/api/analyze/progress/{task_id}"
            progress_response = requests.get(progress_url, timeout=5)
            
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                print(f" Final progress: {progress_data}")
            else:
                print(f"  Progress endpoint returned: {progress_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f" Error: {e}")
        return False

if __name__ == "__main__":
    success = test_sync_progress()
    
    if success:
        print("\n Sync progress test completed!")
        print("\n✅ Sync progress test completed!")
    else:
        print("\n❌ Sync progress test failed!")

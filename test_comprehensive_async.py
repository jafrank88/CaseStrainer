#!/usr/bin/env python3
"""
Comprehensive async progress tracking test
"""

import requests
import json
import time
import threading

def monitor_async_progress(task_id, stop_event, results):
    """Monitor async progress in real-time"""
    progress_url = f"https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{task_id}"
    
    while not stop_event.is_set():
        try:
            progress_response = requests.get(progress_url, timeout=3)
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                progress = progress_data.get("progress_data", {}).get("progress", 0)
                message = progress_data.get("progress_data", {}).get("message", "")
                status = progress_data.get("progress_data", {}).get("status", "")
                results_count = progress_data.get("progress_data", {}).get("results_count", 0)
                
                result = f"Progress: {progress}% - {status} - {message} ({results_count} results)"
                results.append(result)
                print(f"📊 {result}")
                
                # Check if completed
                if status == "completed" or progress >= 100:
                    print(f"✅ Async task completed!")
                    stop_event.set()
                    return True
        except Exception as e:
            print(f"⚠️  Progress polling error: {e}")
        
        time.sleep(2)
    
    return False

def test_comprehensive_async():
    """Test comprehensive async progress tracking"""
    
    # Create a large document (100KB) to trigger async processing
    large_text = """
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
    """ * 800  # About 230KB
    
    print("🧪 Testing comprehensive async progress tracking...")
    print(f"📝 Test text length: {len(large_text)} characters")
    
    # Submit request
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": large_text, "extract_case_names": True}
    
    try:
        print("\n📡 Submitting async request...")
        
        start_time = time.time()
        response = requests.post(url, json=data, timeout=10)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Request submitted in {elapsed_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            processing_mode = result.get("metadata", {}).get("processing_mode", "unknown")
            
            print(f"🆔 Task ID: {task_id}")
            print(f"📊 Processing mode: {processing_mode}")
            
            if task_id and (processing_mode == "async" or processing_mode == "queued"):
                print("✅ Async processing successfully triggered!")
                print("🔄 Starting real-time progress monitoring...\n")
                
                # Start progress monitoring
                stop_event = threading.Event()
                results = []
                monitor_thread = threading.Thread(
                    target=monitor_async_progress, 
                    args=(task_id, stop_event, results)
                )
                monitor_thread.start()
                
                # Wait for completion or timeout (2 minutes max)
                monitor_thread.join(timeout=120)
                
                if monitor_thread.is_alive():
                    print("⏰ Async task taking longer than 2 minutes, stopping monitoring")
                    stop_event.set()
                    monitor_thread.join(timeout=5)
                
                print(f"\n📈 Total progress updates captured: {len(results)}")
                unique_results = list(set(results))
                print(f"📈 Unique progress updates: {len(unique_results)}")
                
                print("\n🔄 Progress timeline:")
                for i, result in enumerate(unique_results[:10]):  # Show first 10
                    print(f"  {i+1}. {result}")
                
                if len(unique_results) > 5:
                    print("✅ Async progress tracking is working correctly!")
                    return True
                else:
                    print("⚠️  Limited progress updates captured")
                    return False
            else:
                print(f"❌ Expected async processing but got: {processing_mode}")
                return False
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_comprehensive_async()
    
    if success:
        print("\n🎉 Comprehensive async progress test PASSED!")
    else:
        print("\n❌ Comprehensive async progress test FAILED!")

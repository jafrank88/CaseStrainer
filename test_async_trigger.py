#!/usr/bin/env python3
"""
Quick test to check async processing trigger
"""

import requests
import json
import time

def test_async_trigger():
    """Test if async processing is triggered"""
    
    # Create a document that will trigger async processing (>50KB)
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
    """ * 200  # About 288KB - should trigger async
    
    print("🧪 Testing async processing trigger...")
    print(f"📝 Test text length: {len(large_text)} characters")
    
    # Submit request
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": large_text, "extract_case_names": True}
    
    try:
        print("\n📡 Submitting request...")
        
        # Submit the main request with longer timeout
        start_time = time.time()
        response = requests.post(url, json=data, timeout=60)
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
                print("✅ Async processing triggered!")
                
                # Test progress endpoint
                progress_url = f"https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{task_id}"
                progress_response = requests.get(progress_url, timeout=10)
                
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    progress = progress_data.get("progress_data", {}).get("progress", 0)
                    message = progress_data.get("progress_data", {}).get("message", "")
                    status = progress_data.get("progress_data", {}).get("status", "")
                    
                    print(f"📊 Initial progress: {progress}% - {status} - {message}")
                    return True
                else:
                    print(f"❌ Progress endpoint failed: {progress_response.status_code}")
                    return False
            else:
                print(f"⚠️  Expected async processing but got: {processing_mode}")
                print("This might be sync processing or the threshold is different")
                return False
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - this might indicate async processing is working")
        print("   (Async requests should return quickly with a task_id)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_async_trigger()

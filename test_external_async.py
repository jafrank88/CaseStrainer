#!/usr/bin/env python3
"""
Test async progress on external site
"""

import requests
import json
import time

def test_external_async():
    """Test async progress on external site"""
    
    # Medium-sized document to trigger async
    text = """
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
    """ * 200  # About 60KB
    
    print("🌐 Testing async progress on external site...")
    print(f"📝 Text length: {len(text)} characters")
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": text, "extract_case_names": True}
    
    try:
        print("\n📡 Submitting request to external site...")
        
        start_time = time.time()
        response = requests.post(url, json=data, timeout=10)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Request completed in {elapsed_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            processing_mode = result.get("metadata", {}).get("processing_mode", "unknown")
            
            print(f"🆔 Task ID: {task_id}")
            print(f"📊 Processing mode: {processing_mode}")
            
            if task_id and (processing_mode == "async" or processing_mode == "queued"):
                print("✅ Async processing working on external site!")
                
                # Test progress endpoint
                progress_url = f"https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{task_id}"
                
                print("\n🔄 Testing progress polling...")
                for i in range(5):  # Test 5 progress updates
                    try:
                        progress_response = requests.get(progress_url, timeout=5)
                        if progress_response.status_code == 200:
                            progress_data = progress_response.json()
                            progress = progress_data.get("progress_data", {}).get("progress", 0)
                            message = progress_data.get("progress_data", {}).get("message", "")
                            status = progress_data.get("progress_data", {}).get("status", "")
                            
                            print(f"📊 Update {i+1}: {progress}% - {status} - {message}")
                        else:
                            print(f"❌ Progress check {i+1} failed: {progress_response.status_code}")
                    except Exception as e:
                        print(f"⚠️  Progress check {i+1} error: {e}")
                    
                    time.sleep(2)
                
                return True
            else:
                print(f"⚠️  Processing mode: {processing_mode}")
                return False
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_external_async()
    
    if success:
        print("\n🎉 External async progress test PASSED!")
    else:
        print("\n❌ External async progress test FAILED!")

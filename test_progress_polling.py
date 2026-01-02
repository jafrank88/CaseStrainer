#!/usr/bin/env python3
"""
Test progress polling like the frontend does
"""

import requests
import json
import time

def test_progress_polling():
    """Test progress polling with a real request"""
    
    # Create a test document that will take some time
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
    """ * 3  # Make it larger to take more time
    
    print("🧪 Testing progress polling like frontend...")
    print(f"📝 Test text length: {len(test_text)} characters")
    
    # Submit request
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": test_text, "extract_case_names": True, "client_request_id": "test-polling-123"}
    
    try:
        print("\n📡 Submitting request...")
        response = requests.post(url, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            request_id = result.get("request_id")
            
            print(f"✅ Request submitted with ID: {request_id}")
            
            # Now poll for progress like the frontend does
            progress_url = f"https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{request_id}"
            
            print("\n🔄 Starting progress polling...")
            updates = []
            
            for i in range(20):  # Poll for up to 20 seconds
                try:
                    progress_response = requests.get(progress_url, timeout=5)
                    
                    if progress_response.status_code == 200:
                        progress_data = progress_response.json()
                        progress_percent = progress_data.get("progress_data", {}).get("progress", 0)
                        message = progress_data.get("progress_data", {}).get("message", "")
                        status = progress_data.get("progress_data", {}).get("status", "")
                        
                        update = f"Progress: {progress_percent}% - {status} - {message}"
                        if update not in updates:
                            updates.append(update)
                            print(f"📊 {update}")
                    
                except Exception as e:
                    print(f"⚠️  Poll error: {e}")
                
                time.sleep(1)
            
            print(f"\n📈 Total unique updates: {len(updates)}")
            for update in updates:
                print(f"  • {update}")
            
            return len(updates) > 1
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_progress_polling()
    
    if success:
        print("\n✅ Progress polling test completed!")
    else:
        print("\n❌ Progress polling test failed!")

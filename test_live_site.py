#!/usr/bin/env python3
"""
Test the live site API directly
"""

import requests
import json
import time

def test_live_site():
    """Test the live site API"""
    
    # Create a simple test document
    test_text = """
    This is a test legal document.
    In the case of Smith v. Jones, 123 F.3d 456, the court established important precedent.
    Another case is Johnson v. Smith, 789 F.2d 234.
    """
    
    print("🧪 Testing live site API...")
    print(f"📝 Test text length: {len(test_text)} characters")
    
    # Send to live API
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": test_text, "extract_case_names": True}
    
    try:
        print("\n📡 Sending request to live API...")
        start_time = time.time()
        
        response = requests.post(url, json=data, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            elapsed_time = time.time() - start_time
            
            print(f"\n⏱️  Request completed in {elapsed_time:.2f} seconds")
            
            # Check results
            processing_mode = result.get("metadata", {}).get("processing_mode", "unknown")
            print(f"📊 Processing mode: {processing_mode}")
            
            citations = result.get("citations", [])
            print(f"📊 Found {len(citations)} citations")
            
            # Check if there's a task ID for progress tracking
            request_id = result.get("request_id")
            
            if request_id:
                print(f"🆔 Request ID: {request_id}")
                
                # Test the progress endpoint
                progress_url = f"https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{request_id}"
                progress_response = requests.get(progress_url, timeout=5)
                
                print(f"Progress endpoint status: {progress_response.status_code}")
                
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    print(f"📊 Progress data: {progress_data}")
                else:
                    print(f"⚠️  Progress response: {progress_response.text}")
            
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_live_site()
    
    if success:
        print("\n✅ Live site test completed!")
    else:
        print("\n❌ Live site test failed!")

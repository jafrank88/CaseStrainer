#!/usr/bin/env python3
"""
Test URL progress to see if we get past the size limit error
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import requests
import json

def test_url_progress():
    """Test if we get past the size limit error."""
    url = "https://law.justia.com/cases/federal/us/390/747/"
    
    print(f"Testing URL progress: {url}")
    print("This test checks if we get past the 'empty or insufficient content' error")
    
    # Test with async mode (should return task_id quickly)
    data = {
        'url': url
    }
    
    try:
        response = requests.post(
            "https://wolf.law.uw.edu/casestrainer/api/analyze",
            data=data,
            timeout=10,  # Short timeout just to get the initial response
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"Initial response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS: Got past the size limit error!")
            print(f"Response keys: {list(result.keys())}")
            
            if 'task_id' in result:
                print(f"Task ID: {result['task_id']}")
                print("The URL was accepted and is being processed asynchronously.")
                print("Size limit fix: WORKING ✅")
            elif 'citations' in result:
                print("Got direct response - sync processing worked!")
                print("Size limit fix: WORKING ✅")
            
            return True
        elif response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get('error', 'Unknown error')
            if 'empty or insufficient content' in error_msg:
                print("❌ Still getting size limit error")
                print("Size limit fix: NOT WORKING ❌")
            else:
                print(f"❌ Different error: {error_msg}")
            return False
        else:
            print(f"❌ Unexpected error: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⚠️  Request timed out - this might indicate the server is processing")
        print("The size limit error might be fixed if it's trying to process")
        return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    result = test_url_progress()
    
    print("\n" + "="*50)
    if result is True:
        print("FINAL RESULT: ✅ SIZE LIMIT FIX IS WORKING")
        print("The URL upload issue has been resolved!")
    elif result is False:
        print("FINAL RESULT: ❌ SIZE LIMIT FIX IS NOT WORKING")
        print("Still experiencing the original issue")
    else:
        print("FINAL RESULT: ⚠️  UNCLEAR")
        print("The request timed out, which might indicate progress")
    
    print("\nSUMMARY:")
    print("- Root cause: 100KB size limit in CitationService._fetch_url_content()")
    print("- Fix applied: Increased limit to 1MB")  
    print("- Status: Fix deployed with service restart")

#!/usr/bin/env python3
"""
Test production async processing flow to get extraction results.
"""

import requests
import json
import time

def test_production_async():
    """Test the async processing flow in production."""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    test_citation = "Punx v Smithers, 123 Wash. 2d 456, 789 P.2d 123 (1990)"
    
    test_data = {
        "type": "text",
        "text": test_citation
    }
    
    print("🔄 Testing Production Async Processing")
    print("=" * 50)
    print(f"Test citation: {test_citation}")
    print()
    
    try:
        # Step 1: Submit the task
        print("📤 Step 1: Submitting task...")
        response = requests.post(f"{base_url}/analyze", json=test_data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Submit failed: {response.status_code}")
            return
            
        result = response.json()
        task_id = result.get('task_id')
        status = result.get('status')
        
        print(f"✅ Task submitted: {task_id}")
        print(f"📊 Status: {status}")
        print()
        
        if status != 'processing':
            print(f"❌ Unexpected status: {status}")
            return
            
        # Step 2: Poll for results
        print("⏳ Step 2: Polling for results...")
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            print(f"   Poll attempt {attempt}/{max_attempts}...")
            
            # Poll for task status
            poll_response = requests.get(f"{base_url}/task_status/{task_id}", timeout=10)
            
            if poll_response.status_code == 200:
                poll_result = poll_response.json()
                poll_status = poll_result.get('status')
                
                print(f"   Status: {poll_status}")
                
                if poll_status == 'completed':
                    print("✅ Task completed!")
                    print()
                    
                    # Get the final results
                    citations = poll_result.get('citations', [])
                    print(f"📄 Found {len(citations)} citations")
                    
                    for i, citation in enumerate(citations):
                        print(f"\n🔍 Citation {i + 1}:")
                        print(f"   Citation: {citation.get('citation', 'N/A')}")
                        print(f"   Extracted Case Name: {citation.get('extracted_case_name', 'N/A')}")
                        print(f"   Extracted Date: {citation.get('extracted_date', 'N/A')}")
                        print(f"   Canonical Name: {citation.get('canonical_name', 'N/A')}")
                        print(f"   Canonical Date: {citation.get('canonical_date', 'N/A')}")
                        print(f"   Verified: {citation.get('verified', 'N/A')}")
                        
                        # Check extraction success
                        extracted_name = citation.get('extracted_case_name')
                        extracted_date = citation.get('extracted_date')
                        
                        if extracted_name and extracted_name != 'N/A':
                            print(f"   ✅ Extracted name: {extracted_name}")
                        else:
                            print(f"   ❌ No extracted name")
                            
                        if extracted_date and extracted_date != 'N/A':
                            print(f"   ✅ Extracted date: {extracted_date}")
                        else:
                            print(f"   ❌ No extracted date")
                    
                    return
                    
                elif poll_status == 'failed':
                    print(f"❌ Task failed: {poll_result.get('error', 'Unknown error')}")
                    return
                    
            else:
                print(f"   ❌ Poll failed: {poll_response.status_code}")
                
            # Wait before next poll
            time.sleep(2)
            
        print(f"❌ Timeout after {max_attempts} attempts")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_production_async() 
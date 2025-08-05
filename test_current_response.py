#!/usr/bin/env python3
"""
Test script to check the current response structure
"""
import requests
import json

def test_current_response():
    task_id = "89a21c66-4802-4712-8fbe-322e3827003d"
    url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
    
    print(f"Testing current response for: {task_id}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check the structure
            print(f"Response keys: {list(data.keys())}")
            print(f"Status field: '{data.get('status')}'")
            print(f"Status type: {type(data.get('status'))}")
            
            if 'result' in data:
                result = data['result']
                print(f"Result keys: {list(result.keys())}")
                print(f"Citations count: {len(result.get('citations', []))}")
                print(f"Clusters count: {len(result.get('clusters', []))}")
            else:
                print("No 'result' field found in response")
                print(f"Direct citations count: {len(data.get('citations', []))}")
                print(f"Direct clusters count: {len(data.get('clusters', []))}")
            
            # Check what the frontend expects
            print("\nFrontend expectations:")
            print(f"response.data.status === 'completed': {data.get('status') == 'completed'}")
            print(f"response.data.status === 'finished': {data.get('status') == 'finished'}")
            if 'result' in data:
                print(f"response.data.result?.citations?.length: {len(result.get('citations', []))}")
            else:
                print(f"response.data.citations?.length: {len(data.get('citations', []))}")
                
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_current_response() 
#!/usr/bin/env python3
"""Test script for URL endpoint"""
import requests
import json
import time

def check_task_status(task_id):
    """Poll task status until complete"""
    url = f'http://localhost:5000/casestrainer/api/task_status/{task_id}'
    max_wait = 60  # Wait up to 60 seconds
    start = time.time()
    
    while time.time() - start < max_wait:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                print(f'  Task status: {status}')
                
                if status == 'completed':
                    return data
                elif status == 'failed':
                    print(f'  Task failed: {data.get("error", "Unknown error")}')
                    return data
            elif response.status_code == 404:
                print(f'  Task not found (may still be processing)...')
            else:
                print(f'  Unexpected status: {response.status_code}')
            
            time.sleep(2)  # Wait 2 seconds before checking again
        except Exception as e:
            print(f'  Error checking status: {e}')
            time.sleep(2)
    
    print(f'  Timeout waiting for task completion')
    return None

def test_url_endpoint():
    url = 'http://localhost:5000/casestrainer/api/analyze'
    payload = {
        'type': 'url',
        'url': 'https://www.courts.wa.gov/opinions/pdf/1031351.pdf',
        'client_request_id': f'test-url-{int(time.time())}'
    }
    
    print('Testing URL endpoint...')
    print(f'URL: {payload["url"]}')
    print('Sending request...')
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=120
        )
        
        print(f'\nStatus Code: {response.status_code}')
        print(f'Content-Type: {response.headers.get("content-type", "unknown")}')
        
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
        else:
            data = {'raw_response': response.text[:500]}
        
        print(f'\nResponse Keys: {list(data.keys())}')
        print(f'Status: {data.get("status", "unknown")}')
        print(f'Task ID: {data.get("task_id", "None")}')
        
        # If async, poll for results
        if data.get('status') == 'processing' or data.get('task_id'):
            task_id = data.get('task_id') or data.get('request_id')
            print(f'\n📋 Polling for async task results (task_id: {task_id})...')
            result = check_task_status(task_id)
            
            if result:
                data = result
            
        print(f'\nCitations Count: {len(data.get("citations", []))}')
        print(f'Clusters Count: {len(data.get("clusters", []))}')
        print(f'Error: {data.get("error", "None")}')
        print(f'Success: {data.get("success", "Not specified")}')
        
        if data.get('citations'):
            print(f'\n✅ First Citation Sample:')
            print(json.dumps(data['citations'][0], indent=2)[:800])
        
        if data.get('clusters'):
            print(f'\n✅ First Cluster Sample:')
            print(json.dumps(data['clusters'][0], indent=2)[:800])
            
        if data.get('error'):
            print(f'\n❌ Full Error Response:')
            print(json.dumps(data, indent=2))
            
    except requests.exceptions.Timeout:
        print('ERROR: Request timed out after 120 seconds')
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_url_endpoint()

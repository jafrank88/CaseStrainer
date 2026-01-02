#!/usr/bin/env python3
import requests
import os
import json

api_key = os.environ.get('COURTLISTENER_API_KEY')
url = 'https://www.courtlistener.com/api/rest/v4/citation-lookup/'
headers = {'Authorization': f'Token {api_key}', 'Content-Type': 'application/json'}

test_citations = ['547 P.2d 1207', '32 So. 3d 496']

print('Testing CourtListener API directly:')
print('='*60)

for citation in test_citations:
    print(f'Testing citation: {citation}')
    payload = {'text': citation}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f'SUCCESS: {response.status_code}')
            
            if isinstance(data, list) and len(data) > 0:
                for i, result in enumerate(data):
                    print(f'  Result {i+1}:')
                    print(f'    Citation: {result.get("citation", "N/A")}')
                    print(f'    Case Name: {result.get("caseName", "N/A")}')
                    print(f'    Date Filed: {result.get("dateFiled", "N/A")}')
                    print(f'    URL: {result.get("absolute_url", "N/A")}')
                    print()
            else:
                print(f'  No results found')
        else:
            print(f'FAILED: {response.status_code}')
            print(f'Response: {response.text}')
            
    except Exception as e:
        print(f'ERROR: {e}')










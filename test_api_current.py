#!/usr/bin/env python3
"""
Test the current API to see what extraction results we're getting.
"""

import requests
import json

def test_api():
    # Test the API with our test paragraph
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)."""

    try:
        response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                               json={'text': test_text, 'type': 'text'}, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print('API Response Status: 200')
            print(f'Citations found: {len(data.get("citations", []))}')
            print(f'Clusters: {len(data.get("clusters", []))}')
            print(f'Full response keys: {list(data.keys())}')
            
            # Check the result field
            if 'result' in data:
                result = data['result']
                print(f'Result keys: {list(result.keys()) if isinstance(result, dict) else "Not a dict"}')
                if isinstance(result, dict):
                    print(f'Result citations: {len(result.get("citations", []))}')
                    print(f'Result clusters: {len(result.get("clusters", []))}')
            
            print('\nCitations from result:')
            result_citations = data.get('result', {}).get('citations', [])
            for i, citation in enumerate(result_citations[:6], 1):
                print(f'  {i}. {citation.get("citation", "N/A")} -> {citation.get("extracted_case_name", "N/A")}')
            
            print('\nCitations from top level:')
            for i, citation in enumerate(data.get('citations', [])[:6], 1):
                print(f'  {i}. {citation.get("citation", "N/A")} -> {citation.get("extracted_case_name", "N/A")}')
            
            # Print any error messages
            if 'error' in data:
                print(f'\nError: {data["error"]}')
            if 'message' in data:
                print(f'Message: {data["message"]}')
        else:
            print(f'API Error: {response.status_code}')
            print(response.text)
    except Exception as e:
        print(f'Error calling API: {e}')

if __name__ == "__main__":
    test_api()

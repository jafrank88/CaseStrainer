#!/usr/bin/env python3
import requests
import json

def test_sample_document():
    print("Testing backend with sample document...")
    
    # Read a larger portion of the sample document to capture citations
    with open('CaseSample.txt', 'r', encoding='utf-8') as f:
        text = f.read()[:5000]  # Increased from 1000 to 5000
    
    print(f"Text length: {len(text)} characters")
    print(f"First 200 chars: {text[:200]}...")
    
    # Test the backend
    try:
        response = requests.post(
            'http://localhost:5000/casestrainer/api/analyze',
            json={'text': text},
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Backend responded successfully!")
            print(f"Status: {result.get('status', 'unknown')}")
            print("\nRaw JSON response:")
            print(json.dumps(result, indent=2))
            
            citations = result.get('citations', [])
            print(f"\nFound {len(citations)} citations")
            
            for i, citation in enumerate(citations, 1):
                print(f"\nCitation {i}:")
                print(f"  Citation: {citation.get('citation', 'N/A')}")
                print(f"  Extracted Case Name: '{citation.get('extracted_case_name', '')}'")
                print(f"  Hinted Case Name: '{citation.get('hinted_case_name', '')}'")
                print(f"  Canonical Case Name: '{citation.get('canonical_case_name', '')}'")
                print(f"  Case Name: '{citation.get('case_name', '')}'")
                
        else:
            print(f"\n❌ Backend error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_sample_document() 
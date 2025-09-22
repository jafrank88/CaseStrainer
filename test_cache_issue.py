#!/usr/bin/env python3

import requests
import json
import time

def test_cache_issue():
    """Test if the phantom citation is coming from caching."""
    
    print("CACHE ISSUE TEST")
    print("=" * 50)
    
    # Test 1: Simple text that definitely doesn't contain any P.3d citations
    simple_text = "This is a simple test with no citations at all."
    
    print("TEST 1: Simple text with no citations")
    print(f"Text: {simple_text}")
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": simple_text, "type": "text"}
    
    try:
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"Found {len(citations)} citations")
            
            # Check for phantom citations
            for citation in citations:
                citation_text = citation.get('citation', 'N/A')
                if 'P.3d' in citation_text:
                    print(f"🚨 PHANTOM in simple text: {citation_text}")
            
            if len(citations) == 0:
                print("✅ No citations found (correct)")
            
        print()
        
        # Test 2: Text with only one specific citation
        single_citation_text = "See Smith v. Jones, 123 F.3d 456 (2020)."
        
        print("TEST 2: Single citation text")
        print(f"Text: {single_citation_text}")
        
        data2 = {"text": single_citation_text, "type": "text"}
        response2 = requests.post(url, data=data2, timeout=30)
        
        if response2.status_code == 200:
            result2 = response2.json()
            citations2 = result2.get('citations', [])
            
            print(f"Found {len(citations2)} citations")
            
            for citation in citations2:
                citation_text = citation.get('citation', 'N/A')
                print(f"  {citation_text}")
                
                if citation_text == "9 P.3d 655":
                    print(f"🚨 PHANTOM in single citation test: {citation_text}")
        
        print()
        
        # Test 3: Wait and try again to see if results change
        print("TEST 3: Wait 2 seconds and retry simple text...")
        time.sleep(2)
        
        response3 = requests.post(url, data=data, timeout=30)
        
        if response3.status_code == 200:
            result3 = response3.json()
            citations3 = result3.get('citations', [])
            
            print(f"Found {len(citations3)} citations after wait")
            
            for citation in citations3:
                citation_text = citation.get('citation', 'N/A')
                if 'P.3d' in citation_text:
                    print(f"🚨 PHANTOM after wait: {citation_text}")
            
            if len(citations3) == 0:
                print("✅ Still no citations (good)")
                
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_cache_issue()

#!/usr/bin/env python3
"""
Test both nginx proxy (port 80) and direct backend (port 5001)
"""

import requests
import json

def test_nginx_proxy():
    """Test both nginx proxy and direct backend"""
    print("🌐 Nginx Proxy vs Direct Backend Test")
    print("=" * 60)
    
    # Test text
    test_text = "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that..."
    
    print(f"Test text: {test_text}")
    print(f"Length: {len(test_text)} chars, {len(test_text.split())} words")
    
    test_data = {
        "text": test_text,
        "source_type": "text"
    }
    
    # Test endpoints
    endpoints = [
        ("Nginx Proxy (Port 80)", "http://localhost/casestrainer/api/analyze"),
        ("Direct Backend (Port 5001)", "http://localhost:5001/casestrainer/api/analyze")
    ]
    
    for name, url in endpoints:
        print(f"\n{'='*20} {name} {'='*20}")
        print(f"URL: {url}")
        
        try:
            print("Sending request...")
            response = requests.post(url, json=test_data, timeout=10)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                metadata = result.get('metadata', {})
                print(f"✅ Success! Processing time: {metadata.get('processing_time', 'N/A')} seconds")
                print(f"Processor used: {metadata.get('processor_used', 'N/A')}")
                print(f"Task type: {metadata.get('task_type', 'N/A')}")
                
                # Show citations found
                citations = result.get('citations', [])
                print(f"Found {len(citations)} citations:")
                for i, citation in enumerate(citations, 1):
                    print(f"  {i}. {citation.get('citation', 'N/A')}")
                    print(f"     Case: {citation.get('extracted_case_name', 'N/A')}")
                    print(f"     Date: {citation.get('extracted_date', 'N/A')}")
                    print(f"     Canonical: {citation.get('canonical_name', 'N/A')} ({citation.get('canonical_date', 'N/A')})")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed")
        except requests.exceptions.Timeout:
            print("⏰ Request timed out")
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_nginx_proxy() 
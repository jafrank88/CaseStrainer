#!/usr/bin/env python3
"""Test PDF URL citation extraction"""

import requests
import json

def test_pdf_url():
    """Test citation extraction from PDF URL"""
    
    print("Testing PDF URL citation extraction...")
    print("URL: https://www.courts.wa.gov/opinions/pdf/863215.pdf")
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    
    # Test with PDF URL
    test_data = {
        "url": "https://www.courts.wa.gov/opinions/pdf/863215.pdf",
        "type": "url",
        "enable_verification": False  # Disable verification to speed up test
    }
    
    try:
        response = requests.post(
            f"{base_url}/analyze",
            json=test_data,
            timeout=60,  # Give more time for PDF processing
            verify=False  # Ignore SSL cert for localhost testing
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if it's an async response
            if 'task_id' in result:
                print(f"\nTask ID: {result['task_id']}")
                print("Processing asynchronously...")
                # Update check_task_status.py with new task_id
                with open('check_task_status.py', 'r') as f:
                    content = f.read()
                import re
                content = re.sub(r'task_id = ".*?"', f'task_id = "{result["task_id"]}"', content)
                with open('check_task_status.py', 'w') as f:
                    f.write(content)
            elif 'citations' in result:
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                print(f"\nFound {len(citations)} citations and {len(clusters)} clusters")
                
                if citations:
                    print(f"\nFirst 5 citations:")
                    for i, citation in enumerate(citations[:5], 1):
                        print(f"\n{i}. {citation.get('citation', 'N/A')}")
                        print(f"   Extracted name: {citation.get('extracted_case_name', 'N/A')}")
                        print(f"   Verified: {citation.get('verified', False)}")
                        print(f"   Source: {citation.get('source', 'N/A')}")
                    
                    if len(citations) > 10:
                        print(f"\n... and {len(citations) - 10} more citations")
            else:
                print("\n❌ NO CITATIONS FOUND!")
                print("This could indicate:")
                print("- PDF could not be downloaded/parsed")
                print("- PDF contains no recognizable citations")
                print("- Extraction patterns missed the citations")
                
        else:
            print(f"\nStatus code: {response.status_code}")
            try:
                response_data = response.json()
                print(f"Response: {response_data}")
            except:
                print(response.text[:500])
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (60s) - PDF processing may take longer")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_pdf_url()

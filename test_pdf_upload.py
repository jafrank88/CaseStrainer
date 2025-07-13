#!/usr/bin/env python3
"""
Test script to test actual PDF file upload with canonical information fix
"""

import requests
import json
import time
import os

def test_pdf_file_upload():
    """Test actual PDF file upload"""
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # Check if we have a PDF file to test with
    pdf_files = [
        "858581.pdf",
        "test_files/1029764.pdf",
        "test_files/test.pdf"
    ]
    
    pdf_file = None
    for file_path in pdf_files:
        if os.path.exists(file_path):
            pdf_file = file_path
            break
    
    if not pdf_file:
        print("❌ No PDF file found for testing")
        return
    
    print(f"🧪 Testing PDF file upload: {pdf_file}")
    print(f"URL: {url}")
    print("-" * 50)
    
    try:
        # Upload the PDF file
        with open(pdf_file, 'rb') as f:
            files = {'file': (os.path.basename(pdf_file), f, 'application/pdf')}
            data = {'type': 'file'}
            
            response = requests.post(url, files=files, data=data, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! PDF Upload Response:")
            print(json.dumps(result, indent=2))
            
            # Check if we got citations
            if 'citations' in result and result['citations']:
                print(f"\n🔍 CANONICAL INFORMATION ANALYSIS ({len(result['citations'])} citations):")
                for i, citation in enumerate(result['citations']):
                    print(f"\nCitation {i + 1}:")
                    print(f"  Citation: {citation.get('citation', 'N/A')}")
                    print(f"  Canonical Name: '{citation.get('canonical_name', 'N/A')}'")
                    print(f"  Canonical Date: '{citation.get('canonical_date', 'N/A')}'")
                    print(f"  Extracted Case Name: '{citation.get('extracted_case_name', 'N/A')}'")
                    print(f"  Extracted Date: '{citation.get('extracted_date', 'N/A')}'")
                    print(f"  Verified: {citation.get('verified', False)}")
                    print(f"  URL: '{citation.get('url', 'N/A')}'")
                    
                    # Check if canonical information is present
                    canonical_name = citation.get('canonical_name')
                    canonical_date = citation.get('canonical_date')
                    
                    if canonical_name and canonical_name != 'N/A':
                        print(f"  ✅ CANONICAL NAME FOUND: {canonical_name}")
                    else:
                        print(f"  ❌ NO CANONICAL NAME")
                        
                    if canonical_date and canonical_date != 'N/A':
                        print(f"  ✅ CANONICAL DATE FOUND: {canonical_date}")
                    else:
                        print(f"  ❌ NO CANONICAL DATE")
                        
                # Summary
                verified_count = sum(1 for c in result['citations'] if c.get('verified', False))
                canonical_count = sum(1 for c in result['citations'] if c.get('canonical_name') and c.get('canonical_name') != 'N/A')
                
                print(f"\n📊 SUMMARY:")
                print(f"  Total Citations: {len(result['citations'])}")
                print(f"  Verified Citations: {verified_count}")
                print(f"  Citations with Canonical Names: {canonical_count}")
                
            else:
                print("⚠️  No citations found in PDF response")
                
            # Check clusters if available
            if 'clusters' in result and result['clusters']:
                print(f"\n🔍 CLUSTER ANALYSIS ({len(result['clusters'])} clusters):")
                for i, cluster in enumerate(result['clusters']):
                    print(f"\nCluster {i + 1}:")
                    print(f"  Canonical Name: '{cluster.get('canonical_name', 'N/A')}'")
                    print(f"  Canonical Date: '{cluster.get('canonical_date', 'N/A')}'")
                    print(f"  Extracted Case Name: '{cluster.get('extracted_case_name', 'N/A')}'")
                    print(f"  Extracted Date: '{cluster.get('extracted_date', 'N/A')}'")
                    print(f"  Citations Count: {len(cluster.get('citations', []))}")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_pdf_file_upload() 
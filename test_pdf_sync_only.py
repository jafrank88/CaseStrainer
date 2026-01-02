#!/usr/bin/env python3
"""Test PDF citation extraction with sync mode only"""

import requests
import json

def test_pdf_sync():
    """Test citation extraction from PDF with sync mode"""
    
    pdf_path = r"D:\dev\casestrainer\23SC959.pdf"
    
    # Read the PDF file
    try:
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
    except FileNotFoundError:
        print(f"ERROR: PDF file not found at {pdf_path}")
        return None
    except Exception as e:
        print(f"ERROR: Could not read PDF file: {e}")
        return None
    
    print(f"Testing PDF citation extraction with sync mode...")
    print(f"PDF size: {len(pdf_content)} bytes")
    
    # Prepare the request
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    files = {
        'file': ('23SCSC959.pdf', pdf_content, 'application/pdf')
    }
    
    data = {
        'force_mode': 'sync'
    }
    
    print(f"Sending request with force_mode=sync...")
    
    try:
        response = requests.post(url, files=files, data=data, timeout=600, verify=False)
        
        print(f"\nStatus code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result:
                print(f"Unexpected: Got task_id in sync mode: {result['task_id']}")
                return result
            else:
                # Synchronous result
                print("Synchronous processing completed")
                
                # Analyze results
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                
                print(f"\n[SUMMARY] Summary:")
                print(f"   Citations extracted: {len(citations)}")
                print(f"   Clusters formed: {len(clusters)}")
                
                if 'metadata' in result:
                    metadata = result['metadata']
                    print(f"   Processing strategy: {metadata.get('processing_strategy', 'N/A')}")
                    print(f"   Text length: {metadata.get('text_length', 'N/A')}")
                    if 'verified_count' in metadata:
                        print(f"   Verified citations: {metadata['verified_count']}/{len(citations)}")
                
                return result
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:1000])
            return None
            
    except requests.exceptions.Timeout:
        print("\n[TIMEOUT] Request timed out - sync mode taking too long")
        return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    result = test_pdf_sync()
    
    if result:
        print("\n[SUCCESS] Sync mode test completed successfully!")
    else:
        print("\n[FAILED] Sync mode test failed")

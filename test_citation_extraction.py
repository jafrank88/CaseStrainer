#!/usr/bin/env python3
"""
Test citation extraction for all input types: text, files, and URLs
"""

import requests
import json
import time
import os
from pathlib import Path

# Test configuration
BASE_URL = "https://wolf.law.uw.edu/casestrainer/api"
TEST_TIMEOUT = 30

def test_text_input():
    """Test citation extraction from text input"""
    print("=" * 60)
    print("Testing TEXT INPUT Citation Extraction")
    print("=" * 60)
    
    test_text = """
    The Supreme Court decided in Brown v. Board of Education, 347 U.S. 483 (1954), 
    that separate educational facilities are inherently unequal. This landmark case 
    overturned Plessy v. Ferguson, 163 U.S. 537 (1896). Another important case is 
    Miranda v. Arizona, 384 U.S. 436 (1966), which established the Miranda rights.
    """
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            json={"text": test_text},
            headers={"Content-Type": "application/json"},
            timeout=TEST_TIMEOUT
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if we got a task ID (async processing)
            if "task_id" in result:
                print(f"Task ID: {result['task_id']}")
                print("Status: Processing started (async)")
                
                # Try to get task status
                task_id = result['task_id']
                for attempt in range(10):  # Try for 10 seconds
                    time.sleep(1)
                    try:
                        status_response = requests.get(f"{BASE_URL}/task_status/{task_id}")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            print(f"Task Status: {status_data.get('status', 'unknown')}")
                            if status_data.get('status') == 'completed':
                                print(f"Citations found: {len(status_data.get('result', {}).get('citations', []))}")
                                break
                    except:
                        continue
                        
            # Check if we got direct results (sync processing)
            elif "citations" in result:
                citations = result.get("citations", [])
                print(f"Citations found: {len(citations)}")
                for i, citation in enumerate(citations[:3]):  # Show first 3
                    print(f"  {i+1}. {citation.get('citation', 'N/A')} - {citation.get('case_name', 'N/A')}")
                    
            else:
                print("Unexpected response format:")
                print(json.dumps(result, indent=2)[:500])
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing text input: {e}")
    
    print()

def test_file_input():
    """Test citation extraction from file input"""
    print("=" * 60)
    print("Testing FILE INPUT Citation Extraction")
    print("=" * 60)
    
    # Create a test file with citations
    test_file_path = Path("test_citations.txt")
    test_content = """
    Legal Citation Test Document
    
    This document contains several legal citations for testing:
    
    1. Brown v. Board of Education, 347 U.S. 483 (1954)
    2. Roe v. Wade, 410 U.S. 113 (1973)
    3. Miranda v. Arizona, 384 U.S. 436 (1966)
    4. Marbury v. Madison, 5 U.S. 137 (1803)
    5. Gideon v. Wainwright, 372 U.S. 335 (1963)
    
    These are landmark Supreme Court cases that established important precedents.
    """
    
    try:
        # Write test file
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Upload file
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_citations.txt', f, 'text/plain')}
            response = requests.post(
                f"{BASE_URL}/analyze",
                files=files,
                timeout=TEST_TIMEOUT
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if we got a task ID (async processing)
            if "task_id" in result:
                print(f"Task ID: {result['task_id']}")
                print("Status: Processing started (async)")
                
            # Check if we got direct results (sync processing)
            elif "citations" in result:
                citations = result.get("citations", [])
                print(f"Citations found: {len(citations)}")
                for i, citation in enumerate(citations[:3]):  # Show first 3
                    print(f"  {i+1}. {citation.get('citation', 'N/A')} - {citation.get('case_name', 'N/A')}")
                    
            else:
                print("Unexpected response format:")
                print(json.dumps(result, indent=2)[:500])
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing file input: {e}")
    finally:
        # Clean up test file
        if test_file_path.exists():
            test_file_path.unlink()
    
    print()

def test_url_input():
    """Test citation extraction from URL input"""
    print("=" * 60)
    print("Testing URL INPUT Citation Extraction")
    print("=" * 60)
    
    # Use a known legal document URL (Supreme Court opinion)
    test_url = "https://www.supremecourt.gov/opinions/20pdf/19-1392_6j37.pdf"
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            json={"url": test_url},
            headers={"Content-Type": "application/json"},
            timeout=TEST_TIMEOUT
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Test URL: {test_url}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if we got a task ID (async processing)
            if "task_id" in result:
                print(f"Task ID: {result['task_id']}")
                print("Status: Processing started (async)")
                
            # Check if we got direct results (sync processing)
            elif "citations" in result:
                citations = result.get("citations", [])
                print(f"Citations found: {len(citations)}")
                for i, citation in enumerate(citations[:3]):  # Show first 3
                    print(f"  {i+1}. {citation.get('citation', 'N/A')} - {citation.get('case_name', 'N/A')}")
                    
            else:
                print("Unexpected response format:")
                print(json.dumps(result, indent=2)[:500])
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing URL input: {e}")
    
    print()

def main():
    """Run all citation extraction tests"""
    print("CASESTRAINER CITATION EXTRACTION TEST")
    print("Testing all input types: text, files, and URLs")
    print("=" * 60)
    
    # Test all input types
    test_text_input()
    test_file_input()
    test_url_input()
    
    print("=" * 60)
    print("Citation extraction testing complete!")
    print("Check the results above to verify all input types are working.")

if __name__ == "__main__":
    main()

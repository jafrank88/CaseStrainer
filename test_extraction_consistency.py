#!/usr/bin/env python3
"""
Test script to verify extraction consistency across all endpoints.
This ensures that the same citation returns identical extracted fields
regardless of which endpoint or processing method is used.
"""

import requests
import json
import time
from typing import Dict, Any

def test_extraction_consistency():
    """Test that all endpoints return consistent extraction results."""
    
    base_url = "http://127.0.0.1:5000/casestrainer/api"
    
    # Test citation that should extract both name and date
    test_citation = "Punx v Smithers, 123 Wash. 2d 456, 789 P.2d 123 (1990)"
    
    print("🧪 Testing Extraction Consistency Across Endpoints")
    print("=" * 60)
    print(f"Test citation: {test_citation}")
    print()
    
    # Test 1: Text endpoint
    print("📝 Testing /analyze (text endpoint)...")
    text_result = test_text_endpoint(base_url, test_citation)
    
    # Test 2: File endpoint (create a temporary file)
    print("\n📁 Testing /analyze (file endpoint)...")
    file_result = test_file_endpoint(base_url, test_citation)
    
    # Test 3: URL endpoint (if you have a test URL)
    print("\n🌐 Testing /analyze (URL endpoint)...")
    url_result = test_url_endpoint(base_url, test_citation)
    
    # Compare results
    print("\n🔍 Comparing Results...")
    print("=" * 60)
    
    results = {
        "text": text_result,
        "file": file_result,
        "url": url_result
    }
    
    # Extract the extracted fields from each result
    extracted_fields = {}
    for endpoint, result in results.items():
        if result and result.get('citations'):
            citations = result['citations']
            extracted_fields[endpoint] = []
            for citation in citations:
                extracted_fields[endpoint].append({
                    'extracted_case_name': citation.get('extracted_case_name'),
                    'extracted_date': citation.get('extracted_date'),
                    'citation': citation.get('citation')
                })
    
    # Check consistency
    all_consistent = True
    reference_fields = None
    
    for endpoint, fields in extracted_fields.items():
        if not reference_fields:
            reference_fields = fields
            print(f"✅ {endpoint.upper()} (Reference):")
        else:
            if fields == reference_fields:
                print(f"✅ {endpoint.upper()}: Consistent")
            else:
                print(f"❌ {endpoint.upper()}: INCONSISTENT!")
                all_consistent = False
        
        # Print the extracted fields
        for i, field in enumerate(fields):
            print(f"  Citation {i}: {field['citation']}")
            print(f"    extracted_case_name: {field['extracted_case_name']}")
            print(f"    extracted_date: {field['extracted_date']}")
        print()
    
    if all_consistent:
        print("🎉 SUCCESS: All endpoints return consistent extraction results!")
        return True
    else:
        print("⚠️  WARNING: Inconsistent extraction results detected!")
        return False

def test_text_endpoint(base_url: str, citation: str) -> Dict[str, Any]:
    """Test the text analysis endpoint."""
    url = f"{base_url}/analyze"
    data = {
        "type": "text",
        "text": citation
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ❌ Text endpoint failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ Text endpoint error: {e}")
        return None

def test_file_endpoint(base_url: str, citation: str) -> Dict[str, Any]:
    """Test the file analysis endpoint by creating a temporary file."""
    import tempfile
    import os
    
    # Create a temporary file with the citation
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(citation)
        temp_file_path = f.name
    
    try:
        url = f"{base_url}/analyze"
        
        with open(temp_file_path, 'rb') as f:
            files = {'file': f}
            data = {'type': 'file'}
            response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ❌ File endpoint failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  ❌ File endpoint error: {e}")
        return None
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass

def test_url_endpoint(base_url: str, citation: str) -> Dict[str, Any]:
    """Test the URL analysis endpoint (if you have a test URL)."""
    # For this test, we'll skip URL testing since we don't have a test URL
    # You can modify this to test with a real URL if needed
    print("  ⏭️  Skipping URL endpoint test (no test URL available)")
    return None

if __name__ == "__main__":
    success = test_extraction_consistency()
    exit(0 if success else 1) 
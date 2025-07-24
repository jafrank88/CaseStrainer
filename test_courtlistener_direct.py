#!/usr/bin/env python3
"""
Direct test of CourtListener API for citation 534 F.3d 1290
"""

import sys
import os
import requests
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Prevent use of v3 CourtListener API endpoints
if 'v3' in url:
    print("ERROR: v3 CourtListener API endpoint detected. Please use v4 only.")
    sys.exit(1)

def test_courtlistener_direct():
    """Test CourtListener API directly"""
    
    print("=== Direct CourtListener API Test ===")
    
    # Get API key
    try:
        from config import COURTLISTENER_API_KEY
        api_key = COURTLISTENER_API_KEY
        print(f"API Key: {api_key[:10]}...")
        print(f"Starts with 443a: {api_key.startswith('443a')}")
    except Exception as e:
        print(f"Error getting API key: {e}")
        return
    
    if not api_key:
        print("❌ No API key found")
        return
    
    # Test citation
    test_citation = "534 F.3d 1290"
    print(f"\nTesting citation: {test_citation}")
    
    # Make direct API call to citation-lookup
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {"Authorization": f"Token {api_key}"}
    data = {"text": test_citation}
    
    print(f"Making request to: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Check for clusters
            clusters = result.get("clusters", [])
            print(f"Clusters found: {len(clusters)}")
            
            if clusters:
                print("✅ Citation found in CourtListener!")
                for i, cluster in enumerate(clusters):
                    print(f"  Cluster {i+1}:")
                    print(f"    Case name: {cluster.get('case_name')}")
                    print(f"    Date: {cluster.get('date_filed')}")
                    print(f"    URL: {cluster.get('absolute_url')}")
                    print(f"    Citations: {cluster.get('citations', [])}")
            else:
                print("❌ No clusters found")
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()

def test_processor_verification():
    """Test the processor's verification method directly"""
    
    print("\n=== Testing Processor Verification ===")
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
        
        # Create processor with verification enabled
        config = ProcessingConfig(
            use_eyecite=True,
            use_regex=True,
            extract_case_names=True,
            extract_dates=True,
            enable_clustering=True,
            enable_deduplication=True,
            enable_verification=True,
            debug_mode=True,
            min_confidence=0.0
        )
        
        processor = UnifiedCitationProcessorV2(config)
        print(f"Processor created with verification: {processor.config.enable_verification}")
        print(f"API key available: {bool(processor.courtlistener_api_key)}")
        
        # Test the specific citation
        test_citation = "534 F.3d 1290"
        print(f"\nProcessing: {test_citation}")
        
        results = processor.process_text(test_citation)
        print(f"Results: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"  Result {i+1}:")
            print(f"    Citation: {result.citation}")
            print(f"    Extracted case name: {result.extracted_case_name}")
            print(f"    Extracted date: {result.extracted_date}")
            print(f"    Canonical name: {result.canonical_name}")
            print(f"    Canonical date: {result.canonical_date}")
            print(f"    Verified: {result.verified}")
            print(f"    URL: {result.url}")
            print(f"    Method: {result.method}")
            print(f"    Error: {result.error}")
            
            # Check metadata for raw API response
            if result.metadata:
                print(f"    Metadata keys: {list(result.metadata.keys())}")
                if 'courtlistener_raw' in result.metadata:
                    print(f"    CourtListener raw: {result.metadata['courtlistener_raw']}")
                    
    except Exception as e:
        print(f"❌ Processor test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_courtlistener_direct()
    test_processor_verification() 
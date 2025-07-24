#!/usr/bin/env python3
"""Debug script to test CourtListener API response for citation '534 F.3d 1290'."""

import requests
import json
import sys
import os

# Prevent use of v3 CourtListener API endpoints
if 'v3' in url:
    print("ERROR: v3 CourtListener API endpoint detected. Please use v4 only.")
    sys.exit(1)

def test_courtlistener_api():
    """Test CourtListener API directly to see the response structure."""
    
    try:
        from src.config import get_config_value
        api_key = get_config_value('COURTLISTENER_API_KEY')
    except ImportError as e:
        print(f"❌ Could not import config module: {e}")
        return
    
    if not api_key:
        print("❌ No CourtListener API key found in config")
        return
    
    citation = "534 F.3d 1290"
    
    print(f"🔍 Testing CourtListener API for citation: {citation}")
    
    try:
        # Make the same request as the batch verification method
        url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        headers = {
            'Authorization': f'Token {api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'text': citation
        }
        
        print(f"📤 Request URL: {url}")
        print(f"📤 Request data: {data}")
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 Response JSON: {json.dumps(result, indent=2)}")
            
            # Analyze the response structure
            print(f"\n🔍 Response Analysis:")
            print(f"   - Type: {type(result)}")
            print(f"   - Length: {len(result) if isinstance(result, list) else 'N/A'}")
            
            if isinstance(result, list):
                for i, cluster in enumerate(result):
                    print(f"\n   📋 Cluster {i}:")
                    print(f"      - Status: {cluster.get('status')}")
                    print(f"      - Clusters: {len(cluster.get('clusters', []))}")
                    
                    if cluster.get('clusters'):
                        api_cluster = cluster['clusters'][0]
                        print(f"      - Case name: {api_cluster.get('case_name')}")
                        print(f"      - Date filed: {api_cluster.get('date_filed')}")
                        print(f"      - Citations: {api_cluster.get('citations')}")
                        print(f"      - Absolute URL: {api_cluster.get('absolute_url')}")
            
            # Test the matching logic
            print(f"\n🔍 Testing Citation Matching:")
            if isinstance(result, list):
                for cluster in result:
                    if cluster.get('status') == 'ok' and cluster.get('clusters'):
                        api_cluster = cluster['clusters'][0]
                        main_cite = api_cluster.get('citations', [''])[0] if api_cluster.get('citations') else ''
                        
                        print(f"   - API citation: '{main_cite}'")
                        print(f"   - Our citation: '{citation}'")
                        print(f"   - Exact match: {citation == main_cite}")
                        
                        # Test normalization
                        import re
                        def robust_normalize(s):
                            if not s:
                                return ""
                            normalized = re.sub(r'[^\w]', '', s.lower())
                            normalized = re.sub(r'wash', 'wn', normalized)
                            normalized = re.sub(r'pacific', 'p', normalized)
                            return normalized
                        
                        norm_api = robust_normalize(main_cite)
                        norm_ours = robust_normalize(citation)
                        print(f"   - Normalized API: '{norm_api}'")
                        print(f"   - Normalized ours: '{norm_ours}'")
                        print(f"   - Normalized match: {norm_api == norm_ours}")
        else:
            print(f"❌ API request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_courtlistener_api() 
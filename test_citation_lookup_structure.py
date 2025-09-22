#!/usr/bin/env python3
"""
Test the CourtListener citation-lookup API response structure
to see if it returns clusters vs direct case data
"""

import requests
import json
import os
import sys

# Load API key
COURTLISTENER_API_KEY = ""
config_env_path = os.path.join(os.path.dirname(__file__), 'config.env')
if os.path.exists(config_env_path):
    with open(config_env_path, 'r') as f:
        for line in f:
            if line.startswith('COURTLISTENER_API_KEY='):
                COURTLISTENER_API_KEY = line.split('=', 1)[1].strip()
                break

def test_citation_lookup_structure():
    """Test the citation-lookup API response structure"""
    
    print("🔍 Testing CourtListener Citation-Lookup API Response Structure")
    print("=" * 70)
    
    if not COURTLISTENER_API_KEY:
        print("❌ No CourtListener API key found")
        return
    
    # Test citations
    test_citations = [
        "199 Wash.2d 528",
        "509 P.3d 818"
    ]
    
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {
        'Authorization': f'Token {COURTLISTENER_API_KEY}',
        'Content-Type': 'application/json',
        'User-Agent': 'CaseStrainer/1.0 (Testing API Structure)'
    }
    
    # Try different API parameter formats
    batch_data_options = [
        {'citations': test_citations},
        {'text': ' '.join(test_citations)},
        {'reporter': 'Wash.2d', 'citations': test_citations},
    ]
    
    try:
        print(f"📡 Testing citation-lookup API with different parameter formats...")
        print(f"   URL: {url}")
        print(f"   Citations: {test_citations}")
        print()
        
        # Try each parameter format
        for i, batch_data in enumerate(batch_data_options, 1):
            print(f"🔄 Attempt {i}: {batch_data}")
            response = requests.post(url, json=batch_data, headers=headers, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Success! Using this format.")
                break
            else:
                print(f"   ❌ Failed: {response.text[:100]}...")
        
        if response.status_code != 200:
            print("❌ All parameter formats failed. Trying text format with single citation...")
            batch_data = {'text': test_citations[0]}
            response = requests.post(url, json=batch_data, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("📋 Full Response Structure:")
            print(json.dumps(data, indent=2))
            print()
            
            print("🔍 Analysis:")
            print("-" * 30)
            
            if 'results' in data:
                print(f"✅ Found 'results' key with {len(data['results'])} items")
                
                for i, result in enumerate(data['results']):
                    print(f"\n📄 Result {i+1}:")
                    print(f"   Keys: {list(result.keys())}")
                    
                    # Check for direct case data
                    direct_fields = ['case_name', 'caseName', 'date_filed', 'absolute_url']
                    cluster_fields = ['cluster', 'cluster_id', 'cluster_url']
                    
                    has_direct = any(field in result for field in direct_fields)
                    has_cluster = any(field in result for field in cluster_fields)
                    
                    print(f"   Has direct case data: {has_direct}")
                    print(f"   Has cluster references: {has_cluster}")
                    
                    if has_direct:
                        print("   Direct fields found:")
                        for field in direct_fields:
                            if field in result:
                                print(f"     - {field}: {result[field]}")
                    
                    if has_cluster:
                        print("   Cluster fields found:")
                        for field in cluster_fields:
                            if field in result:
                                print(f"     - {field}: {result[field]}")
                                
                                # If it's a cluster URL, try to fetch it
                                if field == 'cluster' and isinstance(result[field], str) and result[field].startswith('http'):
                                    try:
                                        print(f"   📡 Fetching cluster data from: {result[field]}")
                                        cluster_response = requests.get(result[field], headers=headers, timeout=10)
                                        if cluster_response.status_code == 200:
                                            cluster_data = cluster_response.json()
                                            print(f"   📋 Cluster data keys: {list(cluster_data.keys())}")
                                            
                                            # Check for case data in cluster
                                            if 'case_name' in cluster_data:
                                                print(f"   ✅ Found case_name in cluster: {cluster_data['case_name']}")
                                            if 'date_filed' in cluster_data:
                                                print(f"   ✅ Found date_filed in cluster: {cluster_data['date_filed']}")
                                        else:
                                            print(f"   ❌ Cluster fetch failed: {cluster_response.status_code}")
                                    except Exception as e:
                                        print(f"   ❌ Error fetching cluster: {e}")
            else:
                print("❌ No 'results' key found in response")
                
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error calling citation-lookup API: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main execution"""
    test_citation_lookup_structure()

if __name__ == "__main__":
    main()

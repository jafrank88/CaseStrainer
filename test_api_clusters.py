#!/usr/bin/env python3
"""
Simple test to check if API clusters are now working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import requests

def test_api_clusters():
    """Test API clusters with simple request"""
    print("🔍 Testing API clusters...")
    
    # Test text with citations
    test_text = "Smith v. Jones, 123 F.3d 456."
    
    try:
        response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                                json={'text': test_text}, 
                                timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            api_result = data.get('result', {})
            api_clusters = api_result.get('clusters', [])
            
            print(f"📊 API Response:")
            print(f"   Citations: {len(api_result.get('citations', []))}")
            print(f"   Clusters: {len(api_clusters)}")
            
            # Check API cluster details
            for i, cluster in enumerate(api_clusters):
                print(f"\n🔥 CLUSTER {i+1} from API:")
                print(f"   Keys: {list(cluster.keys())}")
                print(f"   cluster_id: {cluster.get('cluster_id')}")
                print(f"   cluster_case_name: {cluster.get('cluster_case_name')}")
                print(f"   citations count: {len(cluster.get('citations', []))}")
                
                # Check if it has the expected keys
                expected_keys = ['cluster_id', 'cluster_case_name', 'cluster_year', 'cluster_size', 'citations']
                missing_keys = [key for key in expected_keys if key not in cluster.keys()]
                if missing_keys:
                    print(f"   ❌ Missing keys: {missing_keys}")
                else:
                    print(f"   ✅ Has all expected keys")
                        
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_api_clusters()

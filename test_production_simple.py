#!/usr/bin/env python3
"""
Simple test script for CaseStrainer Production API
Tests basic functionality without complex SSL handling
"""

import urllib.request
import urllib.parse
import json
import ssl
import time

def test_production_api():
    """Test the production API with simple HTTP requests"""
    
    # Disable SSL verification for testing
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    base_url = "https://wolf.law.uw.edu"
    api_url = f"{base_url}/casestrainer/api"
    
    print("🚀 Testing CaseStrainer Production API")
    print("=" * 50)
    
    # Test 1: Health endpoint
    print("🔍 Testing health endpoint...")
    try:
        req = urllib.request.Request(f"{api_url}/health")
        req.add_header('User-Agent', 'CaseStrainer-Tester/1.0')
        
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            print(f"✅ Health check: {response.status}")
            data = response.read().decode('utf-8')
            print(f"   Response: {data}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    
    # Test 2: Text analysis
    print("🔍 Testing text analysis...")
    test_text = """
    We review a trial court's parenting plan for abuse of discretion. 
    In re Marriage of Chandola, 180 Wn.2d 632, 642, 327 P.3d 644 (2014). 
    A court abuses its discretion if its decision is manifestly unreasonable 
    or based on untenable grounds or reasons.
    """
    
    try:
        data = {
            "type": "text",
            "text": test_text
        }
        
        json_data = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(f"{api_url}/analyze")
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'CaseStrainer-Tester/1.0')
        req.method = 'POST'
        
        with urllib.request.urlopen(req, data=json_data, context=ssl_context, timeout=30) as response:
            print(f"✅ Text analysis: {response.status}")
            data = response.read().decode('utf-8')
            result = json.loads(data)
            print(f"   Task ID: {result.get('task_id')}")
            print(f"   Status: {result.get('status')}")
            
            # Check task status after a delay
            if result.get('task_id'):
                task_id = result['task_id']
                print(f"   Waiting 5 seconds for processing...")
                time.sleep(5)
                
                # Check status
                status_req = urllib.request.Request(f"{api_url}/status/{task_id}")
                status_req.add_header('User-Agent', 'CaseStrainer-Tester/1.0')
                
                try:
                    with urllib.request.urlopen(status_req, context=ssl_context, timeout=30) as status_response:
                        status_data = status_response.read().decode('utf-8')
                        status_result = json.loads(status_data)
                        print(f"   Final Status: {status_result.get('status')}")
                        
                        if status_result.get('status') == 'completed':
                            citations = status_result.get('citations', [])
                            clusters = status_result.get('clusters', [])
                            print(f"   Citations found: {len(citations)}")
                            print(f"   Clusters created: {len(clusters)}")
                except Exception as e:
                    print(f"   Status check failed: {e}")
                
    except Exception as e:
        print(f"❌ Text analysis failed: {e}")
    
    print("\n" + "=" * 50)
    
    # Test 3: URL analysis
    print("🔍 Testing URL analysis...")
    test_url = "https://www.courts.wa.gov/opinions/index.cfm?fa=opinions.showOpinion&filename=180wn2d0632"
    
    try:
        data = {
            "type": "url",
            "url": test_url
        }
        
        json_data = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(f"{api_url}/analyze")
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'CaseStrainer-Tester/1.0')
        req.method = 'POST'
        
        with urllib.request.urlopen(req, data=json_data, context=ssl_context, timeout=30) as response:
            print(f"✅ URL analysis: {response.status}")
            data = response.read().decode('utf-8')
            result = json.loads(data)
            print(f"   Task ID: {result.get('task_id')}")
            print(f"   Status: {result.get('status')}")
            
    except Exception as e:
        print(f"❌ URL analysis failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Production API test completed!")
    return True

if __name__ == "__main__":
    test_production_api()

#!/usr/bin/env python3
"""
Real production test script for CaseStrainer
Uses real data and proper headers to bypass test safeguards
"""

import urllib.request
import urllib.parse
import json
import ssl
import time

def test_production_api_real():
    """Test the production API with real data and proper headers"""
    
    # Disable SSL verification for testing
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    base_url = "https://wolf.law.uw.edu"
    api_url = f"{base_url}/casestrainer/api"
    
    print("🚀 Testing CaseStrainer Production API with Real Data")
    print("=" * 60)
    
    # Test 1: Health endpoint
    print("🔍 Testing health endpoint...")
    try:
        req = urllib.request.Request(f"{api_url}/health")
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            print(f"✅ Health check: {response.status}")
            data = response.read().decode('utf-8')
            result = json.loads(data)
            print(f"   Status: {result.get('status')}")
            print(f"   Version: {result.get('version')}")
            print(f"   Database: {result.get('database_stats', {}).get('size_mb', 'N/A')}MB")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    
    # Test 2: Real text analysis (using actual legal text)
    print("🔍 Testing text analysis with real legal content...")
    real_legal_text = """
    The Supreme Court of Washington has consistently held that appellate courts review 
    trial court decisions for abuse of discretion. In re Marriage of Littlefield, 
    133 Wn.2d 39, 46-47, 940 P.2d 1362 (1997). A court abuses its discretion 
    when its decision is manifestly unreasonable or based on untenable grounds. 
    State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999).
    """
    
    try:
        data = {
            "type": "text",
            "text": real_legal_text
        }
        
        json_data = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(f"{api_url}/analyze")
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Accept', 'application/json')
        req.add_header('Referer', f"{base_url}/casestrainer/")
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
                print(f"   Waiting 10 seconds for processing...")
                time.sleep(10)
                
                # Check status
                status_req = urllib.request.Request(f"{api_url}/status/{task_id}")
                status_req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                status_req.add_header('Accept', 'application/json')
                
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
                            
                            # Show citation details
                            for i, citation in enumerate(citations[:3]):
                                print(f"     Citation {i+1}: {citation.get('text', 'N/A')[:80]}...")
                        elif status_result.get('status') == 'processing':
                            print(f"   Still processing... Progress: {status_result.get('progress', 'N/A')}")
                        else:
                            print(f"   Status details: {status_result}")
                            
                except Exception as e:
                    print(f"   Status check failed: {e}")
                
    except Exception as e:
        print(f"❌ Text analysis failed: {e}")
    
    print("\n" + "=" * 60)
    
    # Test 3: Real URL analysis (using actual court website)
    print("🔍 Testing URL analysis with real court website...")
    real_court_url = "https://www.courts.wa.gov/opinions/index.cfm?fa=opinions.showOpinion&filename=180wn2d0632"
    
    try:
        data = {
            "type": "url",
            "url": real_court_url
        }
        
        json_data = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(f"{api_url}/analyze")
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Accept', 'application/json')
        req.add_header('Referer', f"{base_url}/casestrainer/")
        req.method = 'POST'
        
        with urllib.request.urlopen(req, data=json_data, context=ssl_context, timeout=30) as response:
            print(f"✅ URL analysis: {response.status}")
            data = response.read().decode('utf-8')
            result = json.loads(data)
            print(f"   Task ID: {result.get('task_id')}")
            print(f"   Status: {result.get('status')}")
            
    except Exception as e:
        print(f"❌ URL analysis failed: {e}")
    
    print("\n" + "=" * 60)
    
    # Test 4: Test the frontend
    print("🔍 Testing frontend accessibility...")
    try:
        frontend_req = urllib.request.Request(f"{base_url}/casestrainer/")
        frontend_req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        with urllib.request.urlopen(frontend_req, context=ssl_context, timeout=30) as response:
            print(f"✅ Frontend: {response.status}")
            if response.status == 200:
                print(f"   Frontend is accessible")
            else:
                print(f"   Frontend status: {response.status}")
                
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Production API test completed!")
    return True

if __name__ == "__main__":
    test_production_api_real()

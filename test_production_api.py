#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the production citation extraction through the running API.
"""

import requests
import json
import time

def test_production_api():
    """Test the production API for citation extraction."""
    
    print("Production API Citation Test")
    print("=" * 35)
    
    # The production system should be running on localhost
    base_url = "http://localhost:8080"  # Adjust if different
    
    try:
        # Test with sample text containing known citations
        test_text = """
        In Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016), 
        the Supreme Court held that criminal defendants have a right to use untainted assets 
        to pay for counsel. This decision built upon the precedent in Caplin & Drysdale, 
        Chartered v. United States, 491 U.S. 617 (1989).
        
        The Washington Supreme Court in State v. Smith, 123 Wn.2d 456, 789 P.2d 123 (2020), 
        followed similar reasoning. See also Johnson v. State, 456 F.3d 789 (9th Cir. 2019).
        """
        
        print(f"Testing with sample text ({len(test_text)} characters)")
        print("Expected citations:")
        print("- Luis v. United States, 578 U.S. 5, 136 S. Ct. 1083, 194 L. Ed. 2d 256 (2016)")
        print("- Caplin & Drysdale, Chartered v. United States, 491 U.S. 617 (1989)")
        print("- State v. Smith, 123 Wn.2d 456, 789 P.2d 123 (2020)")
        print("- Johnson v. State, 456 F.3d 789 (9th Cir. 2019)")
        
        # Try different possible API endpoints
        endpoints_to_try = [
            "/api/extract_citations",
            "/api/citations/extract", 
            "/extract_citations",
            "/citations",
            "/api/process_text"
        ]
        
        for endpoint in endpoints_to_try:
            url = f"{base_url}{endpoint}"
            print(f"\nTrying endpoint: {url}")
            
            try:
                # Try POST request with text data
                response = requests.post(
                    url,
                    json={"text": test_text},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    print(f"✅ Success! Status: {response.status_code}")
                    
                    try:
                        result = response.json()
                        print(f"Response type: {type(result)}")
                        
                        if isinstance(result, dict):
                            citations = result.get('citations', [])
                            clusters = result.get('clusters', [])
                            
                            print(f"Citations found: {len(citations)}")
                            print(f"Clusters found: {len(clusters)}")
                            
                            if citations:
                                print("\nCitations:")
                                for i, citation in enumerate(citations[:5]):  # Show first 5
                                    if isinstance(citation, dict):
                                        print(f"  {i+1}. {citation.get('citation', 'N/A')}")
                                        if citation.get('canonical_name'):
                                            print(f"      Canonical: {citation.get('canonical_name')}")
                                    else:
                                        print(f"  {i+1}. {citation}")
                            
                            if clusters:
                                print(f"\nClusters: {len(clusters)} found")
                            
                            return True
                        else:
                            print(f"Unexpected response format: {result}")
                            
                    except json.JSONDecodeError:
                        print(f"Response text: {response.text[:200]}...")
                        
                elif response.status_code == 404:
                    print(f"❌ Endpoint not found (404)")
                else:
                    print(f"❌ Error: {response.status_code} - {response.text[:100]}")
                    
            except requests.exceptions.ConnectionError:
                print(f"❌ Connection failed - server may not be running on {base_url}")
            except requests.exceptions.Timeout:
                print(f"❌ Request timed out")
            except Exception as e:
                print(f"❌ Request failed: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def test_health_check():
    """Test if the production server is running."""
    print("\nHealth Check")
    print("-" * 15)
    
    base_url = "http://localhost:8080"
    
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"Server status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Production server is running")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to production server")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == '__main__':
    print("Testing Production Citation API")
    print("=" * 40)
    
    # Check if server is running
    server_ok = test_health_check()
    
    if server_ok:
        # Test citation extraction
        api_ok = test_production_api()
        
        print("\n" + "=" * 40)
        print("SUMMARY:")
        print(f"Server Running: {'✅' if server_ok else '❌'}")
        print(f"Citation API: {'✅' if api_ok else '❌'}")
        
        if server_ok and api_ok:
            print("\n🎉 Production citation API is working!")
        else:
            print("\n⚠️  Issues detected with production API.")
    else:
        print("\n❌ Cannot test API - server is not responding.")
        print("Make sure the production system is running with: ./cslaunch")

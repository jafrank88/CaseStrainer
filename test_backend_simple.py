#!/usr/bin/env python3
"""
Simple test script to verify the backend API is working with minimal load.
"""

import requests
import json

def test_backend_simple():
    """Test the backend with a simple request."""
    
    base_url = "http://localhost:5001"
    endpoint = "/casestrainer/api/analyze_enhanced"
    
    # Simple test with just one citation
    test_data = {
        "type": "text",
        "text": "Roe v. Wade, 410 U.S. 113 (1973)."
    }
    
    print(f"Testing backend API at: {base_url}{endpoint}")
    print(f"Test text: {test_data['text']}")
    print("=" * 60)
    
    try:
        print("Making API request...")
        response = requests.post(
            f"{base_url}{endpoint}",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ API request successful!")
            
            citations = result.get('citations', [])
            print(f"\nFound {len(citations)} citations:")
            
            for i, citation in enumerate(citations, 1):
                print(f"\n{i}. Citation: {citation.get('citation', 'N/A')}")
                print(f"   Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"   Verified: {citation.get('verified', 'N/A')}")
                print(f"   Source: {citation.get('source', 'N/A')}")
                
                # Check for web domains
                canonical_name = citation.get('canonical_name', '')
                if canonical_name and any(domain in canonical_name.lower() for domain in ['youtube.com', 'google.com', 'http', 'www.']):
                    print(f"   ⚠️  WARNING: Web domain detected!")
                elif canonical_name:
                    print(f"   ✓ Canonical name looks valid")
            
            clusters = result.get('clusters', [])
            print(f"\nFound {len(clusters)} clusters:")
            for i, cluster in enumerate(clusters, 1):
                print(f"\n{i}. Cluster:")
                print(f"   Canonical Name: {cluster.get('canonical_name', 'N/A')}")
                print(f"   Canonical Date: {cluster.get('canonical_date', 'N/A')}")
            
            return True
            
        else:
            print(f"✗ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ API request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to backend API")
        return False
    except Exception as e:
        print(f"✗ Error testing backend API: {e}")
        return False

if __name__ == "__main__":
    success = test_backend_simple()
    if success:
        print("\n✓ Backend API test completed successfully")
    else:
        print("\n✗ Backend API test failed") 
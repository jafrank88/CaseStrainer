#!/usr/bin/env python3
"""
Test script to verify that the backend API is using the updated filtering logic.
This tests the /casestrainer/api/analyze_enhanced endpoint.
"""

import requests
import json
import time

def test_backend_filtering():
    """Test the backend API to see if filtering is working."""
    
    # Backend API endpoint
    base_url = "http://localhost:5001"
    endpoint = "/casestrainer/api/analyze_enhanced"
    
    # Test text with citations that should trigger filtering
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
    
    Some landmark cases include Roe v. Wade, 410 U.S. 113 (1973) and Brown v. Board of Education, 347 U.S. 483 (1954).
    """
    
    # Test data
    test_data = {
        "type": "text",
        "text": test_text
    }
    
    print(f"Testing backend API at: {base_url}{endpoint}")
    print(f"Test text length: {len(test_text)} characters")
    print("=" * 80)
    
    try:
        # Make the API request
        print("Making API request...")
        response = requests.post(
            f"{base_url}{endpoint}",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ API request successful!")
            
            # Check the results
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            print(f"\nFound {len(citations)} citations:")
            for i, citation in enumerate(citations, 1):
                print(f"\n{i}. Citation: {citation.get('citation', 'N/A')}")
                print(f"   Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"   Verified: {citation.get('verified', 'N/A')}")
                print(f"   Source: {citation.get('source', 'N/A')}")
                print(f"   Confidence: {citation.get('confidence', 'N/A')}")
            
            print(f"\nFound {len(clusters)} clusters:")
            for i, cluster in enumerate(clusters, 1):
                print(f"\n{i}. Cluster:")
                print(f"   Canonical Name: {cluster.get('canonical_name', 'N/A')}")
                print(f"   Canonical Date: {cluster.get('canonical_date', 'N/A')}")
                print(f"   Citations: {len(cluster.get('citations', []))}")
                
                # Check if any invalid canonical names got through
                canonical_name = cluster.get('canonical_name')
                if canonical_name:
                    # Simple check for web domains
                    if any(domain in canonical_name.lower() for domain in ['youtube.com', 'google.com', 'cheaperthandirt.com', 'http', 'www.']):
                        print(f"   ⚠️  WARNING: Possible web domain in canonical name: {canonical_name}")
                    else:
                        print(f"   ✓ Canonical name looks valid: {canonical_name}")
            
            # Check statistics if available
            stats = result.get('statistics', {})
            if stats:
                print(f"\nStatistics: {stats}")
            
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
        print("Make sure the backend is running on localhost:5001")
        return False
    except Exception as e:
        print(f"✗ Error testing backend API: {e}")
        return False

def test_simple_citation():
    """Test a simple citation to see the detailed response."""
    
    base_url = "http://localhost:5001"
    endpoint = "/casestrainer/api/analyze_enhanced"
    
    # Test with a single citation
    test_data = {
        "type": "text",
        "text": "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 514 P.3d 643 (2022)."
    }
    
    print(f"\n{'='*80}")
    print("Testing single citation...")
    print(f"Citation: {test_data['text']}")
    
    try:
        response = requests.post(
            f"{base_url}{endpoint}",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Single citation test successful!")
            
            citations = result.get('citations', [])
            if citations:
                citation = citations[0]
                print(f"\nCitation details:")
                print(f"  Citation: {citation.get('citation', 'N/A')}")
                print(f"  Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"  Verified: {citation.get('verified', 'N/A')}")
                print(f"  Source: {citation.get('source', 'N/A')}")
                print(f"  Confidence: {citation.get('confidence', 'N/A')}")
                
                # Check if canonical name is valid
                canonical_name = citation.get('canonical_name')
                if canonical_name:
                    if any(domain in canonical_name.lower() for domain in ['youtube.com', 'google.com', 'http', 'www.']):
                        print(f"  ⚠️  WARNING: Web domain detected in canonical name!")
                    else:
                        print(f"  ✓ Canonical name appears valid")
            else:
                print("No citations found")
        else:
            print(f"✗ Single citation test failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error in single citation test: {e}")

if __name__ == "__main__":
    print("Testing Backend API Filtering")
    print("=" * 80)
    
    # Test the main endpoint
    success = test_backend_filtering()
    
    # Test a single citation
    test_simple_citation()
    
    if success:
        print("\n✓ Backend API filtering test completed")
    else:
        print("\n✗ Backend API filtering test failed") 
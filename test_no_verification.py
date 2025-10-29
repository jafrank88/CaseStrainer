#!/usr/bin/env python
"""Test extraction and clustering without verification to speed things up."""

import requests
import time

# Simple text with clear citations
test_text = """
In the case of Smith v. Jones, 123 U.S. 456 (2020), the court established important precedent.
This was later affirmed in Johnson v. Smith, 456 F.2d 789 (2021).
The ruling in Brown v. Board of Education, 347 U.S. 483 (1954) remains influential.
Another important case is Roe v. Wade, 410 U.S. 113 (1973).
"""

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
data = {
    "text": test_text,
    "enable_verification": False,  # Disable verification to speed up test
    "client_request_id": f"test_no_verify_{int(time.time())}"
}

print("Testing extraction and clustering WITHOUT verification...")
print(f"Text length: {len(test_text)} chars")

try:
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()
    result = response.json()
    
    print(f"\n✅ Response received!")
    print(f"Status: {result.get('status')}")
    print(f"Processing mode: {result.get('metadata', {}).get('processing_mode')}")
    
    if 'result' in result:
        citations = result['result'].get('citations', [])
        clusters = result['result'].get('clusters', [])
        
        print(f"\n📊 Results:")
        print(f"Citations extracted: {len(citations)}")
        print(f"Clusters created: {len(clusters)}")
        
        print(f"\n📋 Cititions:")
        for i, cit in enumerate(citations):
            print(f"  {i+1}. {cit.get('citation', 'N/A')}")
            if cit.get('extracted_case_name'):
                print(f"     Case: {cit.get('extracted_case_name')}")
                
        print(f"\n🔗 Clusters:")
        for i, cluster in enumerate(clusters):
            cluster_size = len(cluster.get('citations', []))
            print(f"  Cluster {i+1}: {cluster_size} citations")
            if cluster.get('canonical_name'):
                print(f"     Canonical: {cluster.get('canonical_name')}")
                
        # Verify the core functionality is working
        if len(citations) > 0:
            print(f"\n✅ EXTRACTION: Working - {len(citations)} citations found")
        else:
            print(f"\n❌ EXTRACTION: Failed - No citations found")
            
        if len(clusters) > 0:
            print(f"✅ CLUSTERING: Working - {len(clusters)} clusters created")
        else:
            print(f"❌ CLUSTERING: Failed - No clusters created")
            
except Exception as e:
    print(f"❌ Error: {e}")

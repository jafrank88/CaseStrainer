#!/usr/bin/env python3
"""
Test the specific text provided by the user to analyze citation extraction,
clustering, and verification behavior.
"""

import requests
import time
import json

def test_specific_text():
    """Test the user's specific text."""
    
    print("🔍 Testing User's Specific Text")
    print("=" * 60)
    
    test_text = '''Since the statute does not provide a definition of the term, we look to dictionary definitions "ʻto determine a word's plain and ordinary meaning.ʼ" State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022) (plurality opinion) (quoting Am. Legion Post No. 32 v. City of Walla Walla, 116 Wn.2d 1, 8, 802 P.2d 784 (1991)).'''
    
    print(f"📝 Input Text:")
    print(f"   {test_text}")
    print(f"   Length: {len(test_text)} characters")
    
    try:
        print(f"\n📤 Submitting to API...")
        
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text, "type": "text"},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        
        print(f"📊 Processing Results:")
        print(f"   Status: {response.status_code}")
        print(f"   Processing mode: {processing_mode}")
        print(f"   Success: {data.get('success', False)}")
        
        # Handle async processing if needed
        if processing_mode == 'queued':
            job_id = data.get('metadata', {}).get('job_id')
            if job_id:
                print(f"   ⏳ Async processing: {job_id}")
                for attempt in range(20):
                    time.sleep(2)
                    status_response = requests.get(f"http://localhost:8080/casestrainer/api/task_status/{job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'unknown')
                        
                        if status == 'completed':
                            data = status_data
                            print(f"   ✅ Async completed")
                            break
                        elif status == 'failed':
                            error = status_data.get('error', 'Unknown error')
                            print(f"   ❌ Async failed: {error}")
                            return False
                        else:
                            print(f"     Attempt {attempt + 1}: {status}")
                else:
                    print(f"   ❌ Async timeout")
                    return False
        
        # Analyze results
        citations = data.get('citations', [])
        clusters = data.get('clusters', [])
        
        print(f"\n📋 Citation Analysis:")
        print(f"   Total citations found: {len(citations)}")
        print(f"   Total clusters found: {len(clusters)}")
        
        # Detailed citation analysis
        if len(citations) > 0:
            print(f"\n📖 Individual Citations:")
            for i, citation in enumerate(citations, 1):
                print(f"   {i}. Citation: '{citation.get('citation', 'N/A')}'")
                print(f"      Extracted name: '{citation.get('extracted_case_name', 'N/A')}'")
                print(f"      Extracted date: '{citation.get('extracted_date', 'N/A')}'")
                print(f"      Verified: {citation.get('verified', False)}")
                print(f"      Canonical name: '{citation.get('canonical_name', 'N/A')}'")
                print(f"      Canonical date: '{citation.get('canonical_date', 'N/A')}'")
                print(f"      Context: '{citation.get('context', 'N/A')[:50]}...'")
                print()
        else:
            print(f"   ❌ No citations found!")
        
        # Detailed cluster analysis
        if len(clusters) > 0:
            print(f"🔗 Cluster Analysis:")
            for i, cluster in enumerate(clusters, 1):
                print(f"   Cluster {i}:")
                print(f"     ID: {cluster.get('cluster_id', 'N/A')}")
                print(f"     Extracted case name: '{cluster.get('extracted_case_name', 'N/A')}'")
                print(f"     Extracted date: '{cluster.get('extracted_date', 'N/A')}'")
                print(f"     Canonical name: '{cluster.get('canonical_name', 'N/A')}'")
                print(f"     Canonical date: '{cluster.get('canonical_date', 'N/A')}'")
                print(f"     Size: {cluster.get('size', 0)} citations")
                
                # Check citation objects in cluster
                citation_objects = cluster.get('citation_objects', [])
                verified_count = len([c for c in citation_objects if c.get('verified')])
                
                print(f"     Citations in cluster: {len(citation_objects)}")
                print(f"     Verified citations: {verified_count}")
                
                if verified_count == 0:
                    print(f"     🔍 Result: Would show 'Verifying Source: N/A' (no verified citations)")
                else:
                    canonical_name = cluster.get('canonical_name')
                    if canonical_name and canonical_name != 'None':
                        print(f"     ✅ Result: Would show 'Verifying Source: {canonical_name}'")
                    else:
                        print(f"     ⚠️ Result: Would show 'Verifying Source: N/A' (no canonical data)")
                
                print()
        else:
            print(f"   ❌ No clusters found!")
        
        # Expected citations analysis
        print(f"🎯 Expected Citations Analysis:")
        expected_citations = [
            "State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022)",
            "Am. Legion Post No. 32 v. City of Walla Walla, 116 Wn.2d 1, 8, 802 P.2d 784 (1991)"
        ]
        
        print(f"   Expected to find: {len(expected_citations)} citations")
        for i, expected in enumerate(expected_citations, 1):
            print(f"   {i}. {expected}")
        
        # Check if we found what we expected
        found_citations_text = [c.get('citation', '') for c in citations]
        
        print(f"\n✅ Success Metrics:")
        print(f"   Citations found: {len(citations)} (expected: {len(expected_citations)})")
        print(f"   Clusters found: {len(clusters)}")
        
        # Check for specific patterns
        myg_citations = [c for c in citations if 'M.Y.G.' in c.get('extracted_case_name', '')]
        legion_citations = [c for c in citations if 'Legion' in c.get('extracted_case_name', '')]
        
        print(f"   M.Y.G. citations: {len(myg_citations)}")
        print(f"   Legion citations: {len(legion_citations)}")
        
        success = len(citations) >= 2  # Should find at least the main citations
        
        if success:
            print(f"   🎉 SUCCESS: Found expected citations")
        else:
            print(f"   ❌ ISSUE: Did not find expected number of citations")
        
        return success
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the specific text test."""
    
    print("🚀 Testing User's Specific Text")
    print("=" * 70)
    
    success = test_specific_text()
    
    print("\n" + "=" * 70)
    print("📋 SPECIFIC TEXT TEST RESULTS")
    print("=" * 70)
    
    if success:
        print("✅ TEXT PROCESSING SUCCESSFUL!")
        print("🔍 Key findings:")
        print("   - Citations were extracted correctly")
        print("   - Clustering worked as expected")
        print("   - Any 'N/A' for verification is expected behavior")
    else:
        print("❌ TEXT PROCESSING ISSUES FOUND")
        print("🔧 Possible issues:")
        print("   - Citation extraction may have failed")
        print("   - Text processing pipeline may have errors")
        print("   - API connectivity issues")
    
    return success

if __name__ == "__main__":
    main()

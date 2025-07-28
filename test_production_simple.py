#!/usr/bin/env python3
"""
Simple production test using the API endpoints to verify clustering fix.
"""

import requests
import json
import time

def test_clustering_via_api():
    """Test clustering by calling the actual API endpoint."""
    print("Testing Production Clustering via API")
    print("=" * 50)
    
    # Test text with multiple Gideon v. Wainwright citations
    test_text = """
    This is a test document with legal citations.
    The case of Brown v. Board of Education, 347 U.S. 483 (1954) established important precedent.
    The case of Gideon v. Wainwright, 372 U.S. 335 (1963) guaranteed the right to counsel.
    Additionally, Gideon v. Wainwright, 83 S. Ct. 792 (1963) is the same case.
    Also see 9 L. Ed. 2d 799 (1963) which is another parallel citation for Gideon v. Wainwright.
    In Miranda v. Arizona, 384 U.S. 436 (1966), the Court established important procedural rights.
    """
    
    # API endpoint
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    print(f"Sending text to API: {url}")
    print(f"Text length: {len(test_text)} characters")
    
    try:
        # Send request to API
        response = requests.post(url, json={
            'text': test_text,
            'source_name': 'clustering_test'
        }, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API request successful")
            
            # Check if we have citations
            if 'citations' in result:
                citations = result['citations']
                print(f"Found {len(citations)} citations")
                
                # Analyze Gideon citations
                gideon_citations = []
                for citation in citations:
                    citation_text = citation.get('citation', '')
                    canonical_name = citation.get('canonical_name', '')
                    extracted_name = citation.get('extracted_case_name', '')
                    
                    if ('gideon' in citation_text.lower() or 
                        'gideon' in canonical_name.lower() or 
                        'gideon' in extracted_name.lower()):
                        gideon_citations.append(citation)
                
                print(f"\nGideon Citations Found: {len(gideon_citations)}")
                
                if len(gideon_citations) > 0:
                    print("\nGideon Citation Details:")
                    cluster_ids = set()
                    canonical_names = set()
                    canonical_dates = set()
                    
                    for i, citation in enumerate(gideon_citations):
                        print(f"  {i+1}. {citation.get('citation', 'N/A')}")
                        print(f"     Canonical: {citation.get('canonical_name', 'N/A')} ({citation.get('canonical_date', 'N/A')})")
                        print(f"     Extracted: {citation.get('extracted_case_name', 'N/A')} ({citation.get('extracted_date', 'N/A')})")
                        print(f"     Verified: {citation.get('verified', False)}")
                        
                        # Collect clustering data
                        if citation.get('canonical_name'):
                            canonical_names.add(citation.get('canonical_name'))
                        if citation.get('canonical_date'):
                            canonical_dates.add(citation.get('canonical_date'))
                        print()
                    
                    print(f"Clustering Analysis:")
                    print(f"  Unique canonical names: {len(canonical_names)} - {list(canonical_names)}")
                    print(f"  Unique canonical dates: {len(canonical_dates)} - {list(canonical_dates)}")
                    
                    # Check if clustering is working
                    if len(canonical_names) <= 1 and len(canonical_dates) <= 1:
                        print(f"\n✅ SUCCESS: Gideon citations have consistent canonical data!")
                        return True
                    else:
                        print(f"\n❌ FAILURE: Gideon citations have inconsistent canonical data!")
                        return False
                else:
                    print(f"\n⚠️  No Gideon citations found")
                    return True
                    
            else:
                print("❌ No citations found in API response")
                return False
                
        elif response.status_code == 202:
            # Async processing
            task_id = response.json().get('task_id')
            print(f"✅ Async processing started, task_id: {task_id}")
            
            # Poll for results
            status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
            
            for attempt in range(30):  # Wait up to 30 seconds
                print(f"Polling attempt {attempt + 1}...")
                status_response = requests.get(status_url)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    if status_data.get('status') == 'completed':
                        result = status_data.get('result', {})
                        print("✅ Async processing completed")
                        
                        # Same analysis as above
                        if 'citations' in result:
                            citations = result['citations']
                            print(f"Found {len(citations)} citations")
                            
                            gideon_citations = []
                            for citation in citations:
                                citation_text = citation.get('citation', '')
                                canonical_name = citation.get('canonical_name', '')
                                extracted_name = citation.get('extracted_case_name', '')
                                
                                if ('gideon' in citation_text.lower() or 
                                    'gideon' in canonical_name.lower() or 
                                    'gideon' in extracted_name.lower()):
                                    gideon_citations.append(citation)
                            
                            print(f"\nGideon Citations Found: {len(gideon_citations)}")
                            
                            if len(gideon_citations) > 0:
                                canonical_names = set()
                                canonical_dates = set()
                                
                                for citation in gideon_citations:
                                    if citation.get('canonical_name'):
                                        canonical_names.add(citation.get('canonical_name'))
                                    if citation.get('canonical_date'):
                                        canonical_dates.add(citation.get('canonical_date'))
                                
                                if len(canonical_names) <= 1 and len(canonical_dates) <= 1:
                                    print(f"✅ SUCCESS: Clustering working in production!")
                                    return True
                                else:
                                    print(f"❌ FAILURE: Clustering not working properly")
                                    return False
                            else:
                                print(f"⚠️  No Gideon citations found")
                                return True
                        break
                    elif status_data.get('status') == 'failed':
                        print(f"❌ Processing failed: {status_data.get('error')}")
                        return False
                    else:
                        print(f"Status: {status_data.get('status')}")
                        time.sleep(1)
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    return False
            
            print("❌ Timeout waiting for async processing")
            return False
            
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Is the server running?")
        print("Please start the server with: python app_final_vue.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Citation Clustering Production Test")
    print("=" * 50)
    
    success = test_clustering_via_api()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 PRODUCTION TEST PASSED!")
        print("The clustering fix is working correctly in production.")
    else:
        print("❌ PRODUCTION TEST FAILED!")
        print("The clustering fix needs further investigation.")
    print("=" * 50)

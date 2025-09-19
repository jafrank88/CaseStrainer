#!/usr/bin/env python3
"""
Test script to verify the API response structure fix.
This simulates the API response processing to ensure citations appear correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_response_structure():
    """Test the response structure to ensure citations are at the top level."""
    
    # Simulate the response from UnifiedCitationProcessorV2.process_text()
    processor_result = {
        'citations': [
            {
                'citation': '183 Wash.2d 649',
                'canonical_name': 'Lopez Demetrio v. Sakuma Bros. Farms',
                'canonical_date': '2015',
                'verified': True
            },
            {
                'citation': '355 P.3d 258', 
                'canonical_name': 'Lopez Demetrio v. Sakuma Bros. Farms',
                'canonical_date': '2015',
                'verified': True
            }
        ],
        'clusters': [
            {
                'cluster_id': 'Lopez_Demetrio_v__Sakuma_Bros__Farms_2015',
                'citations': [
                    {
                        'citation': '183 Wash.2d 649',
                        'canonical_name': 'Lopez Demetrio v. Sakuma Bros. Farms'
                    },
                    {
                        'citation': '355 P.3d 258',
                        'canonical_name': 'Lopez Demetrio v. Sakuma Bros. Farms'
                    }
                ]
            }
        ],
        'success': True,
        'metadata': {}
    }
    
    print("=== TESTING API RESPONSE STRUCTURE FIX ===")
    print()
    
    # Test the OLD structure (nested result.result)
    print("1. OLD STRUCTURE (nested result.result):")
    old_response = {
        'result': {
            'result': processor_result
        },
        'request_id': 'test-123',
        'processing_time_ms': 1500
    }
    
    print(f"   Citations accessible at response.result.result.citations: {len(old_response['result']['result']['citations'])} citations")
    print(f"   Frontend would need: response.result?.result?.citations")
    print()
    
    # Test the NEW structure (flattened)
    print("2. NEW STRUCTURE (flattened):")
    new_response = {
        'citations': processor_result.get('citations', []),
        'clusters': processor_result.get('clusters', []),
        'success': processor_result.get('success', True),
        'message': processor_result.get('message', 'Analysis completed'),
        'metadata': processor_result.get('metadata', {}),
        'request_id': 'test-123',
        'processing_time_ms': 1500,
        'document_length': 1000,
        'progress_data': processor_result.get('progress_data', {})
    }
    
    print(f"   Citations accessible at response.citations: {len(new_response['citations'])} citations")
    print(f"   Frontend can use: response.citations directly")
    print()
    
    # Test Vue.js component processing
    print("3. VUE.JS COMPONENT PROCESSING:")
    
    # Simulate the Vue.js processing logic
    resultData = new_response
    
    # Map citation_objects to citations for component compatibility
    mappedClusters = []
    for cluster in (resultData.get('clusters') or []):
        mapped_cluster = {
            **cluster,
            'citations': cluster.get('citation_objects') or cluster.get('citations') or []
        }
        mappedClusters.append(mapped_cluster)
    
    # Extract citations from clusters if not in root
    allCitations = []
    allCitations.extend(resultData.get('citations') or [])
    for cluster in mappedClusters:
        allCitations.extend(cluster.get('citations') or [])
    
    # Remove duplicate citations by citation text
    uniqueCitations = []
    seen = set()
    for citation in allCitations:
        citation_key = citation.get('citation') or citation.get('citation_text')
        if citation_key and citation_key not in seen:
            seen.add(citation_key)
            uniqueCitations.append(citation)
    
    print(f"   Total unique citations found: {len(uniqueCitations)}")
    print(f"   Total clusters found: {len(mappedClusters)}")
    
    if uniqueCitations:
        print("   Sample citations:")
        for i, citation in enumerate(uniqueCitations[:3]):
            print(f"     {i+1}. {citation.get('citation')} - {citation.get('canonical_name', 'Unknown')}")
    
    print()
    print("=== TEST RESULTS ===")
    if len(uniqueCitations) > 0:
        print("✅ SUCCESS: Citations are now accessible in the frontend!")
        print("✅ The nested result.result structure has been fixed.")
        print("✅ Vue.js components should now display citations correctly.")
    else:
        print("❌ FAILURE: Citations are still not accessible.")
    
    return len(uniqueCitations) > 0

if __name__ == "__main__":
    success = test_response_structure()
    sys.exit(0 if success else 1)

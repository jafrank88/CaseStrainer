#!/usr/bin/env python3
"""
Test to debug what the frontend is actually receiving and displaying.
"""

import requests
import json

def test_frontend_data_flow():
    """Test the complete data flow from API to frontend display."""
    
    print("🔍 Testing Frontend Data Flow")
    print("=" * 50)
    
    # Simple test case
    test_text = "The case State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) is important."
    
    print(f"📝 Test Input:")
    print(f"   Text: {test_text}")
    print(f"   Length: {len(test_text)} characters")
    
    try:
        # Make API request
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text, "type": "text"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return False
        
        data = response.json()
        
        print(f"\n📊 API Response Analysis:")
        print(f"   Status: {response.status_code}")
        print(f"   Success: {data.get('success', False)}")
        print(f"   Processing Mode: {data.get('metadata', {}).get('processing_mode', 'unknown')}")
        
        # Check what the frontend would receive
        citations = data.get('citations', [])
        clusters = data.get('clusters', [])
        
        print(f"\n🔍 Frontend Data Analysis:")
        print(f"   Citations array: {type(citations)} with {len(citations)} items")
        print(f"   Clusters array: {type(clusters)} with {len(clusters)} items")
        
        # Simulate the frontend logic exactly
        print(f"\n🖥️ Frontend Logic Simulation:")
        
        # This is the exact condition from CitationResults.vue line 130
        no_citations_condition = (len(citations) if citations else 0) == 0 and (len(clusters) if clusters else 0) == 0
        
        print(f"   citations?.length || 0: {len(citations) if citations else 0}")
        print(f"   clusters?.length || 0: {len(clusters) if clusters else 0}")
        print(f"   No Citations condition: {no_citations_condition}")
        
        if no_citations_condition:
            print(f"   🚨 FRONTEND WOULD SHOW: 'No Citations Found'")
            print(f"   🔍 This explains what you're seeing!")
        else:
            print(f"   ✅ FRONTEND WOULD SHOW: Citations and clusters")
        
        # Debug the actual data structure
        if len(citations) > 0:
            print(f"\n📋 Sample Citations:")
            for i, citation in enumerate(citations[:3], 1):
                print(f"   {i}. Citation: {citation.get('citation', 'N/A')}")
                print(f"      Type: {type(citation)}")
                print(f"      Keys: {list(citation.keys())[:10]}...")  # First 10 keys
        
        if len(clusters) > 0:
            print(f"\n🔗 Sample Clusters:")
            for i, cluster in enumerate(clusters[:2], 1):
                print(f"   {i}. Cluster ID: {cluster.get('cluster_id', 'N/A')}")
                print(f"      Case Name: {cluster.get('extracted_case_name', 'N/A')}")
                print(f"      Size: {cluster.get('size', 0)}")
                print(f"      Type: {type(cluster)}")
        
        # Check if the data structure is what we expect
        expected_structure = {
            'citations': isinstance(citations, list),
            'clusters': isinstance(clusters, list),
            'citations_not_empty': len(citations) > 0,
            'clusters_not_empty': len(clusters) > 0
        }
        
        print(f"\n✅ Data Structure Validation:")
        for key, value in expected_structure.items():
            status = "✅" if value else "❌"
            print(f"   {status} {key}: {value}")
        
        return not no_citations_condition
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_different_scenarios():
    """Test different scenarios that might cause 'No Citations'."""
    
    print(f"\n🔄 Testing Different Scenarios")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Very Simple Citation",
            "text": "State v. Johnson, 160 Wn.2d 500 (2007)"
        },
        {
            "name": "Citation in Sentence",
            "text": "The case State v. Johnson, 160 Wn.2d 500 (2007) is important."
        },
        {
            "name": "Multiple Citations",
            "text": "Cases: State v. Johnson, 160 Wn.2d 500 (2007) and Brown v. Board, 347 U.S. 483 (1954)."
        },
        {
            "name": "Empty Text",
            "text": ""
        },
        {
            "name": "No Citations Text",
            "text": "This document contains no legal citations at all."
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"\n📝 Scenario: {scenario['name']}")
        
        if not scenario['text']:
            print(f"   ⚠️ Empty text - skipping API call")
            results.append({"name": scenario['name'], "would_show_no_citations": True, "reason": "Empty input"})
            continue
        
        try:
            response = requests.post(
                "http://localhost:8080/casestrainer/api/analyze",
                json={"text": scenario['text'], "type": "text"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                citations = data.get('citations', [])
                clusters = data.get('clusters', [])
                
                citations_count = len(citations) if citations else 0
                clusters_count = len(clusters) if clusters else 0
                
                would_show_no_citations = citations_count == 0 and clusters_count == 0
                
                print(f"   Citations: {citations_count}, Clusters: {clusters_count}")
                print(f"   Would show 'No Citations': {would_show_no_citations}")
                
                results.append({
                    "name": scenario['name'],
                    "citations_count": citations_count,
                    "clusters_count": clusters_count,
                    "would_show_no_citations": would_show_no_citations
                })
            else:
                print(f"   ❌ API Error: {response.status_code}")
                results.append({"name": scenario['name'], "would_show_no_citations": True, "reason": f"API Error {response.status_code}"})
                
        except Exception as e:
            print(f"   💥 Exception: {e}")
            results.append({"name": scenario['name'], "would_show_no_citations": True, "reason": f"Exception: {str(e)}"})
    
    print(f"\n📊 Scenario Results Summary:")
    for result in results:
        status = "❌ NO CITATIONS" if result.get('would_show_no_citations', True) else "✅ HAS CITATIONS"
        citations = result.get('citations_count', 0)
        clusters = result.get('clusters_count', 0)
        reason = result.get('reason', f"C:{citations}, Cl:{clusters}")
        print(f"   {status} {result['name']}: {reason}")

def main():
    """Run frontend debugging tests."""
    
    print("🚀 Frontend 'No Citations' Debugging")
    print("=" * 60)
    
    # Run tests
    basic_ok = test_frontend_data_flow()
    test_different_scenarios()
    
    print("\n" + "=" * 60)
    print("📋 FRONTEND DEBUGGING RESULTS")
    print("=" * 60)
    
    if basic_ok:
        print("✅ Basic citation flow is working")
        print("🔍 If you're still seeing 'No Citations':")
        print("   - Check browser console for JavaScript errors")
        print("   - Clear browser cache and refresh")
        print("   - Check if you're using different test data")
        print("   - Verify the specific document you're testing")
    else:
        print("❌ Basic citation flow is broken")
        print("🔍 The API is returning empty citations/clusters arrays")
        print("   - This would cause 'No Citations' message to appear")
        print("   - Check the backend processing pipeline")
    
    return basic_ok

if __name__ == "__main__":
    main()

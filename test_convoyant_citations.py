#!/usr/bin/env python3
import requests
import json

def test_citation(citation_text):
    """Test a single citation and return results"""
    try:
        response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                               json={'text': citation_text, 'type': 'text'})
        data = response.json()
        
        if data.get('citations'):
            citation = data['citations'][0]
            return {
                'citation': citation['citation'],
                'verified': citation['verified'],
                'source': citation['source'],
                'canonical_name': citation.get('canonical_name', 'None'),
                'canonical_date': citation.get('canonical_date', 'None'),
                'status': response.status_code
            }
        else:
            return {'error': 'No citations found', 'status': response.status_code}
    except Exception as e:
        return {'error': str(e)}

def test_websearch_direct(citation):
    """Test websearch directly to see which citation yields better results"""
    try:
        from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine as LegalWebSearchEngine
        engine = LegalWebSearchEngine()
        result = engine.search_cluster_canonical(citation)
        # Handle both dict and string responses
        if isinstance(result, dict):
            return result
        else:
            return {'raw_result': str(result)}
    except Exception as e:
        return {'error': str(e)}

def main():
    print("=== Testing Convoyant Case Citations ===\n")
    
    # Test Washington citation
    print("1. Testing Washington citation (200 Wn.2d 72):")
    wa_result = test_citation("200 Wn.2d 72")
    print(f"   Citation: {wa_result.get('citation', 'N/A')}")
    print(f"   Verified: {wa_result.get('verified', 'N/A')}")
    print(f"   Source: {wa_result.get('source', 'N/A')}")
    print(f"   Canonical Name: {wa_result.get('canonical_name', 'N/A')}")
    print(f"   Canonical Date: {wa_result.get('canonical_date', 'N/A')}")
    print()
    
    # Test Pacific Reporter citation
    print("2. Testing Pacific Reporter citation (514 P.3d 643):")
    p_result = test_citation("514 P.3d 643")
    print(f"   Citation: {p_result.get('citation', 'N/A')}")
    print(f"   Verified: {p_result.get('verified', 'N/A')}")
    print(f"   Source: {p_result.get('source', 'N/A')}")
    print(f"   Canonical Name: {p_result.get('canonical_name', 'N/A')}")
    print(f"   Canonical Date: {p_result.get('canonical_date', 'N/A')}")
    print()
    
    # Test both citations together
    print("3. Testing both citations together:")
    try:
        response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                               json={'text': 'Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)', 'type': 'text'})
        data = response.json()
        print(f"   Status: {response.status_code}")
        if data.get('citations'):
            print(f"   Found {len(data['citations'])} citations:")
            for i, citation in enumerate(data['citations'], 1):
                print(f"   {i}. {citation['citation']} - Verified: {citation['verified']} - Source: {citation['source']}")
                print(f"      Canonical: {citation.get('canonical_name', 'None')}")
        else:
            print(f"   No citations found in response")
    except Exception as e:
        print(f"   Error: {str(e)}")
    print()
    
    # Test with standard test paragraph
    print("4. Testing with standard test paragraph:")
    test_text = "A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)."
    try:
        response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                               json={'text': test_text, 'type': 'text'})
        data = response.json()
        print(f"   Status: {response.status_code}")
        if data.get('citations'):
            print(f"   Found {len(data['citations'])} citations:")
            for i, citation in enumerate(data['citations'], 1):
                print(f"   {i}. {citation['citation']} - Verified: {citation['verified']} - Source: {citation['source']}")
                print(f"      Canonical: {citation.get('canonical_name', 'None')}")
                print(f"      Canonical Date: {citation.get('canonical_date', 'None')}")
        else:
            print(f"   No citations found in response")
    except Exception as e:
        print(f"   Error: {str(e)}")
    print()
    
    # Test direct websearch comparison
    print("5. Direct websearch comparison:")
    print("   Testing 200 Wn.2d 72:")
    wa_websearch = test_websearch_direct("200 Wn.2d 72")
    if 'error' not in wa_websearch:
        if isinstance(wa_websearch, dict):
            print(f"   - Verified: {wa_websearch.get('verified', 'N/A')}")
            print(f"   - Canonical Name: {wa_websearch.get('canonical_name', 'N/A')}")
            print(f"   - Reliability Score: {wa_websearch.get('reliability_score', 'N/A')}")
        else:
            print(f"   - Raw result: {wa_websearch}")
    else:
        print(f"   - Error: {wa_websearch['error']}")
    
    print("   Testing 514 P.3d 643:")
    p_websearch = test_websearch_direct("514 P.3d 643")
    if 'error' not in p_websearch:
        if isinstance(p_websearch, dict):
            print(f"   - Verified: {p_websearch.get('verified', 'N/A')}")
            print(f"   - Canonical Name: {p_websearch.get('canonical_name', 'N/A')}")
            print(f"   - Reliability Score: {p_websearch.get('reliability_score', 'N/A')}")
        else:
            print(f"   - Raw result: {p_websearch}")
    else:
        print(f"   - Error: {p_websearch['error']}")

if __name__ == "__main__":
    main() 
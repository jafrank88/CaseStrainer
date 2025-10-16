"""
Test if eyecite and CourtListener API handle dash-separated citations
"""

print("="*80)
print("TESTING DASH-SEPARATED CITATIONS")
print("="*80)

# Test 1: Check if eyecite can extract dash-separated citations
print("\n1. EYECITE TEST")
print("-"*80)

try:
    import eyecite
    
    # Test text with dash-separated Ohio citation
    test_text = """
    Grace v. Perkins Restaurant, 137-Ohio St.3d-447.
    Also testing 123-Ohio-456 and normal format 234 Ohio 567.
    """
    
    print(f"Test text: {test_text.strip()}")
    print(f"\nCitations found by eyecite:")
    
    citations = eyecite.get_citations(test_text)
    for cit in citations:
        print(f"  - {cit}")
        print(f"    Type: {type(cit).__name__}")
        if hasattr(cit, 'groups'):
            print(f"    Groups: {cit.groups}")
        if hasattr(cit, 'corrected_citation_full'):
            print(f"    Corrected: {cit.corrected_citation_full}")
    
    print(f"\nTotal found: {len(citations)}")
    
except ImportError:
    print("  ✗ Eyecite not available")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Check CourtListener API with dash format
print("\n\n2. COURTLISTENER API TEST")
print("-"*80)

try:
    import requests
    from src.config import COURTLISTENER_API_KEY
    
    if not COURTLISTENER_API_KEY:
        print("  ✗ No API key available")
    else:
        # Test different formats
        test_citations = [
            "137-Ohio St.3d-447",       # Dash format
            "137 Ohio St. 3d 447",      # Space format
            "137 Ohio St.3d 447",       # Mixed format
        ]
        
        for test_cit in test_citations:
            print(f"\nTesting: '{test_cit}'")
            
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            headers = {
                'Authorization': f'Token {COURTLISTENER_API_KEY}',
                'Accept': 'application/json'
            }
            payload = {"text": test_cit}
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    result = data[0]
                    status = result.get('status', 200)
                    clusters = result.get('clusters', [])
                    
                    if status == 200 and clusters:
                        print(f"  ✓ Found! Clusters: {len(clusters)}")
                        if clusters:
                            case_name = clusters[0].get('case_name', 'N/A')
                            print(f"    Case: {case_name}")
                    elif status == 404:
                        print(f"  ✗ Not found (404)")
                        print(f"    Error: {result.get('error_message', 'N/A')}")
                    else:
                        print(f"  ? Status: {status}")
                else:
                    print(f"  ? Unexpected response format")
                    print(f"    Data: {str(data)[:200]}")
            else:
                print(f"  ✗ HTTP Error: {response.status_code}")
                
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)

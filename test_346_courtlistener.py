"""Test CourtListener for 346 F.R.D. 102"""
import requests
import os

def test_courtlistener():
    """Test CourtListener citation-lookup for 346 F.R.D. 102"""
    
    # Get API key
    api_key = None
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('COURTLISTENER_API_KEY'):
                api_key = line.split('=')[1].strip()
                break
    
    if not api_key:
        print("❌ No CourtListener API key found")
        return
    
    citation = "346 F.R.D. 102"
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    print(f"Testing CourtListener citation-lookup for: {citation}")
    print(f"API URL: {url}")
    print()
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {"text": citation}
    
    print("=" * 60)
    print("Querying CourtListener API")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            
            if isinstance(results, list) and len(results) > 0:
                result = results[0]
                status = result.get('status')
                clusters = result.get('clusters', [])
                
                print(f"\nStatus: {status}")
                print(f"Clusters found: {len(clusters)}")
                
                if clusters:
                    print("\n✅ Case found on CourtListener!")
                    for i, cluster in enumerate(clusters, 1):
                        print(f"\nCluster {i}:")
                        print(f"  ID: {cluster.get('id')}")
                        print(f"  Case name: {cluster.get('case_name')}")
                        print(f"  Date filed: {cluster.get('date_filed')}")
                        print(f"  URL: https://www.courtlistener.com{cluster.get('absolute_url', '')}")
                else:
                    print("\n❌ No clusters found - case not on CourtListener")
            else:
                print("\n❌ No results returned")
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_courtlistener()

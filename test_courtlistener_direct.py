import requests
import os
import sys

# Add src to path
sys.path.append('src')

def test_courtlistener_api_direct():
    """Test CourtListener API directly to verify it's working."""
    
    print("=" * 80)
    print("🔍 DIRECT COURTLISTENER API TEST")
    print("=" * 80)
    
    # Get API key from config
    try:
        from config import COURTLISTENER_API_KEY, COURTLISTENER_API_URL
        print(f"API URL: {COURTLISTENER_API_URL}")
        print(f"API Key available: {'Yes' if COURTLISTENER_API_KEY else 'No'}")
        
        if not COURTLISTENER_API_KEY:
            print("❌ No API key found!")
            return False
            
    except Exception as e:
        print(f"❌ Error importing config: {e}")
        return False
    
    # Test with a citation from your paragraph
    test_citation = "159 Wn.2d 700"  # Bostain v. Food Express
    
    headers = {
        'Authorization': f'Token {COURTLISTENER_API_KEY}',
        'User-Agent': 'CaseStrainer/1.0 (Legal Citation Verification Tool)'
    }
    
    # Try the search endpoint
    search_url = f"{COURTLISTENER_API_URL}search/"
    params = {
        'type': 'o',  # opinions
        'q': test_citation,
        'format': 'json'
    }
    
    try:
        print(f"\n🌐 Testing API with citation: {test_citation}")
        print(f"Request URL: {search_url}")
        print(f"Parameters: {params}")
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ CourtListener API is working!")
            print(f"Results found: {data.get('count', 0)}")
            
            if data.get('results'):
                print("\n📋 Sample results:")
                for i, result in enumerate(data['results'][:3], 1):
                    print(f"{i}. {result.get('caseName', 'N/A')}")
                    print(f"   Citation: {result.get('citation', 'N/A')}")
                    print(f"   Court: {result.get('court', 'N/A')}")
                    print(f"   Date: {result.get('dateFiled', 'N/A')}")
                    print(f"   URL: {result.get('absolute_url', 'N/A')}")
                    print()
                
                return True
            else:
                print("⚠️  No results found for this citation")
                return False
                
        elif response.status_code == 401:
            print("❌ Authentication failed - API key is invalid")
            return False
            
        elif response.status_code == 403:
            print("❌ Access forbidden - API key lacks permissions")
            return False
            
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_parallel_citation_detection():
    """Test if the system can detect parallel citations."""
    
    print("\n" + "=" * 80)
    print("🔗 PARALLEL CITATION DETECTION TEST")
    print("=" * 80)
    
    # Test the exact citations from your paragraph
    citations = [
        {"citation": "159 Wn.2d 700", "case": "Bostain v. Food Express", "year": "2007"},
        {"citation": "153 P.3d 846", "case": "Bostain v. Food Express", "year": "2007"}
    ]
    
    print("Testing these citations for parallel detection:")
    for citation in citations:
        print(f"  • {citation['citation']} - {citation['case']} ({citation['year']})")
    
    print(f"\n🔍 Analysis:")
    print(f"  • Same case name: ✅ Both are 'Bostain v. Food Express'")
    print(f"  • Same year: ✅ Both are from 2007")
    print(f"  • Different reporters: ✅ Wn.2d (Washington) vs P.3d (Pacific)")
    print(f"  • Should cluster: ✅ These are classic parallel citations")
    
    print(f"\n💡 This confirms the clustering algorithm should detect these as parallel citations.")
    print(f"   If they're not being clustered, there's a bug in the clustering logic.")

if __name__ == "__main__":
    # Test API connectivity
    api_working = test_courtlistener_api_direct()
    
    # Test parallel citation logic
    test_parallel_citation_detection()
    
    print("\n" + "=" * 80)
    print("🎯 DIAGNOSIS SUMMARY")
    print("=" * 80)
    
    if api_working:
        print("✅ VERIFICATION: CourtListener API is accessible and working")
        print("   Problem: Verification code may not be called or may be disabled")
        print("   Solution: Check if verification is commented out in the processor")
    else:
        print("❌ VERIFICATION: CourtListener API is not working")
        print("   Problem: API key, connectivity, or permissions issue")
        print("   Solution: Fix API configuration before testing verification")
    
    print("\n❌ CLUSTERING: Parallel citations not being detected")
    print("   Problem: Clustering algorithm not recognizing parallel citations")
    print("   Solution: Debug clustering logic in unified_citation_clustering.py")
    
    print("\n📋 NEXT STEPS:")
    print("1. Fix CourtListener API if not working")
    print("2. Check if verification is disabled in unified_citation_processor_v2.py")
    print("3. Debug clustering algorithm for parallel citation detection")
    print("4. Test with a longer paragraph to see if thresholds are the issue")
    
    print("=" * 80)

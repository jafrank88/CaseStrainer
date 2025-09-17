import os
import sys
import requests
import json

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_courtlistener_api():
    """Test if CourtListener API is accessible and working."""
    
    print("=" * 80)
    print("COURTLISTENER API VERIFICATION TEST")
    print("=" * 80)
    
    # Check if API key is available
    from src.config import COURTLISTENER_API_KEY, COURTLISTENER_API_URL
    
    print(f"API URL: {COURTLISTENER_API_URL}")
    print(f"API Key configured: {'Yes' if COURTLISTENER_API_KEY else 'No'}")
    
    if not COURTLISTENER_API_KEY:
        print("❌ No CourtListener API key found!")
        print("This explains why citations are not being verified.")
        return False
    
    # Test API connectivity
    try:
        # Test with a simple search for a known citation
        test_citation = "159 Wn.2d 700"  # Bostain v. Food Express from our test
        
        headers = {
            'Authorization': f'Token {COURTLISTENER_API_KEY}',
            'User-Agent': 'CaseStrainer/1.0 (Legal Citation Verification Tool)'
        }
        
        # Try the opinions endpoint with a search
        search_url = f"{COURTLISTENER_API_URL}search/"
        params = {
            'type': 'o',  # opinions
            'q': test_citation,
            'format': 'json'
        }
        
        print(f"\nTesting API connectivity...")
        print(f"Search URL: {search_url}")
        print(f"Search params: {params}")
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ CourtListener API is accessible!")
            print(f"Results found: {data.get('count', 0)}")
            
            if data.get('results'):
                print("Sample result:")
                result = data['results'][0]
                print(f"  Case: {result.get('caseName', 'N/A')}")
                print(f"  Citation: {result.get('citation', 'N/A')}")
                print(f"  Court: {result.get('court', 'N/A')}")
                print(f"  Date: {result.get('dateFiled', 'N/A')}")
            
            return True
            
        elif response.status_code == 401:
            print("❌ API key is invalid or expired!")
            print("This explains why citations are not being verified.")
            return False
            
        elif response.status_code == 403:
            print("❌ API access forbidden!")
            print("The API key may not have the required permissions.")
            return False
            
        else:
            print(f"❌ API returned status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ API request timed out!")
        print("Network connectivity issues may be preventing verification.")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_clustering_config():
    """Test clustering configuration."""
    
    print("\n" + "=" * 80)
    print("CLUSTERING CONFIGURATION TEST")
    print("=" * 80)
    
    from src.config import get_citation_config
    
    config = get_citation_config()
    
    print(f"Clustering enabled: {config.get('enable_clustering', False)}")
    print(f"Verification enabled: {config.get('enable_verification', False)}")
    
    clustering_options = config.get('clustering_options', {})
    print(f"Parallel detection: {clustering_options.get('enable_parallel_detection', False)}")
    print(f"Case relationship detection: {clustering_options.get('enable_case_relationship_detection', False)}")
    print(f"Metadata propagation: {clustering_options.get('enable_metadata_propagation', False)}")
    
    verification_options = config.get('verification_options', {})
    print(f"CourtListener verification: {verification_options.get('enable_courtlistener', False)}")
    print(f"Fallback sources: {verification_options.get('enable_fallback_sources', False)}")
    print(f"Confidence scoring: {verification_options.get('enable_confidence_scoring', False)}")
    print(f"Min confidence threshold: {verification_options.get('min_confidence_threshold', 0.7)}")

def analyze_paragraph_citations():
    """Analyze why the specific paragraph didn't get clustered citations."""
    
    print("\n" + "=" * 80)
    print("PARAGRAPH CITATION ANALYSIS")
    print("=" * 80)
    
    # The citations we found in the paragraph
    citations = [
        {"citation": "509 P.3d 325", "case": "Fode v. Dep't of Ecology", "year": "2022"},
        {"citation": "159 Wn.2d 700", "case": "Bostain v. Food Express", "year": "2007"},
        {"citation": "153 P.3d 846", "case": "Bostain v. Food Express", "year": "2007"},
        {"citation": "495 P.3d 866 No. 103394-0 12", "case": "Port of Tacoma v. Sacks", "year": "2021"}
    ]
    
    print(f"Citations found: {len(citations)}")
    
    # Group by case name
    case_groups = {}
    for citation in citations:
        case_name = citation['case']
        if case_name not in case_groups:
            case_groups[case_name] = []
        case_groups[case_name].append(citation)
    
    print(f"Unique cases: {len(case_groups)}")
    
    for case_name, case_citations in case_groups.items():
        print(f"\n{case_name}:")
        for citation in case_citations:
            print(f"  - {citation['citation']} ({citation['year']})")
        
        if len(case_citations) > 1:
            print(f"  ✅ Should cluster: {len(case_citations)} citations from same case")
        else:
            print(f"  ❌ No clustering: Only 1 citation from this case")
    
    # Check for parallel citations
    bostain_citations = case_groups.get("Bostain v. Food Express", [])
    if len(bostain_citations) > 1:
        print(f"\n🔍 BOSTAIN CASE ANALYSIS:")
        print(f"Found {len(bostain_citations)} citations for Bostain v. Food Express")
        print("These should be detected as parallel citations:")
        for citation in bostain_citations:
            print(f"  - {citation['citation']} (Washington vs Pacific reporter)")
        print("This is a classic parallel citation case that should cluster!")

if __name__ == "__main__":
    # Test CourtListener API
    api_working = test_courtlistener_api()
    
    # Test clustering configuration
    test_clustering_config()
    
    # Analyze the specific paragraph
    analyze_paragraph_citations()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if not api_working:
        print("❌ VERIFICATION ISSUE: CourtListener API is not accessible")
        print("   This explains why citations show 'verified: false'")
        print("   Solution: Check API key configuration and network connectivity")
    else:
        print("✅ VERIFICATION: CourtListener API is working")
        print("   Citations should be getting verified - may be a processing issue")
    
    print("\n🔗 CLUSTERING ISSUE: Multiple citations from same case not clustered")
    print("   Bostain v. Food Express has 2 citations (159 Wn.2d 700, 153 P.3d 846)")
    print("   These are parallel citations and should be clustered together")
    print("   Solution: Check clustering algorithm and thresholds")
    
    print("\n📋 RECOMMENDATIONS:")
    print("1. Verify CourtListener API key is valid and has permissions")
    print("2. Check clustering algorithm for parallel citation detection")
    print("3. Review processing strategy - may be using 'fast' mode without clustering")
    print("4. Test with longer text that has more obvious citation clusters")
    
    print("=" * 80)

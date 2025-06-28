#!/usr/bin/env python3
"""
Debug script to check API connectivity and configuration.
This script will help identify if the issue is with API keys, connectivity, or configuration.
"""

import sys
import os
import json
import requests
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check if required environment variables are set."""
    print(f"\n{'='*60}")
    print(f"ENVIRONMENT VARIABLES CHECK")
    print(f"{'='*60}")
    
    required_vars = [
        'COURTLISTENER_API_KEY',
        'GOOGLE_API_KEY',
        'LANGSEARCH_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show first few characters for security
            masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '***'
            print(f"  ✓ {var}: {masked_value}")
        else:
            print(f"  ✗ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n  WARNING: Missing environment variables: {', '.join(missing_vars)}")
        print(f"  These may be required for full functionality.")
    
    return missing_vars

def test_courtlistener_api():
    """Test CourtListener API connectivity."""
    print(f"\n{'='*60}")
    print(f"COURT LISTENER API TEST")
    print(f"{'='*60}")
    
    api_key = os.getenv('COURTLISTENER_API_KEY')
    if not api_key:
        print(f"  ✗ No CourtListener API key found")
        return False
    
    # Test with a known citation
    test_citation = "347 U.S. 483"
    
    try:
        # Test citation lookup endpoint
        print(f"  Testing citation lookup endpoint...")
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        }
        
        response = requests.post(
            "https://www.courtlistener.com/api/rest/v4/citation-lookup/",
            json={"text": test_citation},
            headers=headers,
            timeout=15
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Citation lookup successful")
            print(f"  Response: {json.dumps(data, indent=2)[:500]}...")
            return True
        elif response.status_code == 401:
            print(f"  ✗ Authentication failed - check API key")
            return False
        elif response.status_code == 403:
            print(f"  ✗ Access forbidden - check API permissions")
            return False
        elif response.status_code == 429:
            print(f"  ⚠ Rate limited - API is working but too many requests")
            return True
        else:
            print(f"  ✗ Unexpected status code: {response.status_code}")
            print(f"  Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Request failed: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return False

def test_google_api():
    """Test Google API connectivity."""
    print(f"\n{'='*60}")
    print(f"GOOGLE API TEST")
    print(f"{'='*60}")
    
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print(f"  ✗ No Google API key found")
        return False
    
    try:
        # Test Google Custom Search API
        print(f"  Testing Google Custom Search API...")
        
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                'key': api_key,
                'cx': 'test',  # This will fail but we can check if the API key is valid
                'q': 'test'
            },
            timeout=10
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 400:
            # This is expected with a test cx parameter
            print(f"  ✓ Google API key appears to be valid (400 is expected with test cx)")
            return True
        elif response.status_code == 403:
            print(f"  ✗ Google API key invalid or quota exceeded")
            return False
        else:
            print(f"  Response: {response.text[:200]}...")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Request failed: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return False

def test_web_search():
    """Test web search functionality."""
    print(f"\n{'='*60}")
    print(f"WEB SEARCH TEST")
    print(f"{'='*60}")
    
    try:
        # Test basic web search
        print(f"  Testing basic web search...")
        
        test_url = "https://www.google.com"
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            print(f"  ✓ Basic web connectivity working")
            return True
        else:
            print(f"  ✗ Web connectivity issue: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Web connectivity failed: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return False

def test_citation_components():
    """Test citation component extraction."""
    print(f"\n{'='*60}")
    print(f"CITATION COMPONENTS TEST")
    print(f"{'='*60}")
    
    try:
        from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        
        verifier = EnhancedMultiSourceVerifier()
        
        test_citations = [
            "Brown v. Board of Education, 347 U.S. 483 (1954)",
            "181 Wash.2d 391, 333 P.3d 440",
            "123 F.3d 456",
            "Smith v. Jones, 456 U.S. 789 (1982)"
        ]
        
        for citation in test_citations:
            print(f"  Testing: {citation}")
            
            # Test cleaning
            cleaned = verifier._clean_citation_for_lookup(citation)
            print(f"    Cleaned: {cleaned}")
            
            # Test component extraction
            components = verifier._extract_citation_components(citation)
            print(f"    Components: {json.dumps(components, indent=4)}")
            print()
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error testing citation components: {e}")
        return False

def check_configuration():
    """Check configuration files and settings."""
    print(f"\n{'='*60}")
    print(f"CONFIGURATION CHECK")
    print(f"{'='*60}")
    
    # Check if config files exist
    config_files = [
        'config.py',
        'src/config.py',
        '.env',
        'config.json'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"  ✓ Found config file: {config_file}")
        else:
            print(f"  - Config file not found: {config_file}")
    
    # Check if database exists
    db_files = [
        'data/citations.db',
        'src/citations.db',
        'citations.db'
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"  ✓ Found database: {db_file}")
        else:
            print(f"  - Database not found: {db_file}")

def minimal_courtlistener_test():
    """Minimal direct test of the CourtListener citation-lookup endpoint."""
    print(f"\n{'='*60}")
    print(f"MINIMAL COURTLISTENER CITATION-LOOKUP TEST")
    print(f"{'='*60}")
    
    api_key = os.getenv('COURTLISTENER_API_KEY')
    if not api_key:
        print(f"  ✗ No CourtListener API key found")
        return False
    
    endpoint = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    citation = "347 U.S. 483"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    payload = {"text": citation}
    print(f"  Endpoint: {endpoint}")
    print(f"  Headers: {headers}")
    print(f"  Payload: {payload}")
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        print(f"  Status Code: {response.status_code}")
        print(f"  Response Headers: {response.headers}")
        print(f"  Response Text: {response.text[:500]}")
        if response.status_code == 200:
            print(f"  ✓ Success!")
            return True
        else:
            print(f"  ✗ Failure!")
            return False
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return False

def main():
    """Main function to run all tests."""
    print(f"CaseStrainer API Connectivity Debug Tool")
    print(f"========================================")
    
    # Run all tests
    env_ok = len(check_environment_variables()) == 0
    courtlistener_ok = test_courtlistener_api()
    minimal_ok = minimal_courtlistener_test()
    google_ok = test_google_api()
    web_ok = test_web_search()
    components_ok = test_citation_components()
    check_configuration()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    
    tests = [
        ("Environment Variables", env_ok),
        ("CourtListener API", courtlistener_ok),
        ("Minimal CourtListener", minimal_ok),
        ("Google API", google_ok),
        ("Web Connectivity", web_ok),
        ("Citation Components", components_ok)
    ]
    
    all_passed = True
    for test_name, passed in tests:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall Status: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    if not all_passed:
        print(f"\nRECOMMENDATIONS:")
        if not env_ok:
            print(f"  - Set missing environment variables")
        if not courtlistener_ok or not minimal_ok:
            print(f"  - Check CourtListener API key and permissions")
        if not google_ok:
            print(f"  - Check Google API key and quota")
        if not web_ok:
            print(f"  - Check internet connectivity")
        if not components_ok:
            print(f"  - Check citation processing code")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Debug script to test why Kimmelman v. Morrison citation isn't being verified
"""

import sys
import os
import requests
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.config import get_config_value

def test_kimmelman_citation():
    """Test the specific Kimmelman citation that's not being verified"""
    
    # Test text with the problematic citation
    test_text = "The right to counsel protects not only the rights of individual defendants but also the legitimacy of the adversary process. Kimmelman v. Morrison, 477 U.S. 365, 374, 106 S. Ct. 2574, 91 L. Ed. 2d 305 (1986)"
    
    print("=== Testing Kimmelman Citation Verification ===")
    print(f"Text: {test_text}")
    print()
    
    # Process with our system
    processor = UnifiedCitationProcessorV2()
    result = processor.process_text(test_text)
    
    print(f"Found {len(result['citations'])} citations:")
    for i, citation in enumerate(result['citations'], 1):
        print(f"\n{i}. Citation: {citation.citation}")
        print(f"   Extracted Case Name: {getattr(citation, 'extracted_case_name', 'N/A')}")
        print(f"   Extracted Date: {getattr(citation, 'extracted_date', 'N/A')}")
        print(f"   Canonical Name: {getattr(citation, 'canonical_name', 'N/A')}")
        print(f"   Canonical Date: {getattr(citation, 'canonical_date', 'N/A')}")
        print(f"   Verified: {getattr(citation, 'verified', False)}")
        print(f"   Source: {getattr(citation, 'source', 'N/A')}")
        print(f"   Error: {getattr(citation, 'error', 'None')}")

def test_courtlistener_direct():
    """Test CourtListener API directly with the citation"""
    
    print("\n=== Testing CourtListener API Directly ===")
    
    api_key = get_config_value("COURTLISTENER_API_KEY")
    print(f"API Key available: {bool(api_key)}")
    
    # Test the batch citation lookup
    test_citations = ["477 U.S.365", "477 U.S. 365", "106 S. Ct. 2574", "91 L. Ed. 2d 305"]
    
    for citation in test_citations:
        print(f"\nTesting citation: {citation}")
        
        # Test batch lookup
        try:
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            headers = {}
            if api_key:
                headers['Authorization'] = f'Token {api_key}'
            
            data = {"text": citation}
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Results: {len(result)} items found")
                for item in result:
                    print(f"  - Citation: {item.get('citation', 'N/A')}")
                    clusters = item.get('clusters', [])
                    if clusters:
                        cluster = clusters[0]
                        print(f"  - Case: {cluster.get('case_name', 'N/A')}")
                        print(f"  - Date: {cluster.get('date_filed', 'N/A')}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

def test_eyecite_direct():
    """Test eyecite directly if available"""
    
    print("\n=== Testing Eyecite Directly ===")
    
    try:
        import eyecite
        from eyecite import get_citations
        print("Eyecite available")
        
        test_text = "Kimmelman v. Morrison, 477 U.S. 365, 374, 106 S. Ct. 2574, 91 L. Ed. 2d 305 (1986)"
        citations = get_citations(test_text)
        
        print(f"Eyecite found {len(citations)} citations:")
        for i, cite in enumerate(citations, 1):
            print(f"  {i}. {cite}")
            print(f"     Type: {type(cite)}")
            if hasattr(cite, 'groups'):
                print(f"     Groups: {cite.groups}")
                
    except ImportError:
        print("Eyecite not available")
    except Exception as e:
        print(f"Eyecite error: {e}")

if __name__ == "__main__":
    test_kimmelman_citation()
    test_courtlistener_direct()
    test_eyecite_direct() 